import asyncio
import json
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.database import get_database, get_redis_client as get_redis
from app.schemas import (
    HeartRateDataPoint,
    LapDataPoint,
    MotionDataPoint,
    SessionStatus,
    TrainingSessionResponse,
    UserResponse,
    CoachAdjustmentRequest,
    DataQualityReport,
    DataQualityScore,
    AnomalySegment,
)
from app.utils.auth import require_role, get_current_user
from app.utils.helpers import align_timestamps
from app.services.data_quality import (
    clean_heart_rate_data,
    clean_touchwall_data,
    clean_camera_data,
    assess_data_quality,
    run_data_pipeline,
    QualityLabel,
)

router = APIRouter(prefix="/api/data", tags=["数据接入"])


class BandDataUploadRequest(BaseModel):
    athlete_id: str
    session_id: str
    points: list[HeartRateDataPoint]


class TouchWallTimerRequest(BaseModel):
    athlete_id: str
    session_id: str
    laps: list[LapDataPoint]


class CameraAnalysisRequest(BaseModel):
    athlete_id: str
    session_id: str
    frames: list[MotionDataPoint]


class SessionStartRequest(BaseModel):
    athlete_id: str
    coach_id: str
    group_name: str


@router.post("/band")
async def upload_band_data(
    body: BandDataUploadRequest,
    current_user: UserResponse = Depends(require_role("athlete", "coach", "headcoach")),
):
    redis = get_redis()
    db = get_database()

    raw_points = [
        {
            "timestamp": p.timestamp.isoformat(),
            "bpm": p.bpm,
            "stroke_rate": p.stroke_rate,
        }
        for p in body.points
    ]

    cleaned_points, hr_anomalies = clean_heart_rate_data(raw_points)

    stream_key = f"band:{body.athlete_id}:{body.session_id}"
    cache_key = f"session:{body.session_id}:heart_rate_data"
    anomaly_key = f"session:{body.session_id}:anomalies:band"

    tasks = []

    async def write_stream(point: dict):
        await redis.xadd(
            stream_key,
            {
                "timestamp": point.get("timestamp", ""),
                "bpm": str(point.get("bpm", 0)),
                "stroke_rate": str(point.get("stroke_rate", "")) if point.get("stroke_rate") else "",
                "quality_label": point.get("quality_label", "normal"),
            },
        )

    async def write_cache(point: dict):
        await redis.rpush(
            cache_key,
            json.dumps(point, ensure_ascii=False),
        )

    for point in cleaned_points:
        tasks.append(write_stream(point))
        tasks.append(write_cache(point))

    for anomaly in hr_anomalies:
        tasks.append(
            redis.rpush(anomaly_key, json.dumps(anomaly, ensure_ascii=False, default=str))
        )

    await asyncio.gather(*tasks)

    return {
        "received": len(body.points),
        "cleaned": len(cleaned_points),
        "anomalies_detected": len(hr_anomalies),
        "status": "ok",
    }


