import asyncio
import json
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.database import get_database, get_redis_client as get_redis
from app.schemas import (
    HeartRateDataPoint,
    LapDataPoint,
    MotionDataPoint,
    SessionStatus,
    TrainingSessionResponse,
    UserResponse,
)
from app.utils.auth import require_role, get_current_user
from app.utils.helpers import align_timestamps

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

    stream_key = f"band:{body.athlete_id}:{body.session_id}"
    cache_key = f"session:{body.session_id}:heart_rate_data"

    tasks = []

    async def write_stream(point: HeartRateDataPoint):
        await redis.xadd(
            stream_key,
            {
                "timestamp": point.timestamp.isoformat(),
                "bpm": str(point.bpm),
                "stroke_rate": str(point.stroke_rate) if point.stroke_rate else "",
            },
        )

    async def write_cache(point: HeartRateDataPoint):
        await redis.rpush(
            cache_key,
            json.dumps(
                {
                    "timestamp": point.timestamp.isoformat(),
                    "bpm": point.bpm,
                    "stroke_rate": point.stroke_rate,
                },
                ensure_ascii=False,
            ),
        )

    for point in body.points:
        tasks.append(write_stream(point))
        tasks.append(write_cache(point))

    await asyncio.gather(*tasks)

    return {"received": len(body.points), "status": "ok"}


@router.post("/touchwall")
async def upload_touchwall_data(
    body: TouchWallTimerRequest,
    current_user: UserResponse = Depends(require_role("coach", "headcoach", "athlete")),
):
    redis = get_redis()
    db = get_database()

    stream_key = f"touchwall:{body.athlete_id}:{body.session_id}"
    cache_key = f"session:{body.session_id}:lap_data"
    dist_key = f"session:{body.session_id}:total_distance"

    total_distance = 0.0

    tasks = []

    async def write_stream(lap: LapDataPoint):
        await redis.xadd(
            stream_key,
            {
                "lap_number": str(lap.lap_number),
                "distance_m": str(lap.distance_m),
                "time_sec": str(lap.time_sec),
                "pace": str(lap.pace) if lap.pace else "",
            },
        )

    async def write_cache(lap: LapDataPoint):
        await redis.rpush(
            cache_key,
            json.dumps(
                {
                    "lap_number": lap.lap_number,
                    "distance_m": lap.distance_m,
                    "time_sec": lap.time_sec,
                    "pace": lap.pace,
                },
                ensure_ascii=False,
            ),
        )

    for lap in body.laps:
        total_distance += lap.distance_m
        tasks.append(write_stream(lap))
        tasks.append(write_cache(lap))

    await asyncio.gather(*tasks)

    existing_dist = await redis.get(dist_key)
    if existing_dist:
        total_distance += float(existing_dist)
    await redis.set(dist_key, str(total_distance))

    return {"received": len(body.laps), "total_distance": total_distance}


@router.post("/camera")
async def upload_camera_data(
    body: CameraAnalysisRequest,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    redis = get_redis()
    db = get_database()

    stream_key = f"camera:{body.athlete_id}:{body.session_id}"
    cache_key = f"session:{body.session_id}:motion_data"

    tasks = []

    async def write_stream(frame: MotionDataPoint):
        await redis.xadd(
            stream_key,
            {
                "timestamp": frame.timestamp.isoformat(),
                "stroke_length_cm": str(frame.stroke_length_cm) if frame.stroke_length_cm else "",
                "body_rotation_deg": str(frame.body_rotation_deg) if frame.body_rotation_deg else "",
            },
        )

    async def write_cache(frame: MotionDataPoint):
        await redis.rpush(
            cache_key,
            json.dumps(
                {
                    "timestamp": frame.timestamp.isoformat(),
                    "stroke_length_cm": frame.stroke_length_cm,
                    "body_rotation_deg": frame.body_rotation_deg,
                },
                ensure_ascii=False,
            ),
        )

    for frame in body.frames:
        tasks.append(write_stream(frame))
        tasks.append(write_cache(frame))

    await asyncio.gather(*tasks)

    return {"received": len(body.frames), "status": "ok"}


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

    heart_rate_data = []
    for item in hr_raw:
        d = json.loads(item)
        heart_rate_data.append(
            HeartRateDataPoint(
                timestamp=datetime.fromisoformat(d["timestamp"]),
                bpm=d["bpm"],
                stroke_rate=d.get("stroke_rate"),
            )
        )

    lap_data = []
    for item in lap_raw:
        d = json.loads(item)
        lap_data.append(
            LapDataPoint(
                lap_number=d["lap_number"],
                distance_m=d["distance_m"],
                time_sec=d["time_sec"],
                pace=d.get("pace"),
            )
        )

    motion_data = []
    for item in motion_raw:
        d = json.loads(item)
        motion_data.append(
            MotionDataPoint(
                timestamp=datetime.fromisoformat(d["timestamp"]),
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

    updated = await db["training_sessions"].find_one({"_id": sid})
    updated["_id"] = str(updated["_id"])
    updated["id"] = str(updated["_id"])
    updated["athlete_id"] = str(updated["athlete_id"])
    if updated.get("coach_id"):
        updated["coach_id"] = str(updated["coach_id"])

    return updated


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

    async def event_generator():
        last_id_band = "0-0"
        last_id_touch = "0-0"

        while True:
            if await request.is_disconnected():
                break

            try:
                latest_bpm = None
                latest_lap = None
                total_distance = 0.0

                band_results = await redis.xread(
                    streams={band_key: last_id_band}, count=100, block=100
                )
                if band_results:
                    for _, messages in band_results:
                        for msg_id, fields in messages:
                            last_id_band = msg_id
                            if "bpm" in fields and fields["bpm"]:
                                latest_bpm = int(fields["bpm"])

                touch_results = await redis.xread(
                    streams={touch_key: last_id_touch}, count=100, block=100
                )
                if touch_results:
                    for _, messages in touch_results:
                        for msg_id, fields in messages:
                            last_id_touch = msg_id
                            if "lap_number" in fields and fields["lap_number"]:
                                latest_lap = int(fields["lap_number"])

                dist_raw = await redis.get(f"session:{session_id}:total_distance")
                if dist_raw:
                    total_distance = float(dist_raw)

                data = {
                    "session_id": session_id,
                    "heart_rate": latest_bpm,
                    "current_lap": latest_lap,
                    "distance_m": round(total_distance, 2),
                    "timestamp": datetime.utcnow().isoformat(),
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
