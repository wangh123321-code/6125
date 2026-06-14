import asyncio
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import aiofiles
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.database import db, get_database
from app.schemas import (
    HeartRateZoneItem,
    MonthlyComparisonItem,
    MonthlyReportList,
    MonthlyReportResponse,
    SessionStatus,
    StrokeBreakdownItem,
    TechniqueTrendItem,
    UserResponse,
    UserRole,
)
from app.utils.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/reports", tags=["月度报告与PDF导出"])

STROKE_TYPES = ["自由泳", "蛙泳", "仰泳", "蝶泳"]
HEART_RATE_ZONES = [
    ("Zone1", 0, 110),
    ("Zone2", 110, 130),
    ("Zone3", 130, 150),
    ("Zone4", 150, 170),
    ("Zone5", 170, 220),
]
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


class GenerateReportRequest(BaseModel):
    athlete_id: str
    year: int
    month: int


class GroupGenerateRequest(BaseModel):
    year: int
    month: int
    group_name: Optional[str] = None


class GroupSummaryItem(BaseModel):
    athlete_id: str
    athlete_name: str
    total_distance_m: float
    progress_index: float
    regressed_count: int


def _ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    return REPORTS_DIR


def _get_month_range(year: int, month: int):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


def _get_prev_month(year: int, month: int):
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _calc_heart_rate_zones(heart_rate_data: list, session_duration_min: float) -> list[HeartRateZoneItem]:
    zone_minutes = defaultdict(float)
    if not heart_rate_data or len(heart_rate_data) < 2:
        return [
            HeartRateZoneItem(zone=z[0], minutes=0.0, percentage=0.0)
            for z in HEART_RATE_ZONES
        ]

    for i in range(1, len(heart_rate_data)):
        prev = heart_rate_data[i - 1]
        curr = heart_rate_data[i]
        bpm = (prev["bpm"] + curr["bpm"]) / 2
        ts_prev = prev["timestamp"] if isinstance(prev["timestamp"], datetime) else datetime.fromisoformat(prev["timestamp"])
        ts_curr = curr["timestamp"] if isinstance(curr["timestamp"], datetime) else datetime.fromisoformat(curr["timestamp"])
        delta_min = (ts_curr - ts_prev).total_seconds() / 60.0

        for zone_name, low, high in HEART_RATE_ZONES:
            if low <= bpm < high:
                zone_minutes[zone_name] += delta_min
                break

    total = sum(zone_minutes.values()) or 1.0
    return [
        HeartRateZoneItem(
            zone=z[0],
            minutes=round(zone_minutes.get(z[0], 0.0), 2),
            percentage=round(zone_minutes.get(z[0], 0.0) / total * 100, 2),
        )
        for z in HEART_RATE_ZONES
    ]


def _calc_stroke_breakdown(sessions: list) -> list[StrokeBreakdownItem]:
    stroke_dist: dict[str, float] = defaultdict(float)

    for s in sessions:
        total_dist = s.get("total_distance_m", 0.0) or 0.0
        lap_data = s.get("lap_data", []) or []

        if lap_data:
            per_lap = total_dist / len(lap_data) if len(lap_data) > 0 else 0.0
            for i, lap in enumerate(lap_data):
                stroke_idx = i % len(STROKE_TYPES)
                stroke = STROKE_TYPES[stroke_idx]
                stroke_dist[stroke] += per_lap
        else:
            stroke_dist["自由泳"] += total_dist

    total = sum(stroke_dist.values()) or 1.0
    result = []
    for stroke in STROKE_TYPES:
        dist = stroke_dist.get(stroke, 0.0)
        if dist > 0:
            result.append(
                StrokeBreakdownItem(
                    stroke=stroke,
                    distance_m=round(dist, 2),
                    percentage=round(dist / total * 100, 2),
                )
            )

    if not result:
        result.append(StrokeBreakdownItem(stroke="自由泳", distance_m=0.0, percentage=0.0))
    return result


