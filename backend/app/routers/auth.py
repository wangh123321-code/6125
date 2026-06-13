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


@router.get("/athletes", response_model=list[UserResponse])
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

    return [UserResponse(**athlete) for athlete in athletes]
