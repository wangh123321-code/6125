from datetime import datetime
from enum import Enum
from typing import Optional
from statistics import median


class QualityLabel(str, Enum):
    NORMAL = "normal"
    REPAIRED = "repaired"
    ABNORMAL = "abnormal"


HR_MIN_BPM = 40
HR_MAX_BPM = 220
HR_SPIKE_THRESHOLD = 30
MEDIAN_FILTER_WINDOW = 5
CAMERA_MAX_GAP_SEC = 5.0


def clean_heart_rate_data(
    points: list[dict],
    window_size: int = MEDIAN_FILTER_WINDOW,
) -> tuple[list[dict], list[dict]]:
    repaired = []
    anomalies: list[dict] = []
    if not points:
        return points, anomalies

    sorted_points = sorted(points, key=lambda p: _ts_key(p))
    bpm_values = [p.get("bpm", 0) for p in sorted_points]

    for i, point in enumerate(sorted_points):
        original_bpm = point.get("bpm", 0)
        is_anomaly = False
        anomaly_reasons = []

        if original_bpm < HR_MIN_BPM:
            is_anomaly = True
            anomaly_reasons.append(f"心率{original_bpm}低于生理下限{HR_MIN_BPM}")
        elif original_bpm > HR_MAX_BPM:
            is_anomaly = True
            anomaly_reasons.append(f"心率{original_bpm}超过生理上限{HR_MAX_BPM}")

        if i > 0:
            prev_bpm = sorted_points[i - 1].get("bpm", 0)
            if abs(original_bpm - prev_bpm) > HR_SPIKE_THRESHOLD and not _is_edge_value(prev_bpm):
                is_anomaly = True
                anomaly_reasons.append(f"瞬间波动{abs(original_bpm - prev_bpm)}BPM超过阈值{HR_SPIKE_THRESHOLD}")

        if is_anomaly:
            replacement = _median_filter(bpm_values, i, window_size)
            start_ts = point.get("timestamp", "")
            end_ts = point.get("timestamp", "")
            anomalies.append({
                "source": "band",
                "field": "bpm",
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "original_value": original_bpm,
                "repaired_value": replacement,
                "reason": "; ".join(anomaly_reasons),
                "action": "median_filter",
            })
            point["bpm"] = replacement
            point["quality_label"] = QualityLabel.REPAIRED.value
            repaired.append(point)
        else:
            point["quality_label"] = QualityLabel.NORMAL.value

    return sorted_points, anomalies


def _is_edge_value(bpm: int) -> bool:
    return bpm <= HR_MIN_BPM or bpm >= HR_MAX_BPM


def _median_filter(values: list, index: int, window_size: int) -> int:
    half = window_size // 2
    start = max(0, index - half)
    end = min(len(values), index + half + 1)
    window = []
    for v in values[start:end]:
        if HR_MIN_BPM <= v <= HR_MAX_BPM:
            window.append(v)
    if not window:
        if index > 0:
            return values[index - 1]
        if index < len(values) - 1:
            return values[index + 1]
        return 70
    return int(median(window))


def _ts_key(point: dict) -> str:
    ts = point.get("timestamp", "")
    if isinstance(ts, datetime):
        return ts.isoformat()
    return str(ts)


def clean_touchwall_data(
    laps: list[dict],
    band_points: Optional[list[dict]] = None,
    camera_frames: Optional[list[dict]] = None,
) -> tuple[list[dict], list[dict]]:
    anomalies: list[dict] = []

    if not laps:
        missing = _detect_missing_laps(band_points, camera_frames)
        if missing:
            for m in missing:
                m["quality_label"] = QualityLabel.REPAIRED.value
                anomalies.append({
                    "source": "touchwall",
                    "field": "lap_number",
                    "start_timestamp": m.get("touch_timestamp", m.get("timestamp", "")),
                    "end_timestamp": m.get("touch_timestamp", m.get("timestamp", "")),
                    "original_value": None,
                    "repaired_value": m.get("lap_number"),
                    "reason": "触壁漏记，通过手环划频和摄像头转身检测交叉验证补记",
                    "action": "cross_validation_fill",
                })
            laps = missing

    for lap in laps:
        if lap.get("quality_label") == QualityLabel.REPAIRED.value:
            continue
        lap["quality_label"] = QualityLabel.NORMAL.value

    laps.sort(key=lambda l: l.get("lap_number", 0))
    return laps, anomalies