def _calc_technique_trends(sessions: list) -> list[TechniqueTrendItem]:
    by_date_sl: dict[str, list[float]] = defaultdict(list)
    by_date_br: dict[str, list[float]] = defaultdict(list)

    for s in sessions:
        session_date = s.get("session_date")
        if isinstance(session_date, datetime):
            date_key = session_date.strftime("%Y-%m-%d")
        else:
            date_key = str(session_date)[:10]

        motion_data = s.get("motion_data", []) or []
        for m in motion_data:
            sl = m.get("stroke_length_cm")
            br = m.get("body_rotation_deg")
            if sl is not None:
                by_date_sl[date_key].append(float(sl))
            if br is not None:
                by_date_br[date_key].append(float(br))

    sorted_dates_sl = sorted(by_date_sl.keys())
    sorted_dates_br = sorted(by_date_br.keys())

    sl_values = [
        round(sum(by_date_sl[d]) / len(by_date_sl[d]), 2) for d in sorted_dates_sl
    ]
    br_values = [
        round(sum(by_date_br[d]) / len(by_date_br[d]), 2) for d in sorted_dates_br
    ]

    def _calc_trend(values: list[float]) -> Optional[str]:
        if len(values) < 2:
            return None
        first_half = sum(values[: len(values) // 2]) / max(1, len(values) // 2)
        second_half = sum(values[len(values) // 2 :]) / max(1, len(values) - len(values) // 2)
        if second_half > first_half * 1.02:
            return "improving"
        elif second_half < first_half * 0.98:
            return "declining"
        return "stable"

    return [
        TechniqueTrendItem(
            metric="stroke_length_cm",
            values=sl_values,
            trend=_calc_trend(sl_values),
        ),
        TechniqueTrendItem(
            metric="body_rotation_deg",
            values=br_values,
            trend=_calc_trend(br_values),
        ),
    ]


def _build_comparison(
    curr_total: float,
    curr_hr_zones: list[HeartRateZoneItem],
    curr_tech: list[TechniqueTrendItem],
    prev_report: Optional[dict],
) -> list[MonthlyComparisonItem]:
    result: list[MonthlyComparisonItem] = []

    prev_total = prev_report.get("total_distance_m", 0.0) if prev_report else 0.0
    result.append(
        _make_comparison("total_distance_m", curr_total, prev_total, higher_is_better=True)
    )

    curr_z3_plus = sum(z.minutes for z in curr_hr_zones if z.zone in ("Zone3", "Zone4", "Zone5"))
    prev_hr = prev_report.get("heart_rate_zones", []) if prev_report else []
    prev_z3_plus = sum(
        z["minutes"] if isinstance(z, dict) else z.minutes
        for z in prev_hr
        if (z["zone"] if isinstance(z, dict) else z.zone) in ("Zone3", "Zone4", "Zone5")
    )
    result.append(
        _make_comparison("high_intensity_minutes", curr_z3_plus, prev_z3_plus, higher_is_better=True)
    )

    curr_sl_avg = 0.0
    curr_br_avg = 0.0
    for t in curr_tech:
        if t.metric == "stroke_length_cm" and t.values:
            curr_sl_avg = sum(t.values) / len(t.values)
        elif t.metric == "body_rotation_deg" and t.values:
            curr_br_avg = sum(t.values) / len(t.values)

    prev_tech = prev_report.get("technique_trends", []) if prev_report else []
    prev_sl_avg = 0.0
    prev_br_avg = 0.0
    for t in prev_tech:
        metric = t["metric"] if isinstance(t, dict) else t.metric
        vals = t["values"] if isinstance(t, dict) else t.values
        if metric == "stroke_length_cm" and vals:
            prev_sl_avg = sum(vals) / len(vals)
        elif metric == "body_rotation_deg" and vals:
            prev_br_avg = sum(vals) / len(vals)

    result.append(
        _make_comparison("avg_stroke_length_cm", curr_sl_avg, prev_sl_avg, higher_is_better=True)
    )
    result.append(
        _make_comparison("avg_body_rotation_deg", curr_br_avg, prev_br_avg, higher_is_better=True)
    )

    return result


def _make_comparison(metric: str, current: float, previous: float, higher_is_better: bool) -> MonthlyComparisonItem:
    if previous == 0:
        changed = 0.0
    else:
        changed = (current - previous) / previous * 100

    regressed = False
    if previous > 0:
        if higher_is_better and changed < -10:
            regressed = True
        elif (not higher_is_better) and changed > 10:
            regressed = True

    return MonthlyComparisonItem(
        metric=metric,
        current=round(current, 2),
        previous=round(previous, 2),
        changed_percent=round(changed, 2),
        regressed=regressed,
    )


QUALITY_THRESHOLD = 60.0


async def _generate_report_for_athlete(athlete_id: str, year: int, month: int) -> MonthlyReportResponse:
    db = get_database()

    start, end = _get_month_range(year, month)
    prev_year, prev_month = _get_prev_month(year, month)
    prev_start, prev_end = _get_month_range(prev_year, prev_month)

    athlete_oid = ObjectId(athlete_id)

    cursor = db["training_sessions"].find(
        {
            "athlete_id": athlete_oid,
            "status": SessionStatus.COMPLETED,
            "session_date": {"$gte": start, "$lt": end},
        }
    )
    all_sessions = await cursor.to_list(length=None)

    reliable_sessions = []
    excluded_sessions = []
    for s in all_sessions:
        quality = s.get("data_quality")
        if quality and quality.get("overall", 100) < QUALITY_THRESHOLD:
            excluded_sessions.append(s)
        else:
            reliable_sessions.append(s)

    total_distance = sum(s.get("total_distance_m", 0.0) or 0.0 for s in reliable_sessions)

    all_hr_data: list = []
    for s in reliable_sessions:
        hr_data = s.get("heart_rate_data", []) or []
        all_hr_data.extend(hr_data)

    session_count = len(reliable_sessions)
    total_duration_min = session_count * 60.0 if session_count > 0 else 0.0
    hr_zones = _calc_heart_rate_zones(all_hr_data, total_duration_min)

    stroke_breakdown = _calc_stroke_breakdown(reliable_sessions)
    technique_trends = _calc_technique_trends(reliable_sessions)

    prev_report = await db["monthly_reports"].find_one(
        {"athlete_id": athlete_oid, "year": prev_year, "month": prev_month}
    )
    comparison = _build_comparison(total_distance, hr_zones, technique_trends, prev_report)

    excluded_info = []
    for es in excluded_sessions:
        q = es.get("data_quality", {})
        excluded_info.append({
            "session_id": str(es.get("_id", "")),
            "session_date": es.get("session_date", "").isoformat() if isinstance(es.get("session_date"), datetime) else str(es.get("session_date", "")),
            "quality_score": q.get("overall", 0) if q else 0,
            "exclusion_reason": f"数据质量评分{q.get('overall', 0)}低于阈值{QUALITY_THRESHOLD}" if q else "缺少数据质量评分",
        })

    report_doc = {
        "athlete_id": athlete_oid,
        "year": year,
        "month": month,
        "total_distance_m": round(total_distance, 2),
        "stroke_breakdown": [x.model_dump() for x in stroke_breakdown],
        "heart_rate_zones": [x.model_dump() for x in hr_zones],
        "technique_trends": [x.model_dump() for x in technique_trends],
        "comparison_to_last_month": [x.model_dump() for x in comparison],
        "excluded_sessions": excluded_info,
        "quality_threshold": QUALITY_THRESHOLD,
        "file_path": None,
        "created_at": datetime.utcnow(),
    }

    existing = await db["monthly_reports"].find_one(
        {"athlete_id": athlete_oid, "year": year, "month": month}
    )
    if existing:
        report_doc["_id"] = existing["_id"]
        if existing.get("file_path"):
            report_doc["file_path"] = existing["file_path"]
        await db["monthly_reports"].replace_one({"_id": existing["_id"]}, report_doc)
    else:
        result = await db["monthly_reports"].insert_one(report_doc)
        report_doc["_id"] = result.inserted_id

    athlete_user = await db["users"].find_one({"_id": athlete_oid})
    athlete_name = athlete_user.get("full_name", str(athlete_id)) if athlete_user else str(athlete_id)

    reports_dir = _ensure_reports_dir()
    safe_name = athlete_name.replace("/", "_").replace("\\", "_")
    file_name = f"{safe_name}_{year}{month:02d}_月度报告.pdf"
    file_path = os.path.join(reports_dir, file_name)

    await generate_pdf(report_doc, athlete_name, year, month, file_path)

    await db["monthly_reports"].update_one(
        {"_id": report_doc["_id"]}, {"$set": {"file_path": file_path}}
    )
    report_doc["file_path"] = file_path

    report_doc["_id"] = str(report_doc["_id"])
    report_doc["id"] = str(report_doc["_id"])
    report_doc["athlete_id"] = str(report_doc["athlete_id"])

    return MonthlyReportResponse(**report_doc)


def _make_stroke_pie(stroke_breakdown: list, tmp_path: str):
    labels = [s["stroke"] if isinstance(s, dict) else s.stroke for s in stroke_breakdown]
    sizes = [s["percentage"] if isinstance(s, dict) else s.percentage for s in stroke_breakdown]
    sizes = [x for x in sizes if x > 0]
    labels = [labels[i] for i, x in enumerate([s["percentage"] if isinstance(s, dict) else s.percentage for s in stroke_breakdown]) if x > 0]

    if not sizes:
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.text(0.5, 0.5, "No Data", ha="center", va="center")
        ax.axis("off")
        fig.savefig(tmp_path, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"],
    )
    ax.set_title("Stroke Distribution")
    ax.axis("equal")
    fig.savefig(tmp_path, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)


def _make_hr_bar(hr_zones: list, tmp_path: str):
    labels = [z["zone"] if isinstance(z, dict) else z.zone for z in hr_zones]
    values = [z["minutes"] if isinstance(z, dict) else z.minutes for z in hr_zones]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values, color=["#81C784", "#64B5F6", "#FFB74D", "#E57373", "#BA68C8"])
    ax.set_title("Heart Rate Zone Distribution (minutes)")
    ax.set_ylabel("Minutes")
    for bar, v in zip(bars, values):
        if v > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{v:.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    fig.tight_layout()
    fig.savefig(tmp_path, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)


def _make_tech_line(tech_trends: list, tmp_path: str):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    axes = [ax1, ax2]
    metrics = ["stroke_length_cm", "body_rotation_deg"]
    titles = ["Stroke Length Trend (cm)", "Body Rotation Trend (deg)"]
    colors_list = ["#2196F3", "#FF9800"]

    for i, (metric, title, color, ax) in enumerate(zip(metrics, titles, colors_list, axes)):
        trend_item = None
        for t in tech_trends:
            m = t["metric"] if isinstance(t, dict) else t.metric
            if m == metric:
                trend_item = t
                break
        if trend_item:
            values = trend_item["values"] if isinstance(trend_item, dict) else trend_item.values
            if values:
                x = list(range(1, len(values) + 1))
                ax.plot(x, values, marker="o", color=color, linewidth=2)
                ax.set_title(title)
                ax.set_xlabel("Session")
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, "No Data", ha="center", va="center")
                ax.set_title(title)
                ax.axis("off")
        else:
            ax.text(0.5, 0.5, "No Data", ha="center", va="center")
            ax.set_title(title)
            ax.axis("off")

    fig.tight_layout()
    fig.savefig(tmp_path, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)


async def generate_pdf(report_data: dict, athlete_name: str, year: int, month: int, file_path: str):
    import io

    loop = asyncio.get_event_loop()

    with tempfile.TemporaryDirectory() as tmpdir:
        pie_path = os.path.join(tmpdir, "pie.png")
        bar_path = os.path.join(tmpdir, "bar.png")
        line_path = os.path.join(tmpdir, "line.png")

        await loop.run_in_executor(None, _make_stroke_pie, report_data.get("stroke_breakdown", []), pie_path)
        await loop.run_in_executor(None, _make_hr_bar, report_data.get("heart_rate_zones", []), bar_path)
        await loop.run_in_executor(None, _make_tech_line, report_data.get("technique_trends", []), line_path)

        total_distance = report_data.get("total_distance_m", 0.0)
        comparison = report_data.get("comparison_to_last_month", [])
        hr_zones = report_data.get("heart_rate_zones", [])

        avg_hr = 0.0
        hr_total = 0.0
        hr_weight = 0.0
        for z in hr_zones:
            minutes = z["minutes"] if isinstance(z, dict) else z.minutes
            percentage = z["percentage"] if isinstance(z, dict) else z.percentage
            zone_name = z["zone"] if isinstance(z, dict) else z.zone
            mid = 0
            for zn, low, high in HEART_RATE_ZONES:
                if zn == zone_name:
                    mid = (low + high) / 2
                    break
            hr_total += mid * minutes
            hr_weight += minutes
        avg_hr = round(hr_total / hr_weight, 1) if hr_weight > 0 else 0.0

        progress_sum = 0.0
        progress_count = 0
        for c in comparison:
            changed = c["changed_percent"] if isinstance(c, dict) else c.changed_percent
            prev = c["previous"] if isinstance(c, dict) else c.previous
            if prev and prev > 0:
                progress_sum += changed
                progress_count += 1
        progress_index = round(progress_sum / progress_count, 2) if progress_count > 0 else 0.0

        session_count = 0
        stroke_bd = report_data.get("stroke_breakdown", [])
        if stroke_bd:
            for s in stroke_bd:
                dist = s["distance_m"] if isinstance(s, dict) else s.distance_m
                session_count += dist
        avg_session_dist = round(total_distance / max(1, (total_distance / 2000)), 0) if total_distance > 0 else 0

        def _build_pdf():
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                leftMargin=2 * cm,
                rightMargin=2 * cm,
                topMargin=2 * cm,
                bottomMargin=2 * cm,
            )
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Title"],
                fontSize=18,
                spaceAfter=20,
                textColor=colors.HexColor("#1565C0"),
            )
            section_style = ParagraphStyle(
                "Section",
                parent=styles["Heading2"],
                fontSize=13,
                spaceBefore=12,
                spaceAfter=8,
                textColor=colors.HexColor("#2E7D32"),
            )
            normal_style = styles["Normal"]

            story = []

            story.append(Paragraph(f"{athlete_name} {year}年{month}月 Training Monthly Report", title_style))
            story.append(Spacer(1, 0.3 * cm))

            overview_data = [
                ["Total Distance (m)", f"{total_distance:.2f}"],
                ["Avg Session Dist (m)", f"{avg_session_dist:.0f}"],
                ["Avg Heart Rate (bpm)", f"{avg_hr:.1f}"],
                ["Progress Index (%)", f"{progress_index:.2f}"],
            ]
            overview_table = Table(overview_data, colWidths=[8 * cm, 5 * cm])
            overview_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E3F2FD")),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1565C0")),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("PADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(Paragraph("Overview", section_style))
            story.append(overview_table)
            story.append(Spacer(1, 0.5 * cm))

            story.append(Paragraph("Stroke Distribution", section_style))
            if os.path.exists(pie_path):
                story.append(Image(pie_path, width=12 * cm, height=9 * cm))
            story.append(Spacer(1, 0.3 * cm))

            story.append(Paragraph("Heart Rate Zones", section_style))
            if os.path.exists(bar_path):
                story.append(Image(bar_path, width=14 * cm, height=8 * cm))
            story.append(Spacer(1, 0.3 * cm))

            story.append(Paragraph("Technique Trends", section_style))
            if os.path.exists(line_path):
                story.append(Image(line_path, width=15 * cm, height=6 * cm))
            story.append(Spacer(1, 0.3 * cm))

            story.append(Paragraph("Comparison to Last Month", section_style))
            comp_header = ["Metric", "Current", "Previous", "Change (%)", "Status"]
            comp_rows = [comp_header]
            metric_labels = {
                "total_distance_m": "Total Distance (m)",
                "high_intensity_minutes": "High Intensity (min)",
                "avg_stroke_length_cm": "Avg Stroke Length (cm)",
                "avg_body_rotation_deg": "Avg Body Rotation (deg)",
            }
            regressed_rows = []
            for idx, c in enumerate(comparison):
                metric = c["metric"] if isinstance(c, dict) else c.metric
                curr = c["current"] if isinstance(c, dict) else c.current
                prev = c["previous"] if isinstance(c, dict) else c.previous
                changed = c["changed_percent"] if isinstance(c, dict) else c.changed_percent
                regressed = c["regressed"] if isinstance(c, dict) else c.regressed
                label = metric_labels.get(metric, metric)
                status = "Regressed" if regressed else ("Improved" if changed > 0 else ("Stable" if changed == 0 else "Slight Down"))
                comp_rows.append([label, f"{curr:.2f}", f"{prev:.2f}", f"{changed:+.2f}%", status])
                if regressed:
                    regressed_rows.append(idx + 1)

            comp_table = Table(comp_rows, colWidths=[5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 3 * cm])
            ts = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
            for r in regressed_rows:
                ts.add("BACKGROUND", (0, r), (-1, r), colors.HexColor("#FFCDD2"))
                ts.add("TEXTCOLOR", (0, r), (-1, r), colors.HexColor("#C62828"))
            comp_table.setStyle(ts)
            story.append(comp_table)

            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))

            doc.build(story)

        await loop.run_in_executor(None, _build_pdf)