@router.post("/touchwall")
async def upload_touchwall_data(
    body: TouchWallTimerRequest,
    current_user: UserResponse = Depends(require_role("coach", "headcoach", "athlete")),
):
    redis = get_redis()
    db = get_database()

    raw_laps = [
        {
            "lap_number": lap.lap_number,
            "distance_m": lap.distance_m,
            "time_sec": lap.time_sec,
            "pace": lap.pace,
        }
        for lap in body.laps
    ]

    hr_cache_key = f"session:{body.session_id}:heart_rate_data"
    motion_cache_key = f"session:{body.session_id}:motion_data"
    band_points_raw = await redis.lrange(hr_cache_key, 0, -1)
    camera_frames_raw = await redis.lrange(motion_cache_key, 0, -1)

    band_points = [json.loads(item) for item in band_points_raw] if band_points_raw else None
    camera_frames = [json.loads(item) for item in camera_frames_raw] if camera_frames_raw else None

    cleaned_laps, lap_anomalies = clean_touchwall_data(raw_laps, band_points, camera_frames)

    stream_key = f"touchwall:{body.athlete_id}:{body.session_id}"
    cache_key = f"session:{body.session_id}:lap_data"
    dist_key = f"session:{body.session_id}:total_distance"
    anomaly_key = f"session:{body.session_id}:anomalies:touchwall"

    total_distance = 0.0

    tasks = []

    async def write_stream(lap: dict):
        await redis.xadd(
            stream_key,
            {
                "lap_number": str(lap.get("lap_number", 0)),
                "distance_m": str(lap.get("distance_m", 0)),
                "time_sec": str(lap.get("time_sec", 0)),
                "pace": str(lap.get("pace", "")) if lap.get("pace") else "",
                "quality_label": lap.get("quality_label", "normal"),
            },
        )

    async def write_cache(lap: dict):
        await redis.rpush(
            cache_key,
            json.dumps(lap, ensure_ascii=False, default=str),
        )

    for lap in cleaned_laps:
        total_distance += lap.get("distance_m", 0)
        tasks.append(write_stream(lap))
        tasks.append(write_cache(lap))

    for anomaly in lap_anomalies:
        tasks.append(
            redis.rpush(anomaly_key, json.dumps(anomaly, ensure_ascii=False, default=str))
        )

    await asyncio.gather(*tasks)

    existing_dist = await redis.get(dist_key)
    if existing_dist:
        total_distance += float(existing_dist)
    await redis.set(dist_key, str(total_distance))

    return {
        "received": len(body.laps),
        "cleaned": len(cleaned_laps),
        "anomalies_detected": len(lap_anomalies),
        "total_distance": total_distance,
    }