def _detect_missing_laps(
    band_points: Optional[list[dict]],
    camera_frames: Optional[list[dict]],
) -> list[dict]:
    turn_events: list[dict] = []

    if camera_frames:
        sorted_frames = sorted(camera_frames, key=lambda f: _ts_key(f))
        for i in range(1, len(sorted_frames)):
            prev = sorted_frames[i - 1]
            curr = sorted_frames[i]
            br_prev = prev.get("body_rotation_deg")
            br_curr = curr.get("body_rotation_deg")
            if br_prev is not None and br_curr is not None:
                if abs(float(br_curr) - float(br_prev)) > 25:
                    turn_events.append({
                        "timestamp": curr.get("timestamp", ""),
                        "source": "camera",
                        "type": "turn_detected",
                    })

    if band_points:
        sorted_band = sorted(band_points, key=lambda p: _ts_key(p))
        for i in range(1, len(sorted_band)):
            prev = sorted_band[i - 1]
            curr = sorted_band[i]
            sr_prev = prev.get("stroke_rate")
            sr_curr = curr.get("stroke_rate")
            if sr_prev is not None and sr_curr is not None:
                if float(sr_prev) > 0 and float(sr_curr) < float(sr_prev) * 0.3:
                    turn_events.append({
                        "timestamp": curr.get("timestamp", ""),
                        "source": "band",
                        "type": "stroke_pause_detected",
                    })

    if not turn_events:
        return []

    turn_events.sort(key=lambda e: str(e.get("timestamp", "")))

    filled_laps = []
    lap_num = 1
    for event in turn_events:
        ts = event.get("timestamp", "")
        filled_laps.append({
            "lap_number": lap_num,
            "touch_timestamp": ts,
            "timestamp": ts,
            "distance_m": 50.0,
            "time_sec": 0.0,
            "pace": None,
            "quality_label": QualityLabel.REPAIRED.value,
            "auto_filled": True,
        })
        lap_num += 1

    return filled_laps


def clean_camera_data(
    frames: list[dict],
    max_gap_sec: float = CAMERA_MAX_GAP_SEC,
) -> tuple[list[dict], list[dict]]:
    anomalies: list[dict] = []

    if not frames:
        return frames, anomalies

    sorted_frames = sorted(frames, key=lambda f: _ts_key(f))

    for frame in sorted_frames:
        frame["quality_label"] = QualityLabel.NORMAL.value

    i = 1
    while i < len(sorted_frames):
        prev = sorted_frames[i - 1]
        curr = sorted_frames[i]
        gap = _compute_gap_sec(prev, curr)

        if gap > max_gap_sec:
            anomalies.append({
                "source": "camera",
                "field": "frame_gap",
                "start_timestamp": _ts_key(prev),
                "end_timestamp": _ts_key(curr),
                "original_value": None,
                "repaired_value": None,
                "reason": f"连续丢帧{gap:.1f}秒超过阈值{max_gap_sec}秒，标记为不可靠",
                "action": "mark_unreliable",
            })
            _mark_range_unreliable(sorted_frames, i - 1, i)
            i += 1
            continue

        if gap > 0.1:
            interpolated = _interpolate_frames(prev, curr, gap)
            for interp_frame in interpolated:
                interp_frame["quality_label"] = QualityLabel.REPAIRED.value
                sorted_frames.insert(i, interp_frame)
                i += 1

            anomalies.append({
                "source": "camera",
                "field": "frame_gap",
                "start_timestamp": _ts_key(prev),
                "end_timestamp": _ts_key(curr),
                "original_value": None,
                "repaired_value": f"插值填充{len(interpolated)}帧",
                "reason": f"丢帧间隔{gap:.1f}秒，线性插值填充",
                "action": "linear_interpolation",
            })
            i += 1
            continue

        i += 1

    return sorted_frames, anomalies


def _compute_gap_sec(prev: dict, curr: dict) -> float:
    ts_prev = prev.get("timestamp", "")
    ts_curr = curr.get("timestamp", "")
    try:
        if isinstance(ts_prev, datetime):
            dt_prev = ts_prev
        else:
            dt_prev = datetime.fromisoformat(str(ts_prev))
        if isinstance(ts_curr, datetime):
            dt_curr = ts_curr
        else:
            dt_curr = datetime.fromisoformat(str(ts_curr))
        return abs((dt_curr - dt_prev).total_seconds())
    except (ValueError, TypeError):
        return 0.0


def _mark_range_unreliable(frames: list[dict], start_idx: int, end_idx: int):
    for idx in range(start_idx, min(end_idx + 1, len(frames))):
        frames[idx]["quality_label"] = QualityLabel.ABNORMAL.value
        frames[idx]["unreliable"] = True


def _interpolate_frames(prev: dict, curr: dict, gap_sec: float) -> list[dict]:
    interval = 0.1
    count = max(1, int(gap_sec / interval) - 1)
    if count <= 0:
        return []

    result = []
    for k in range(1, count + 1):
        ratio = k / (count + 1)
        interp = {}
        for key in ("stroke_length_cm", "body_rotation_deg", "elbow_angle_deg", "kick_frequency", "body_position_score"):
            v_prev = prev.get(key)
            v_curr = curr.get(key)
            if v_prev is not None and v_curr is not None:
                interp[key] = round(float(v_prev) + ratio * (float(v_curr) - float(v_prev)), 2)

        ts_prev = prev.get("timestamp", "")
        ts_curr = curr.get("timestamp", "")
        try:
            if isinstance(ts_prev, datetime):
                dt_prev = ts_prev
            else:
                dt_prev = datetime.fromisoformat(str(ts_prev))
            if isinstance(ts_curr, datetime):
                dt_curr = ts_curr
            else:
                dt_curr = datetime.fromisoformat(str(ts_curr))
            from datetime import timedelta
            interp_ts = dt_prev + timedelta(seconds=gap_sec * ratio)
            interp["timestamp"] = interp_ts
        except (ValueError, TypeError):
            interp["timestamp"] = ts_prev

        interp["interpolated"] = True
        result.append(interp)

    return result


