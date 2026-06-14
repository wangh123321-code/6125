from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    require_role,
)
from app.database import db, get_redis, get_database
from app.schemas import UserCreate, UserResponse, UserLogin, Token, UserRole
from app.config import settings
from bson import ObjectId
from datetime import datetime, timedelta
import random
import asyncio

router = APIRouter(prefix="/api/auth", tags=["认证管理"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    get_database()

    existing_user = await db["users"].find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    hashed_password = get_password_hash(user_data.password)
    user_doc = {
        "username": user_data.username,
        "hashed_password": hashed_password,
        "full_name": user_data.full_name,
        "role": user_data.role.value,
        "group": user_data.group,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }

    result = await db["users"].insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    return UserResponse(**user_doc)


@router.post("/login")
async def login(user_data: UserLogin):
    get_database()

    user = await db["users"].find_one({"username": user_data.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user),
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_active_user)):
    return current_user


@router.post("/init-demo-data")
async def init_demo_data():
    db = get_database()

    await db["users"].delete_many({})
    await db["athlete_profiles"].delete_many({})

    stats = {"headcoaches": 0, "coaches": 0, "athletes": 0, "profiles": 0}

    hashed_pw = get_password_hash("123456")

    headcoach_doc = {
        "username": "headcoach001",
        "hashed_password": hashed_pw,
        "full_name": "总教练 张主任",
        "role": UserRole.HEADCOACH.value,
        "group": None,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    result = await db["users"].insert_one(headcoach_doc)
    stats["headcoaches"] = 1

    groups = [
        {"name": "自由泳组", "coach": "coach001", "coach_name": "李教练", "athlete_start": 1, "athlete_end": 15},
        {"name": "蛙泳组", "coach": "coach002", "coach_name": "王教练", "athlete_start": 16, "athlete_end": 30},
        {"name": "混合组", "coach": "coach003", "coach_name": "赵教练", "athlete_start": 31, "athlete_end": 45},
    ]

    created_coaches = []
    for g in groups:
        coach_doc = {
            "username": g["coach"],
            "hashed_password": hashed_pw,
            "full_name": g["coach_name"],
            "role": UserRole.COACH.value,
            "group": g["name"],
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        result = await db["users"].insert_one(coach_doc)
        coach_doc["_id"] = result.inserted_id
        created_coaches.append(coach_doc)
        stats["coaches"] += 1

    for g in groups:
        athlete_tasks = []
        for i in range(g["athlete_start"], g["athlete_end"] + 1):
            athlete_num = str(i).zfill(3)
            athlete_doc = {
                "username": f"athlete{athlete_num}",
                "hashed_password": hashed_pw,
                "full_name": f"运动员{athlete_num}",
                "role": UserRole.ATHLETE.value,
                "group": g["name"],
                "is_active": True,
                "created_at": datetime.utcnow(),
            }
            age = random.randint(16, 25)
            height_cm = round(random.uniform(170, 200), 1)
            weight_kg = round(random.uniform(60, 90), 1)
            gender = random.choice(["男", "女"])
            stroke_map = {
                "自由泳组": ["自由泳", "仰泳"],
                "蛙泳组": ["蛙泳", "蝶泳"],
                "混合组": ["自由泳", "蛙泳", "仰泳", "蝶泳"],
            }
            stroke_types = stroke_map.get(g["name"], ["自由泳"])

            result = await db["users"].insert_one(athlete_doc)
            athlete_id = result.inserted_id
            stats["athletes"] += 1

            profile_doc = {
                "user_id": athlete_id,
                "age": age,
                "gender": gender,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "stroke_types": stroke_types,
                "created_at": datetime.utcnow(),
            }
            await db["athlete_profiles"].insert_one(profile_doc)
            stats["profiles"] += 1

    return {
        "message": "演示数据初始化成功",
        "stats": stats,
        "details": {
            "总教练": {"username": "headcoach001", "password": "123456"},
            "教练": [
                {"username": "coach001", "password": "123456", "group": "自由泳组"},
                {"username": "coach002", "password": "123456", "group": "蛙泳组"},
                {"username": "coach003", "password": "123456", "group": "混合组"},
            ],
            "运动员": {
                "count": 45,
                "range": "athlete001 ~ athlete045",
                "password": "123456",
            },
        },
    }


@router.get("/athletes")
async def get_athletes(
    group_name: Optional[str] = Query(None, description="组名称过滤"),
    current_user: UserResponse = Depends(require_role("coach", "headcoach")),
):
    get_database()

    query = {"role": UserRole.ATHLETE.value}

    if current_user.role == UserRole.COACH:
        query["group"] = current_user.group
        if group_name and group_name != current_user.group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="教练只能查看自己组的运动员",
            )
    elif current_user.role == UserRole.HEADCOACH:
        if group_name:
            query["group"] = group_name

    cursor = db["users"].find(query).sort("username", 1)
    athletes = await cursor.to_list(length=None)

    result = []
    for athlete in athletes:
        user_resp = UserResponse(**athlete).model_dump()
        profile = await db["athlete_profiles"].find_one({"user_id": athlete["_id"]})
        if profile:
            user_resp["age"] = profile.get("age")
            user_resp["gender"] = profile.get("gender")
            user_resp["height_cm"] = profile.get("height_cm")
            user_resp["weight_kg"] = profile.get("weight_kg")
            user_resp["stroke_types"] = profile.get("stroke_types", [])
        else:
            user_resp["age"] = None
            user_resp["gender"] = None
            user_resp["height_cm"] = None
            user_resp["weight_kg"] = None
            user_resp["stroke_types"] = []
        result.append(user_resp)

    return result


dashboard_router = APIRouter(tags=["仪表盘"])


@dashboard_router.get("/api/coach/dashboard")
async def coach_dashboard(current_user: UserResponse = Depends(require_role("coach", "headcoach"))):
    get_database()

    session_query = {"status": "completed"}
    if current_user.role == UserRole.COACH:
        session_query["group_name"] = current_user.group

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_athlete_ids = await db["training_sessions"].distinct(
        "athlete_id",
        {**session_query, "session_date": {"$gte": today_start}},
    )

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_report_count = await db["monthly_reports"].count_documents(
        {"created_at": {"$gte": month_start}},
    )

    agg_pipeline = [
        {"$match": session_query},
        {
            "$group": {
                "_id": None,
                "total_distance": {"$sum": "$total_distance_m"},
                "hr_points": {"$push": "$heart_rate_data"},
            }
        },
    ]
    agg_result = await db["training_sessions"].aggregate(agg_pipeline).to_list(length=1)

    total_distance_m = 0.0
    avg_heart_rate = 0.0
    if agg_result:
        total_distance_m = float(agg_result[0].get("total_distance", 0.0))
        all_hr = []
        for hr_list in agg_result[0].get("hr_points", []) or []:
            for point in hr_list or []:
                if point and point.get("bpm"):
                    all_hr.append(int(point["bpm"]))
        if all_hr:
            avg_heart_rate = round(sum(all_hr) / len(all_hr), 2)

    recent_sessions_cursor = db["training_sessions"].find(session_query).sort("created_at", -1).limit(5)
    recent_sessions = await recent_sessions_cursor.to_list(length=5)

    session_list = []
    for s in recent_sessions:
        athlete = await db["users"].find_one({"_id": s["athlete_id"]})
        athlete_name = athlete["full_name"] if athlete else "未知"

        all_paces = []
        for lap in s.get("lap_data", []) or []:
            if lap.get("pace") is not None:
                all_paces.append(float(lap["pace"]))
        avg_pace = round(sum(all_paces) / len(all_paces), 2) if all_paces else 0.0

        hr_values = []
        for point in s.get("heart_rate_data", []) or []:
            if point and point.get("bpm"):
                hr_values.append(int(point["bpm"]))
        session_avg_hr = round(sum(hr_values) / len(hr_values), 2) if hr_values else 0.0

        stroke_types = []
        for motion in s.get("motion_data", []) or []:
            if motion.get("stroke_length_cm") is not None:
                stroke_types.append(float(motion["stroke_length_cm"]))
        avg_stroke = round(sum(stroke_types) / len(stroke_types), 2) if stroke_types else 0.0

        session_list.append({
            "id": str(s["_id"]),
            "athleteName": athlete_name,
            "distance": round(s.get("total_distance_m", 0.0) / 1000, 2),
            "pace": avg_pace,
            "stroke": avg_stroke,
            "avgHeartRate": session_avg_hr,
            "time": s.get("start_time").isoformat() if s.get("start_time") else None,
        })

    return {
        "stats": {
            "todayTrainees": len(today_athlete_ids),
            "totalDistance": round(total_distance_m / 1000, 2),
            "monthlyReports": monthly_report_count,
            "avgHeartRate": avg_heart_rate,
        },
        "sessions": session_list,
    }


@dashboard_router.get("/api/headcoach/all-data")
@dashboard_router.get("/api/headcoach/group-stats")
async def headcoach_all_data(current_user: UserResponse = Depends(require_role("headcoach"))):
    get_database()

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    coaches_cursor = db["users"].find({"role": UserRole.COACH.value, "is_active": True})
    coaches_list = await coaches_cursor.to_list(length=None)

    groups_data = []
    coaches_info = []
    for c in coaches_list:
        group_name = c.get("group", "")
        coaches_info.append({
            "name": c["full_name"],
            "group": group_name,
            "id": str(c["_id"]),
        })

        member_count = await db["users"].count_documents({
            "role": UserRole.ATHLETE.value,
            "group": group_name,
            "is_active": True,
        })

        group_agg = [
            {"$match": {"group_name": group_name, "status": "completed"}},
            {
                "$group": {
                    "_id": None,
                    "total_distance": {"$sum": "$total_distance_m"},
                    "lap_paces": {"$push": "$lap_data"},
                }
            },
        ]
        group_result = await db["training_sessions"].aggregate(group_agg).to_list(length=1)

        group_total_dist = 0.0
        group_avg_pace = 0.0
        if group_result:
            group_total_dist = float(group_result[0].get("total_distance", 0.0))
            all_paces = []
            for pace_list in group_result[0].get("lap_paces", []) or []:
                for p in pace_list or []:
                    if p and p.get("pace") is not None:
                        all_paces.append(float(p["pace"]))
            if all_paces:
                group_avg_pace = round(sum(all_paces) / len(all_paces), 2)

        group_total_sessions = await db["training_sessions"].count_documents({
            "group_name": group_name,
        })
        group_completed_sessions = await db["training_sessions"].count_documents({
            "group_name": group_name,
            "status": "completed",
        })
        group_completion_rate = 0.0
        if group_total_sessions > 0:
            group_completion_rate = round(group_completed_sessions / group_total_sessions * 100, 1)

        groups_data.append({
            "name": group_name,
            "memberCount": member_count,
            "totalAthletes": member_count,
            "totalDistance": round(group_total_dist / 1000, 2),
            "avgPace": group_avg_pace,
            "completionRate": group_completion_rate,
            "coachName": c["full_name"],
        })

    athletes_cursor = db["users"].find({"role": UserRole.ATHLETE.value, "is_active": True})
    athletes_list = await athletes_cursor.to_list(length=None)

    athletes_data = []
    for a in athletes_list:
        aid = a["_id"]
        athlete_agg = [
            {"$match": {"athlete_id": aid, "status": "completed"}},
            {
                "$group": {
                    "_id": None,
                    "total_distance": {"$sum": "$total_distance_m"},
                    "lap_paces": {"$push": "$lap_data"},
                    "hr_points": {"$push": "$heart_rate_data"},
                    "session_count": {"$sum": 1},
                }
            },
        ]
        athlete_result = await db["training_sessions"].aggregate(athlete_agg).to_list(length=1)

        month_agg = [
            {"$match": {"athlete_id": aid, "status": "completed", "session_date": {"$gte": month_start}}},
            {
                "$group": {
                    "_id": None,
                    "total_distance": {"$sum": "$total_distance_m"},
                }
            },
        ]
        month_result = await db["training_sessions"].aggregate(month_agg).to_list(length=1)
        month_distance = 0.0
        if month_result:
            month_distance = round(float(month_result[0].get("total_distance", 0.0)) / 1000, 2)

        a_total_dist = 0.0
        a_avg_pace = 0.0
        a_avg_hr = 0.0
        completion_rate = 0.0
        if athlete_result:
            a_total_dist = float(athlete_result[0].get("total_distance", 0.0))

            all_paces = []
            for pace_list in athlete_result[0].get("lap_paces", []) or []:
                for p in pace_list or []:
                    if p and p.get("pace") is not None:
                        all_paces.append(float(p["pace"]))
            if all_paces:
                a_avg_pace = round(sum(all_paces) / len(all_paces), 2)

            all_hr = []
            for hr_list in athlete_result[0].get("hr_points", []) or []:
                for point in hr_list or []:
                    if point and point.get("bpm"):
                        all_hr.append(int(point["bpm"]))
            if all_hr:
                a_avg_hr = round(sum(all_hr) / len(all_hr), 2)

            total_sessions = await db["training_sessions"].count_documents({"athlete_id": aid})
            completed_sessions = athlete_result[0].get("session_count", 0)
            if total_sessions > 0:
                completion_rate = round(completed_sessions / total_sessions * 100, 1)

        profile = await db["athlete_profiles"].find_one({"user_id": aid})
        age = None
        gender = None
        height = None
        weight = None
        specialty = ""
        if profile:
            age = profile.get("age")
            gender = profile.get("gender")
            height = profile.get("height_cm")
            weight = profile.get("weight_kg")
            stroke_types = profile.get("stroke_types", [])
            specialty = stroke_types[0] if stroke_types else ""

        athletes_data.append({
            "id": str(aid),
            "name": a["full_name"],
            "full_name": a["full_name"],
            "group": a.get("group", ""),
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight,
            "specialty": specialty,
            "totalDistance": round(a_total_dist / 1000, 2),
            "monthDistance": month_distance,
            "avgPace": a_avg_pace,
            "avgHeartRate": a_avg_hr,
            "completionRate": completion_rate,
            "attendanceRate": completion_rate,
        })

    return {
        "groups": groups_data,
        "athletes": athletes_data,
        "coaches": coaches_info,
    }
