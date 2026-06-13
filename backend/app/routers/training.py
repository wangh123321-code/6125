from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import db, get_database
from app.schemas import (
    PlanStatus,
    TrainingPlanCreate,
    TrainingPlanResponse,
    TrainingSuggestionResponse,
    TrainingSuggestionUpdate,
    UserResponse,
)
from app.utils.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/training", tags=["训练计划与建议"])


async def _check_coach_athlete_group(coach_id: str, athlete_id: str) -> None:
    get_database()
    coach = await db["users"].find_one({"_id": ObjectId(coach_id)})
    athlete = await db["users"].find_one({"_id": ObjectId(athlete_id)})
    if not coach or not athlete:
        raise HTTPException(status_code=404, detail="教练或运动员不存在")
    if coach.get("group") != athlete.get("group"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="教练只能为自己组的运动员创建训练计划",
        )


async def _get_accessible_athlete_ids(current_user: UserResponse) -> list[ObjectId]:
    get_database()
    if current_user.role == "athlete":
        return [ObjectId(current_user.id)]
    elif current_user.role == "coach":
        coach_group = current_user.group
        cursor = db["users"].find({"role": "athlete", "group": coach_group}, {"_id": 1})
        athletes = await cursor.to_list(length=None)
        return [a["_id"] for a in athletes]
    else:
        cursor = db["users"].find({"role": "athlete"}, {"_id": 1})
        athletes = await cursor.to_list(length=None)
        return [a["_id"] for a in athletes]


async def _can_access_athlete(
    athlete_id: ObjectId, current_user: UserResponse
) -> bool:
    get_database()
    if current_user.role == "athlete":
        return str(athlete_id) == str(current_user.id)
    elif current_user.role == "coach":
        coach_group = current_user.group
        athlete = await db["users"].find_one({"_id": athlete_id})
        if not athlete:
            return False
        return athlete.get("group") == coach_group
    else:
        return True