@router.post("/generate", response_model=MonthlyReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    body: GenerateReportRequest,
    current_user: UserResponse = Depends(require_role("coach", "headcoach", "athlete")),
):
    get_database()

    if current_user.role == UserRole.ATHLETE:
        if str(current_user.id) != body.athlete_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="运动员只能生成自己的报告",
            )

    try:
        athlete_oid = ObjectId(body.athlete_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 athlete_id")

    athlete = await db["users"].find_one({"_id": athlete_oid})
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    if current_user.role == UserRole.COACH:
        coach_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
        coach_group = coach_user.get("group") if coach_user else None
        athlete_group = athlete.get("group")
        if coach_group and athlete_group != coach_group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="教练只能生成自己组运动员的报告",
            )

    report = await _generate_report_for_athlete(body.athlete_id, body.year, body.month)
    return report


@router.get("/list", response_model=MonthlyReportList)
async def list_reports(
    athlete_id: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_active_user),
):
    get_database()

    query: dict = {}

    if current_user.role == UserRole.ATHLETE:
        query["athlete_id"] = ObjectId(current_user.id)
        if athlete_id and athlete_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权查看其他运动员报告")
    elif current_user.role == UserRole.COACH:
        coach_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
        coach_group = coach_user.get("group") if coach_user else None
        group_athletes_cursor = db["users"].find({"role": UserRole.ATHLETE.value, "group": coach_group})
        group_athletes = await group_athletes_cursor.to_list(length=None)
        group_athlete_ids = [a["_id"] for a in group_athletes]
        query["athlete_id"] = {"$in": group_athlete_ids} if group_athlete_ids else []
        if athlete_id:
            try:
                aid = ObjectId(athlete_id)
                if aid not in group_athlete_ids:
                    raise HTTPException(status_code=403, detail="无权查看其他组运动员报告")
                query["athlete_id"] = aid
            except Exception:
                raise HTTPException(status_code=400, detail="无效的 athlete_id")

    if athlete_id and current_user.role != UserRole.ATHLETE and current_user.role != UserRole.COACH:
        try:
            query["athlete_id"] = ObjectId(athlete_id)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的 athlete_id")

    if year:
        query["year"] = year
    if month:
        query["month"] = month

    total = await db["monthly_reports"].count_documents(query)
    skip = (page - 1) * page_size
    cursor = (
        db["monthly_reports"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    )
    reports = await cursor.to_list(length=page_size)

    result = []
    for r in reports:
        r["_id"] = str(r["_id"])
        r["id"] = str(r["_id"])
        r["athlete_id"] = str(r["athlete_id"])
        result.append(MonthlyReportResponse(**r))

    return MonthlyReportList(reports=result, total=total)


@router.get("/{report_id}", response_model=MonthlyReportResponse)
async def get_report(
    report_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
):
    get_database()

    try:
        rid = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 report_id")

    report = await db["monthly_reports"].find_one({"_id": rid})
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    report_athlete_id = str(report["athlete_id"])

    if current_user.role == UserRole.ATHLETE:
        if str(current_user.id) != report_athlete_id:
            raise HTTPException(status_code=403, detail="无权查看此报告")
    elif current_user.role == UserRole.COACH:
        coach_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
        coach_group = coach_user.get("group") if coach_user else None
        athlete = await db["users"].find_one({"_id": ObjectId(report_athlete_id)})
        athlete_group = athlete.get("group") if athlete else None
        if coach_group and athlete_group != coach_group:
            raise HTTPException(status_code=403, detail="无权查看其他组运动员报告")

    report["_id"] = str(report["_id"])
    report["id"] = str(report["_id"])
    report["athlete_id"] = str(report["athlete_id"])
    return MonthlyReportResponse(**report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
):
    get_database()

    try:
        rid = ObjectId(report_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 report_id")

    report = await db["monthly_reports"].find_one({"_id": rid})
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    report_athlete_id = str(report["athlete_id"])

    if current_user.role == UserRole.ATHLETE:
        if str(current_user.id) != report_athlete_id:
            raise HTTPException(status_code=403, detail="无权下载此报告")
    elif current_user.role == UserRole.COACH:
        coach_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
        coach_group = coach_user.get("group") if coach_user else None
        athlete = await db["users"].find_one({"_id": ObjectId(report_athlete_id)})
        athlete_group = athlete.get("group") if athlete else None
        if coach_group and athlete_group != coach_group:
            raise HTTPException(status_code=403, detail="无权下载其他组运动员报告")

    file_path = report.get("file_path")
    if not file_path or not os.path.exists(file_path):
        athlete = await db["users"].find_one({"_id": ObjectId(report_athlete_id)})
        athlete_name = athlete.get("full_name", report_athlete_id) if athlete else report_athlete_id
        _ensure_reports_dir()
        safe_name = athlete_name.replace("/", "_").replace("\\", "_")
        file_name = f"{safe_name}_{report['year']}{report['month']:02d}_月度报告.pdf"
        file_path = os.path.join(REPORTS_DIR, file_name)
        await generate_pdf(report, athlete_name, report["year"], report["month"], file_path)
        await db["monthly_reports"].update_one({"_id": rid}, {"$set": {"file_path": file_path}})

    athlete = await db["users"].find_one({"_id": ObjectId(report_athlete_id)})
    athlete_name = athlete.get("full_name", "运动员") if athlete else "运动员"
    download_name = f"{athlete_name}_{report['year']}{report['month']:02d}_月度报告.pdf"

    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type="application/pdf",
    )


@router.get("/group-summary", response_model=list[GroupSummaryItem])
async def group_summary(
    year: int = Query(...),
    month: int = Query(...),
    group_name: Optional[str] = Query(None),
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    get_database()

    query = {"role": UserRole.ATHLETE.value}

    if current_user.role == UserRole.COACH:
        coach_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
        coach_group = coach_user.get("group") if coach_user else None
        if group_name and group_name != coach_group:
            raise HTTPException(status_code=403, detail="教练只能查看自己组的报告")
        query["group"] = coach_group
    elif current_user.role == UserRole.HEADCOACH:
        if group_name:
            query["group"] = group_name

    athletes_cursor = db["users"].find(query)
    athletes = await athletes_cursor.to_list(length=None)

    result: list[GroupSummaryItem] = []
    for athlete in athletes:
        athlete_id = str(athlete["_id"])
        athlete_name = athlete.get("full_name", "")

        report = await db["monthly_reports"].find_one(
            {"athlete_id": athlete["_id"], "year": year, "month": month}
        )
        if not report:
            result.append(
                GroupSummaryItem(
                    athlete_id=athlete_id,
                    athlete_name=athlete_name,
                    total_distance_m=0.0,
                    progress_index=0.0,
                    regressed_count=0,
                )
            )
            continue

        total_dist = report.get("total_distance_m", 0.0)
        comparison = report.get("comparison_to_last_month", [])

        progress_sum = 0.0
        progress_count = 0
        regressed_count = 0
        for c in comparison:
            changed = c["changed_percent"] if isinstance(c, dict) else c.changed_percent
            prev = c["previous"] if isinstance(c, dict) else c.previous
            regressed = c["regressed"] if isinstance(c, dict) else c.regressed
            if prev and prev > 0:
                progress_sum += changed
                progress_count += 1
            if regressed:
                regressed_count += 1

        progress_index = round(progress_sum / progress_count, 2) if progress_count > 0 else 0.0

        result.append(
            GroupSummaryItem(
                athlete_id=athlete_id,
                athlete_name=athlete_name,
                total_distance_m=round(total_dist, 2),
                progress_index=progress_index,
                regressed_count=regressed_count,
            )
        )

    return result


@router.post("/group-generate")
async def group_generate(
    body: GroupGenerateRequest,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    get_database()

    query = {"role": UserRole.ATHLETE.value}

    if current_user.role == UserRole.COACH:
        coach_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
        coach_group = coach_user.get("group") if coach_user else None
        if body.group_name and body.group_name != coach_group:
            raise HTTPException(status_code=403, detail="教练只能生成自己组的报告")
        query["group"] = coach_group
    elif current_user.role == UserRole.HEADCOACH:
        if body.group_name:
            query["group"] = body.group_name

    athletes_cursor = db["users"].find(query)
    athletes = await athletes_cursor.to_list(length=None)

    tasks = []
    athlete_list = []
    for athlete in athletes:
        athlete_id = str(athlete["_id"])
        athlete_name = athlete.get("full_name", "")
        athlete_list.append({"id": athlete_id, "name": athlete_name})
        tasks.append(
            _generate_report_for_athlete(athlete_id, body.year, body.month)
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    generated_count = sum(1 for r in results if not isinstance(r, Exception))

    return {
        "generated_count": generated_count,
        "athletes": athlete_list,
    }
