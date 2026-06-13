from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    ATHLETE = "athlete"
    COACH = "coach"
    HEADCOACH = "headcoach"


class SessionStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"


class PlanStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class User(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    username: str
    password_hash: str
    full_name: str
    role: UserRole
    group: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AthleteProfile(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user_id: ObjectId
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    stroke_types: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class HeartRateDataPoint(BaseModel):
    timestamp: datetime
    bpm: int
    stroke_rate: Optional[float] = None


class LapDataPoint(BaseModel):
    lap_number: int
    distance_m: float
    time_sec: float
    pace: Optional[float] = None


class MotionDataPoint(BaseModel):
    timestamp: datetime
    stroke_length_cm: Optional[float] = None
    body_rotation_deg: Optional[float] = None


class TrainingSession(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    athlete_id: ObjectId
    session_date: datetime
    start_time: datetime
    end_time: Optional[datetime] = None
    total_distance_m: float = 0.0
    heart_rate_data: list[HeartRateDataPoint] = Field(default_factory=list)
    lap_data: list[LapDataPoint] = Field(default_factory=list)
    motion_data: list[MotionDataPoint] = Field(default_factory=list)
    coach_id: Optional[ObjectId] = None
    group_name: Optional[str] = None
    status: SessionStatus = SessionStatus.IN_PROGRESS
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TrainingSet(BaseModel):
    distance_m: float
    target_pace_sec: Optional[float] = None
    rest_sec: Optional[float] = None


class TrainingPlanSession(BaseModel):
    date: datetime
    warmup_distance: float = 0.0
    main_set: list[TrainingSet] = Field(default_factory=list)
    cool_down_distance: float = 0.0
    notes: Optional[str] = None


class TrainingPlan(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    athlete_id: ObjectId
    coach_id: Optional[ObjectId] = None
    plan_date: datetime
    sessions: list[TrainingPlanSession] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TrainingSuggestion(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    athlete_id: ObjectId
    session_id: ObjectId
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    suggested_pace_sec_per_100m: Optional[float] = None
    suggested_rest_sec: Optional[float] = None
    reason: Optional[str] = None
    coach_modified: bool = False
    modified_pace: Optional[float] = None
    modified_rest: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class StrokeBreakdownItem(BaseModel):
    stroke: str
    distance_m: float
    percentage: float


class HeartRateZoneItem(BaseModel):
    zone: str
    minutes: float
    percentage: float


class TechniqueTrendItem(BaseModel):
    metric: str
    values: list[float] = Field(default_factory=list)
    trend: Optional[str] = None


class MonthlyComparisonItem(BaseModel):
    metric: str
    current: float
    previous: float
    changed_percent: float
    regressed: bool = False


class MonthlyReport(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    athlete_id: ObjectId
    year: int
    month: int
    total_distance_m: float = 0.0
    stroke_breakdown: list[StrokeBreakdownItem] = Field(default_factory=list)
    heart_rate_zones: list[HeartRateZoneItem] = Field(default_factory=list)
    technique_trends: list[TechniqueTrendItem] = Field(default_factory=list)
    comparison_to_last_month: list[MonthlyComparisonItem] = Field(default_factory=list)
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