@router.post("/plan", response_model=TrainingPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_training_plan(
    plan_data: TrainingPlanCreate,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    get_database()

    try:
        athlete_oid = ObjectId(plan_data.athlete_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 athlete_id")

    if current_user.role == "coach":
        await _check_coach_athlete_group(current_user.id, plan_data.athlete_id)

    coach_oid = None
    if plan_data.coach_id:
        try:
            coach_oid = ObjectId(plan_data.coach_id)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的 coach_id")
    else:
        coach_oid = ObjectId(current_user.id)

    plan_doc = {
        "athlete_id": athlete_oid,
        "coach_id": coach_oid,
        "plan_date": plan_data.plan_date,
        "sessions": [s.model_dump() for s in plan_data.sessions],
        "status": plan_data.status.value if isinstance(plan_data.status, PlanStatus) else plan_data.status,
        "created_at": datetime.utcnow(),
    }

    result = await db["training_plans"].insert_one(plan_doc)
    plan_doc["_id"] = result.inserted_id

    return TrainingPlanResponse(**plan_doc)


@router.get("/plans", response_model=list[TrainingPlanResponse])
async def list_training_plans(
    athlete_id: Optional[str] = Query(None, description="运动员ID过滤"),
    date_from: Optional[str] = Query(None, description="开始日期(YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期(YYYY-MM-DD)"),
    current_user: UserResponse = Depends(get_current_active_user),
):
    get_database()

    accessible_ids = await _get_accessible_athlete_ids(current_user)
    query: dict = {"athlete_id": {"$in": accessible_ids}, "status": {"$ne": PlanStatus.ARCHIVED}}

    if athlete_id:
        try:
            target_oid = ObjectId(athlete_id)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的 athlete_id")
        if not await _can_access_athlete(target_oid, current_user):
            raise HTTPException(status_code=403, detail="无权查看该运动员数据")
        query["athlete_id"] = target_oid

    if date_from or date_to:
        query["plan_date"] = {}
        if date_from:
            query["plan_date"]["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            query["plan_date"]["$lte"] = datetime.fromisoformat(date_to)

    cursor = db["training_plans"].find(query).sort("plan_date", -1)
    plans = await cursor.to_list(length=None)

    result = []
    for p in plans:
        p["_id"] = str(p["_id"])
        p["athlete_id"] = str(p["athlete_id"])
        if p.get("coach_id"):
            p["coach_id"] = str(p["coach_id"])
        result.append(TrainingPlanResponse(**p))

    return result


@router.get("/plan/{plan_id}", response_model=TrainingPlanResponse)
async def get_training_plan(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
):
    get_database()

    try:
        pid = ObjectId(plan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 plan_id")

    plan = await db["training_plans"].find_one({"_id": pid})
    if not plan:
        raise HTTPException(status_code=404, detail="训练计划不存在")

    athlete_oid = plan["athlete_id"]
    if not await _can_access_athlete(athlete_oid, current_user):
        raise HTTPException(status_code=403, detail="无权查看此训练计划")

    plan["_id"] = str(plan["_id"])
    plan["athlete_id"] = str(plan["athlete_id"])
    if plan.get("coach_id"):
        plan["coach_id"] = str(plan["coach_id"])

    return TrainingPlanResponse(**plan)


@router.put("/plan/{plan_id}", response_model=TrainingPlanResponse)
async def update_training_plan(
    plan_id: str,
    plan_data: TrainingPlanCreate,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    get_database()

    try:
        pid = ObjectId(plan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 plan_id")

    plan = await db["training_plans"].find_one({"_id": pid})
    if not plan:
        raise HTTPException(status_code=404, detail="训练计划不存在")

    if current_user.role == "coach":
        athlete_oid = plan["athlete_id"]
        if not await _can_access_athlete(athlete_oid, current_user):
            raise HTTPException(status_code=403, detail="无权修改此训练计划")

    try:
        athlete_oid = ObjectId(plan_data.athlete_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 athlete_id")

    if current_user.role == "coach":
        await _check_coach_athlete_group(current_user.id, plan_data.athlete_id)

    coach_oid = None
    if plan_data.coach_id:
        try:
            coach_oid = ObjectId(plan_data.coach_id)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的 coach_id")
    else:
        coach_oid = ObjectId(current_user.id)

    update_doc = {
        "$set": {
            "athlete_id": athlete_oid,
            "coach_id": coach_oid,
            "plan_date": plan_data.plan_date,
            "sessions": [s.model_dump() for s in plan_data.sessions],
            "status": plan_data.status.value if isinstance(plan_data.status, PlanStatus) else plan_data.status,
        }
    }

    await db["training_plans"].update_one({"_id": pid}, update_doc)

    updated = await db["training_plans"].find_one({"_id": pid})
    updated["_id"] = str(updated["_id"])
    updated["athlete_id"] = str(updated["athlete_id"])
    if updated.get("coach_id"):
        updated["coach_id"] = str(updated["coach_id"])

    return TrainingPlanResponse(**updated)


@router.delete("/plan/{plan_id}", response_model=dict)
async def delete_training_plan(
    plan_id: str,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    get_database()

    try:
        pid = ObjectId(plan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 plan_id")

    plan = await db["training_plans"].find_one({"_id": pid})
    if not plan:
        raise HTTPException(status_code=404, detail="训练计划不存在")

    if current_user.role == "coach":
        athlete_oid = plan["athlete_id"]
        if not await _can_access_athlete(athlete_oid, current_user):
            raise HTTPException(status_code=403, detail="无权删除此训练计划")

    await db["training_plans"].update_one(
        {"_id": pid},
        {"$set": {"status": PlanStatus.ARCHIVED}},
    )

    return {"message": "训练计划已归档删除", "plan_id": plan_id}


@router.get("/suggestions", response_model=list[TrainingSuggestionResponse])
async def list_training_suggestions(
    athlete_id: Optional[str] = Query(None, description="运动员ID过滤"),
    session_id: Optional[str] = Query(None, description="训练会话ID过滤"),
    current_user: UserResponse = Depends(get_current_active_user),
):
    get_database()

    accessible_ids = await _get_accessible_athlete_ids(current_user)
    query: dict = {"athlete_id": {"$in": accessible_ids}}

    if athlete_id:
        try:
            target_oid = ObjectId(athlete_id)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的 athlete_id")
        if not await _can_access_athlete(target_oid, current_user):
            raise HTTPException(status_code=403, detail="无权查看该运动员数据")
        query["athlete_id"] = target_oid

    if session_id:
        try:
            query["session_id"] = ObjectId(session_id)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的 session_id")

    cursor = db["training_suggestions"].find(query).sort("generated_at", -1)
    suggestions = await cursor.to_list(length=None)

    result = []
    for s in suggestions:
        s["_id"] = str(s["_id"])
        s["athlete_id"] = str(s["athlete_id"])
        s["session_id"] = str(s["session_id"])
        result.append(TrainingSuggestionResponse(**s))

    return result


@router.put("/suggestion/{suggestion_id}", response_model=TrainingSuggestionResponse)
async def update_training_suggestion(
    suggestion_id: str,
    suggestion_data: TrainingSuggestionUpdate,
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    get_database()

    try:
        sid = ObjectId(suggestion_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 suggestion_id")

    suggestion = await db["training_suggestions"].find_one({"_id": sid})
    if not suggestion:
        raise HTTPException(status_code=404, detail="训练建议不存在")

    athlete_oid = suggestion["athlete_id"]
    if current_user.role == "coach":
        if not await _can_access_athlete(athlete_oid, current_user):
            raise HTTPException(status_code=403, detail="无权修改此训练建议")

    update_fields: dict = {"coach_modified": True}
    if suggestion_data.modified_pace is not None:
        update_fields["modified_pace"] = suggestion_data.modified_pace
    if suggestion_data.modified_rest is not None:
        update_fields["modified_rest"] = suggestion_data.modified_rest
    if suggestion_data.notes is not None:
        update_fields["notes"] = suggestion_data.notes

    await db["training_suggestions"].update_one(
        {"_id": sid},
        {"$set": update_fields},
    )

    updated = await db["training_suggestions"].find_one({"_id": sid})
    updated["_id"] = str(updated["_id"])
    updated["athlete_id"] = str(updated["athlete_id"])
    updated["session_id"] = str(updated["session_id"])

    return TrainingSuggestionResponse(**updated)


@router.get("/stats/athlete/{athlete_id}")
async def get_athlete_stats(
    athlete_id: str,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: UserResponse = Depends(get_current_active_user),
):
    get_database()

    try:
        athlete_oid = ObjectId(athlete_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 athlete_id")

    if not await _can_access_athlete(athlete_oid, current_user):
        raise HTTPException(status_code=403, detail="无权查看该运动员统计数据")

    start_date = datetime.utcnow() - timedelta(days=days)

    pipeline = [
        {
            "$match": {
                "athlete_id": athlete_oid,
                "session_date": {"$gte": start_date},
                "status": "completed",
            }
        },
        {
            "$group": {
                "_id": None,
                "total_distance": {"$sum": "$total_distance_m"},
                "session_count": {"$sum": 1},
                "avg_pace_list": {
                    "$push": {
                        "$avg": {
                            "$filter": {
                                "input": "$lap_data.pace",
                                "cond": {"$ne": ["$$this", None]},
                            }
                        }
                    }
                },
                "hr_points": {"$push": "$heart_rate_data"},
                "all_lap_paces": {"$push": "$lap_data.pace"},
            }
        },
    ]

    agg_result = await db["training_sessions"].aggregate(pipeline).to_list(length=1)

    total_distance = 0.0
    session_count = 0
    avg_heart_rate = 0.0
    avg_pace = 0.0
    best_pace = 0.0

    if agg_result:
        data = agg_result[0]
        total_distance = float(data.get("total_distance", 0.0))
        session_count = int(data.get("session_count", 0))

        all_paces = []
        for pace_list in data.get("all_lap_paces", []) or []:
            for p in pace_list or []:
                if p is not None:
                    all_paces.append(float(p))

        if all_paces:
            avg_pace = round(sum(all_paces) / len(all_paces), 2)
            best_pace = round(min(all_paces), 2)

        all_hr_values = []
        for hr_list in data.get("hr_points", []) or []:
            for point in hr_list or []:
                if point and point.get("bpm"):
                    all_hr_values.append(int(point["bpm"]))

        if all_hr_values:
            avg_heart_rate = round(sum(all_hr_values) / len(all_hr_values), 2)

    trend_pipeline = [
        {
            "$match": {
                "athlete_id": athlete_oid,
                "session_date": {"$gte": start_date},
                "status": "completed",
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$session_date"}
                },
                "distance": {"$sum": "$total_distance_m"},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    trend_result = await db["training_sessions"].aggregate(trend_pipeline).to_list(length=None)
    distance_trend = [{"date": t["_id"], "distance": float(t["distance"])} for t in trend_result]

    hr_distribution = {"warmup": 0, "aerobic": 0, "anaerobic": 0, "extreme": 0}

    hr_pipeline = [
        {
            "$match": {
                "athlete_id": athlete_oid,
                "session_date": {"$gte": start_date},
                "status": "completed",
            }
        },
        {"$project": {"heart_rate_data": 1, "_id": 0}},
        {"$unwind": "$heart_rate_data"},
    ]

    hr_points = await db["training_sessions"].aggregate(hr_pipeline).to_list(length=None)
    for point in hr_points:
        hr = point["heart_rate_data"].get("bpm", 0)
        if hr < 120:
            hr_distribution["warmup"] += 1
        elif hr < 150:
            hr_distribution["aerobic"] += 1
        elif hr < 175:
            hr_distribution["anaerobic"] += 1
        else:
            hr_distribution["extreme"] += 1

    total_hr = sum(hr_distribution.values())
    if total_hr > 0:
        for k in hr_distribution:
            hr_distribution[k] = round(hr_distribution[k] / total_hr, 4)

    return {
        "total_distance": round(total_distance, 2),
        "session_count": session_count,
        "avg_heart_rate": avg_heart_rate,
        "avg_pace": avg_pace,
        "best_pace": best_pace,
        "distance_trend": distance_trend,
        "heart_rate_distribution": hr_distribution,
    }


@router.get("/peer-comparison/{athlete_id}")
async def get_peer_comparison(
    athlete_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
):
    get_database()

    try:
        athlete_oid = ObjectId(athlete_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 athlete_id")

    if not await _can_access_athlete(athlete_oid, current_user):
        raise HTTPException(status_code=403, detail="无权查看该运动员对比数据")

    target_athlete = await db["users"].find_one({"_id": athlete_oid})
    if not target_athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")

    group_name = target_athlete.get("group")
    if not group_name:
        raise HTTPException(status_code=400, detail="运动员所属组未知")

    group_athletes_cursor = db["users"].find({"role": "athlete", "group": group_name}, {"_id": 1})
    group_athletes = await group_athletes_cursor.to_list(length=None)
    group_ids = [a["_id"] for a in group_athletes]

    days = 30
    start_date = datetime.utcnow() - timedelta(days=days)

    per_athlete_pipeline = [
        {
            "$match": {
                "athlete_id": {"$in": group_ids},
                "session_date": {"$gte": start_date},
                "status": "completed",
            }
        },
        {
            "$group": {
                "_id": "$athlete_id",
                "total_distance": {"$sum": "$total_distance_m"},
                "session_count": {"$sum": 1},
                "lap_paces": {"$push": "$lap_data.pace"},
                "hr_points": {"$push": "$heart_rate_data"},
                "stroke_lengths": {"$push": "$motion_data.stroke_length_cm"},
            }
        },
    ]

    per_athlete = await db["training_sessions"].aggregate(per_athlete_pipeline).to_list(length=None)

    athlete_stats: dict[str, dict] = {}
    for item in per_athlete:
        aid = str(item["_id"])
        all_paces = []
        for pace_list in item.get("lap_paces", []) or []:
            for p in pace_list or []:
                if p is not None:
                    all_paces.append(float(p))

        avg_pace = round(sum(all_paces) / len(all_paces), 2) if all_paces else 0.0

        all_hr = []
        for hr_list in item.get("hr_points", []) or []:
            for point in hr_list or []:
                if point and point.get("bpm"):
                    all_hr.append(int(point["bpm"]))

        avg_hr = round(sum(all_hr) / len(all_hr), 2) if all_hr else 0.0

        all_sl = []
        for sl_list in item.get("stroke_lengths", []) or []:
            for sl in sl_list or []:
                if sl is not None:
                    all_sl.append(float(sl))

        avg_sl = round(sum(all_sl) / len(all_sl), 2) if all_sl else 0.0

        athlete_stats[aid] = {
            "total_distance": float(item.get("total_distance", 0.0)),
            "avg_pace": avg_pace,
            "avg_heart_rate": avg_hr,
            "avg_stroke_length": avg_sl,
        }

    if not athlete_stats:
        return []

    metrics_map = {
        "平均配速(秒/100米)": "avg_pace",
        "平均心率(bpm)": "avg_heart_rate",
        "总距离(米)": "total_distance",
        "平均划距(厘米)": "avg_stroke_length",
    }

    result = []
    target_stats = athlete_stats.get(str(athlete_oid), {})

    for metric_name, metric_key in metrics_map.items():
        all_values = []
        for aid, stats in athlete_stats.items():
            val = stats.get(metric_key, 0.0)
            if val > 0:
                all_values.append(val)

        if not all_values:
            continue

        athlete_value = target_stats.get(metric_key, 0.0)
        group_avg = round(sum(all_values) / len(all_values), 2)

        sorted_values = sorted(all_values)
        if athlete_value > 0:
            lower_count = len([v for v in sorted_values if v <= athlete_value])
            percentile = round((lower_count / len(sorted_values)) * 100, 1)
        else:
            percentile = 0.0

        if metric_key == "avg_pace":
            lower_count = len([v for v in sorted_values if v >= athlete_value]) if athlete_value > 0 else 0
            percentile = round((lower_count / len(sorted_values)) * 100, 1) if athlete_value > 0 else 0.0

        result.append(
            {
                "metric": metric_name,
                "athlete_value": athlete_value,
                "group_avg": group_avg,
                "percentile": percentile,
            }
        )

    return result