def assess_data_quality(
    heart_rate_data: list[dict],
    lap_data: list[dict],
    motion_data: list[dict],
    anomalies: list[dict],
) -> dict:
    completeness = _calc_completeness(heart_rate_data, lap_data, motion_data)
    consistency = _calc_consistency(heart_rate_data, lap_data, motion_data, anomalies)
    reliability = _calc_reliability(heart_rate_data, lap_data, motion_data, anomalies)

    overall = round(completeness * 0.35 + consistency * 0.35 + reliability * 0.30, 1)

    return {
        "completeness": round(completeness, 1),
        "consistency": round(consistency, 1),
        "reliability": round(reliability, 1),
        "overall": overall,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "warning": overall < 60,
    }


def _calc_completeness(hr: list, laps: list, motion: list) -> float:
    score = 100.0

    if hr:
        hr_with_zero = sum(1 for p in hr if p.get("bpm", 0) <= 0)
        hr_loss_ratio = hr_with_zero / len(hr) if hr else 1.0
        score -= hr_loss_ratio * 30
    else:
        score -= 30

    if laps:
        expected_laps = max(1, int(sum(l.get("distance_m", 50) for l in laps) / 50))
        actual_laps = len([l for l in laps if not l.get("auto_filled")])
        lap_ratio = actual_laps / expected_laps if expected_laps > 0 else 0
        score -= (1 - lap_ratio) * 30
    else:
        score -= 30

    if motion:
        unreliable = sum(1 for f in motion if f.get("unreliable") or f.get("quality_label") == QualityLabel.ABNORMAL.value)
        motion_loss_ratio = unreliable / len(motion) if motion else 1.0
        score -= motion_loss_ratio * 40
    else:
        score -= 40

    return max(0, min(100, score))


def _calc_consistency(hr: list, laps: list, motion: list, anomalies: list) -> float:
    score = 100.0
    source_anomaly_count = {}
    for a in anomalies:
        src = a.get("source", "unknown")
        source_anomaly_count[src] = source_anomaly_count.get(src, 0) + 1

    if hr:
        hr_anomalies = source_anomaly_count.get("band", 0)
        hr_penalty = min(40, hr_anomalies / max(1, len(hr)) * 100 * 2)
        score -= hr_penalty

    if laps:
        lap_anomalies = source_anomaly_count.get("touchwall", 0)
        lap_penalty = min(30, lap_anomalies * 10)
        score -= lap_penalty

    if motion:
        cam_anomalies = source_anomaly_count.get("camera", 0)
        cam_penalty = min(30, cam_anomalies / max(1, len(motion)) * 100 * 2)
        score -= cam_penalty

    return max(0, min(100, score))


def _calc_reliability(hr: list, laps: list, motion: list, anomalies: list) -> float:
    score = 100.0

    repaired_actions = [a for a in anomalies if a.get("action") in ("median_filter", "cross_validation_fill", "linear_interpolation")]
    unreliable_actions = [a for a in anomalies if a.get("action") == "mark_unreliable"]

    score -= len(repaired_actions) * 5
    score -= len(unreliable_actions) * 15

    cross_validated = [a for a in anomalies if a.get("action") == "cross_validation_fill"]
    score += len(cross_validated) * 3

    total_data_points = len(hr) + len(laps) + len(motion)
    if total_data_points > 0:
        anomaly_ratio = len(anomalies) / total_data_points
        if anomaly_ratio > 0.2:
            score -= (anomaly_ratio - 0.2) * 100

    return max(0, min(100, score))


def run_data_pipeline(
    hr_points: list[dict],
    lap_points: list[dict],
    camera_frames: list[dict],
) -> dict:
    all_anomalies = []

    cleaned_hr, hr_anomalies = clean_heart_rate_data(hr_points)
    all_anomalies.extend(hr_anomalies)

    cleaned_laps, lap_anomalies = clean_touchwall_data(lap_points, cleaned_hr, camera_frames)
    all_anomalies.extend(lap_anomalies)

    cleaned_frames, cam_anomalies = clean_camera_data(camera_frames)
    all_anomalies.extend(cam_anomalies)

    quality = assess_data_quality(cleaned_hr, cleaned_laps, cleaned_frames, all_anomalies)

    return {
        "heart_rate_data": cleaned_hr,
        "lap_data": cleaned_laps,
        "motion_data": cleaned_frames,
        "quality": quality,
    }