@router.post("/camera")
async def upload_camera_data(
    body: CameraAnalysisRequest,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    redis = get_redis()
    db = get_database()

    raw_frames = [
        {
            "timestamp": frame.timestamp.isoformat(),
            "stroke_length_cm": frame.stroke_length_cm,
            "body_rotation_deg": frame.body_rotation_deg,
        }
        for frame in body.frames
    ]

    cleaned_frames, cam_anomalies = clean_camera_data(raw_frames)

    stream_key = f"camera:{body.athlete_id}:{body.session_id}"
    cache_key = f"session:{body.session_id}:motion_data"
    anomaly_key = f"session:{body.session_id}:anomalies:camera"

    tasks = []

    async def write_stream(frame: dict):
        await redis.xadd(
            stream_key,
            {
                "timestamp": frame.get("timestamp", ""),
                "stroke_length_cm": str(frame.get("stroke_length_cm", "")) if frame.get("stroke_length_cm") else "",
                "body_rotation_deg": str(frame.get("body_rotation_deg", "")) if frame.get("body_rotation_deg") else "",
                "quality_label": frame.get("quality_label", "normal"),
            },
        )

    async def write_cache(frame: dict):
        await redis.rpush(
            cache_key,
            json.dumps(frame, ensure_ascii=False, default=str),
        )

    for frame in cleaned_frames:
        tasks.append(write_stream(frame))
        tasks.append(write_cache(frame))

    for anomaly in cam_anomalies:
        tasks.append(
            redis.rpush(anomaly_key, json.dumps(anomaly, ensure_ascii=False, default=str))
        )

    await asyncio.gather(*tasks)

    return {
        "received": len(body.frames),
        "cleaned": len(cleaned_frames),
        "anomalies_detected": len(cam_anomalies),
        "status": "ok",
    }


@router.post("/session/start")
async def start_session(
    body: SessionStartRequest,
    current_user: UserResponse = Depends(require_role("coach", "headcoach", "athlete")),
):
    redis = get_redis()
    db = get_database()

    now = datetime.utcnow()
    session_doc = {
        "athlete_id": ObjectId(body.athlete_id),
        "session_date": now,
        "start_time": now,
        "end_time": None,
        "total_distance_m": 0.0,
        "heart_rate_data": [],
        "lap_data": [],
        "motion_data": [],
        "coach_id": ObjectId(body.coach_id),
        "group_name": body.group_name,
        "status": SessionStatus.IN_PROGRESS,
        "data_quality": None,
        "created_at": now,
    }

    result = await db["training_sessions"].insert_one(session_doc)
    session_id = str(result.inserted_id)

    await redis.set(f"session:{session_id}:status", "active")

    session_doc["_id"] = session_id
    session_doc["id"] = session_id
    session_doc["athlete_id"] = body.athlete_id
    session_doc["coach_id"] = body.coach_id

    return {"session_id": session_id, "session": session_doc}


@router.post("/session/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    redis = get_redis()
    db = get_database()

    try:
        sid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 session_id")

    session = await db["training_sessions"].find_one({"_id": sid})
    if not session:
        raise HTTPException(status_code=404, detail="Session 不存在")

    hr_raw = await redis.lrange(f"session:{session_id}:heart_rate_data", 0, -1)
    lap_raw = await redis.lrange(f"session:{session_id}:lap_data", 0, -1)
    motion_raw = await redis.lrange(f"session:{session_id}:motion_data", 0, -1)
    dist_raw = await redis.get(f"session:{session_id}:total_distance")

    anomaly_keys = await redis.keys(f"session:{session_id}:anomalies:*")
    all_anomalies = []
    for akey in anomaly_keys:
        anomaly_items = await redis.lrange(akey, 0, -1)
        for item in anomaly_items:
            all_anomalies.append(json.loads(item))

    heart_rate_data_dicts = [json.loads(item) for item in hr_raw] if hr_raw else []
    lap_data_dicts = [json.loads(item) for item in lap_raw] if lap_raw else []
    motion_data_dicts = [json.loads(item) for item in motion_raw] if motion_raw else []

    quality = assess_data_quality(heart_rate_data_dicts, lap_data_dicts, motion_data_dicts, all_anomalies)

    heart_rate_data = []
    for d in heart_rate_data_dicts:
        heart_rate_data.append(
            HeartRateDataPoint(
                timestamp=datetime.fromisoformat(d["timestamp"]) if isinstance(d["timestamp"], str) else d["timestamp"],
                bpm=d["bpm"],
                stroke_rate=d.get("stroke_rate"),
            )
        )

    lap_data = []
    for d in lap_data_dicts:
        lap_data.append(
            LapDataPoint(
                lap_number=d["lap_number"],
                distance_m=d["distance_m"],
                time_sec=d["time_sec"],
                pace=d.get("pace"),
            )
        )

    motion_data = []
    for d in motion_data_dicts:
        motion_data.append(
            MotionDataPoint(
                timestamp=datetime.fromisoformat(d["timestamp"]) if isinstance(d["timestamp"], str) else d["timestamp"],
                stroke_length_cm=d.get("stroke_length_cm"),
                body_rotation_deg=d.get("body_rotation_deg"),
            )
        )

    hr_stream: dict[float, float] = {}
    for p in heart_rate_data:
        ts = p.timestamp.timestamp()
        hr_stream[ts] = float(p.bpm)

    lap_stream: dict[float, float] = {}
    for lap in lap_data:
        lap_stream[float(lap.lap_number)] = lap.distance_m

    motion_stream: dict[float, float] = {}
    for m in motion_data:
        ts = m.timestamp.timestamp()
        motion_stream[ts] = float(m.stroke_length_cm or 0.0)

    aligned = align_timestamps(hr_stream, lap_stream, motion_stream)

    total_distance_m = float(dist_raw) if dist_raw else 0.0
    if total_distance_m == 0.0:
        total_distance_m = sum(lap.distance_m for lap in lap_data)

    now = datetime.utcnow()
    update_doc = {
        "$set": {
            "status": SessionStatus.COMPLETED,
            "end_time": now,
            "total_distance_m": total_distance_m,
            "heart_rate_data": [
                {
                    "timestamp": p.timestamp,
                    "bpm": p.bpm,
                    "stroke_rate": p.stroke_rate,
                }
                for p in heart_rate_data
            ],
            "lap_data": [
                {
                    "lap_number": lap.lap_number,
                    "distance_m": lap.distance_m,
                    "time_sec": lap.time_sec,
                    "pace": lap.pace,
                }
                for lap in lap_data
            ],
            "motion_data": [
                {
                    "timestamp": m.timestamp,
                    "stroke_length_cm": m.stroke_length_cm,
                    "body_rotation_deg": m.body_rotation_deg,
                }
                for m in motion_data
            ],
            "data_quality": quality,
        }
    }

    await db["training_sessions"].update_one({"_id": sid}, update_doc)

    avg_hr = (
        sum(p.bpm for p in heart_rate_data) / len(heart_rate_data)
        if heart_rate_data
        else 0.0
    )
    avg_pace = (
        sum(lap.pace for lap in lap_data if lap.pace) / len([l for l in lap_data if l.pace])
        if any(l.pace for l in lap_data)
        else 0.0
    )

    suggestion_reason = []
    if avg_hr > 170:
        suggestion_reason.append("平均心率偏高，建议增加休息时间")
    if total_distance_m > 0 and avg_pace and avg_pace > 120:
        suggestion_reason.append("配速偏慢，建议加强耐力训练")
    if quality.get("warning"):
        suggestion_reason.append(f"数据质量评分{quality.get('overall', 0)}分，部分数据经过修复，建议人工核实")
    if not suggestion_reason:
        suggestion_reason.append("训练状态良好，保持当前节奏")

    suggestion_doc = {
        "athlete_id": ObjectId(session["athlete_id"]),
        "session_id": sid,
        "generated_at": now,
        "suggested_pace_sec_per_100m": round(avg_pace, 2) if avg_pace else None,
        "suggested_rest_sec": 30.0 if avg_hr > 160 else 20.0,
        "reason": "；".join(suggestion_reason),
        "coach_modified": False,
        "modified_pace": None,
        "modified_rest": None,
        "notes": None,
        "created_at": now,
    }
    await db["training_suggestions"].insert_one(suggestion_doc)

    await redis.delete(f"session:{session_id}:status")
    await redis.delete(f"session:{session_id}:heart_rate_data")
    await redis.delete(f"session:{session_id}:lap_data")
    await redis.delete(f"session:{session_id}:motion_data")
    await redis.delete(f"session:{session_id}:total_distance")
    for akey in anomaly_keys:
        await redis.delete(akey)

    updated = await db["training_sessions"].find_one({"_id": sid})
    updated["_id"] = str(updated["_id"])
    updated["id"] = str(updated["_id"])
    updated["athlete_id"] = str(updated["athlete_id"])
    if updated.get("coach_id"):
        updated["coach_id"] = str(updated["coach_id"])

    return updated


@router.get("/session/{session_id}/quality")
async def get_session_quality(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    db = get_database()

    try:
        sid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 session_id")

    session = await db["training_sessions"].find_one({"_id": sid})
    if not session:
        raise HTTPException(status_code=404, detail="Session 不存在")

    quality_data = session.get("data_quality")
    if not quality_data:
        hr_data = session.get("heart_rate_data", []) or []
        lap_data = session.get("lap_data", []) or []
        motion_data = session.get("motion_data", []) or []

        hr_dicts = [
            {
                "timestamp": p.get("timestamp", "").isoformat() if isinstance(p.get("timestamp"), datetime) else str(p.get("timestamp", "")),
                "bpm": p.get("bpm", 0),
                "stroke_rate": p.get("stroke_rate"),
            }
            for p in hr_data
        ]
        lap_dicts = [
            {
                "lap_number": l.get("lap_number", 0),
                "distance_m": l.get("distance_m", 0),
                "time_sec": l.get("time_sec", 0),
                "pace": l.get("pace"),
            }
            for l in lap_data
        ]
        motion_dicts = [
            {
                "timestamp": f.get("timestamp", "").isoformat() if isinstance(f.get("timestamp"), datetime) else str(f.get("timestamp", "")),
                "stroke_length_cm": f.get("stroke_length_cm"),
                "body_rotation_deg": f.get("body_rotation_deg"),
            }
            for f in motion_data
        ]

        quality_data = assess_data_quality(hr_dicts, lap_dicts, motion_dicts, [])
        await db["training_sessions"].update_one(
            {"_id": sid},
            {"$set": {"data_quality": quality_data}},
        )

    return {
        "session_id": session_id,
        "quality": quality_data,
    }


@router.post("/session/{session_id}/adjust")
async def coach_adjust_data(
    session_id: str,
    body: CoachAdjustmentRequest,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    db = get_database()

    try:
        sid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 session_id")

    session = await db["training_sessions"].find_one({"_id": sid})
    if not session:
        raise HTTPException(status_code=404, detail="Session 不存在")

    data_field_map = {
        "band": "heart_rate_data",
        "touchwall": "lap_data",
        "camera": "motion_data",
    }

    mongo_field = data_field_map.get(body.data_source)
    if not mongo_field:
        raise HTTPException(status_code=400, detail=f"不支持的数据源: {body.data_source}")

    data_array = session.get(mongo_field, []) or []
    if body.index < 0 or body.index >= len(data_array):
        raise HTTPException(status_code=400, detail=f"索引越界: {body.index}")

    data_array[body.index][body.field] = body.new_value

    log_doc = {
        "session_id": sid,
        "coach_id": ObjectId(current_user.id),
        "data_source": body.data_source,
        "field": body.field,
        "index": body.index,
        "original_value": body.original_value,
        "new_value": body.new_value,
        "reason": body.reason,
        "created_at": datetime.utcnow(),
    }
    await db["coach_adjustment_logs"].insert_one(log_doc)

    await db["training_sessions"].update_one(
        {"_id": sid},
        {"$set": {mongo_field: data_array}},
    )

    return {"status": "ok", "message": "数据已调整，操作已记录"}


@router.get("/session/{session_id}/adjustments")
async def get_session_adjustments(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    db = get_database()

    try:
        sid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 session_id")

    cursor = db["coach_adjustment_logs"].find({"session_id": sid}).sort("created_at", -1)
    logs = await cursor.to_list(length=100)

    result = []
    for log in logs:
        log["_id"] = str(log["_id"])
        log["session_id"] = str(log["session_id"])
        log["coach_id"] = str(log["coach_id"])
        result.append(log)

    return {"adjustments": result, "total": len(result)}


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    db = get_database()

    try:
        sid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 session_id")

    session = await db["training_sessions"].find_one({"_id": sid})
    if not session:
        raise HTTPException(status_code=404, detail="Session 不存在")

    athlete_id = str(session["athlete_id"])
    group_name = session.get("group_name", "")
    coach_id = str(session.get("coach_id", "")) if session.get("coach_id") else ""

    if current_user.role == "athlete":
        if str(current_user.id) != athlete_id:
            raise HTTPException(status_code=403, detail="无权查看此 session")
    elif current_user.role == "coach":
        coach_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
        user_group = coach_user.get("group", "") if coach_user else ""
        if coach_id != str(current_user.id) and group_name != user_group:
            raise HTTPException(status_code=403, detail="无权查看此 session")

    session["_id"] = str(session["_id"])
    session["id"] = str(session["_id"])
    session["athlete_id"] = str(session["athlete_id"])
    if session.get("coach_id"):
        session["coach_id"] = str(session["coach_id"])

    return TrainingSessionResponse(**session)


@router.get("/sessions")
async def list_sessions(
    athlete_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    current_user: UserResponse = Depends(get_current_user),
):
    db = get_database()

    query: dict = {}

    if current_user.role == "athlete":
        query["athlete_id"] = ObjectId(current_user.id)
    elif current_user.role == "coach":
        coach_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
        user_group = coach_user.get("group", "") if coach_user else ""
        query["$or"] = [
            {"coach_id": ObjectId(current_user.id)},
            {"group_name": user_group},
        ]

    if athlete_id:
        if current_user.role == "athlete" and athlete_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="无权查看其他运动员数据")
        query["athlete_id"] = ObjectId(athlete_id)

    if date_from or date_to:
        query["session_date"] = {}
        if date_from:
            query["session_date"]["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            query["session_date"]["$lte"] = datetime.fromisoformat(date_to)

    cursor = db["training_sessions"].find(query).sort("created_at", -1).limit(limit)
    sessions = await cursor.to_list(length=limit)
    total = await db["training_sessions"].count_documents(query)

    result = []
    for s in sessions:
        s["_id"] = str(s["_id"])
        s["id"] = str(s["_id"])
        s["athlete_id"] = str(s["athlete_id"])
        if s.get("coach_id"):
            s["coach_id"] = str(s["coach_id"])
        result.append(TrainingSessionResponse(**s))

    return {"sessions": result, "total": total}


@router.get("/realtime/{session_id}")
async def realtime_stream(
    session_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
):
    redis = get_redis()
    db = get_database()

    try:
        sid_obj = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 session_id")

    status_key = f"session:{session_id}:status"
    session_status = await redis.get(status_key)
    session = await db["training_sessions"].find_one({"_id": sid_obj})
    if not session:
        raise HTTPException(status_code=404, detail="Session 不存在")
    if not session_status and session["status"] != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Session 未在进行中")

    athlete_id = str(session["athlete_id"])
    band_key = f"band:{athlete_id}:{session_id}"
    touch_key = f"touchwall:{athlete_id}:{session_id}"
    camera_key = f"camera:{athlete_id}:{session_id}"

    async def _classify_quality(fields: dict) -> str:
        label = fields.get("quality_label", "normal")
        if label in (QualityLabel.REPAIRED.value, QualityLabel.ABNORMAL.value):
            return label
        return QualityLabel.NORMAL.value

    async def event_generator():
        last_id_band = "0-0"
        last_id_touch = "0-0"
        last_id_camera = "0-0"

        while True:
            if await request.is_disconnected():
                break

            try:
                latest_bpm = None
                latest_lap = None
                total_distance = 0.0
                hr_quality = QualityLabel.NORMAL.value
                lap_quality = QualityLabel.NORMAL.value
                camera_quality = QualityLabel.NORMAL.value

                band_results = await redis.xread(
                    streams={band_key: last_id_band}, count=100, block=100
                )
                if band_results:
                    for _, messages in band_results:
                        for msg_id, fields in messages:
                            last_id_band = msg_id
                            if "bpm" in fields and fields["bpm"]:
                                latest_bpm = int(fields["bpm"])
                            hr_quality = await _classify_quality(fields)

                touch_results = await redis.xread(
                    streams={touch_key: last_id_touch}, count=100, block=100
                )
                if touch_results:
                    for _, messages in touch_results:
                        for msg_id, fields in messages:
                            last_id_touch = msg_id
                            if "lap_number" in fields and fields["lap_number"]:
                                latest_lap = int(fields["lap_number"])
                            lap_quality = await _classify_quality(fields)

                camera_results = await redis.xread(
                    streams={camera_key: last_id_camera}, count=100, block=100
                )
                if camera_results:
                    for _, messages in camera_results:
                        for msg_id, fields in messages:
                            last_id_camera = msg_id
                            camera_quality = await _classify_quality(fields)

                dist_raw = await redis.get(f"session:{session_id}:total_distance")
                if dist_raw:
                    total_distance = float(dist_raw)

                data = {
                    "session_id": session_id,
                    "heart_rate": latest_bpm,
                    "current_lap": latest_lap,
                    "distance_m": round(total_distance, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "quality_labels": {
                        "heart_rate": hr_quality,
                        "lap": lap_quality,
                        "camera": camera_quality,
                    },
                }

                yield {
                    "event": "update",
                    "data": json.dumps(data, ensure_ascii=False),
                }

            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}, ensure_ascii=False),
                }

            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
