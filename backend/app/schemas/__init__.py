from datetime import datetime
from typing import Optional, Any
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from typing_extensions import Annotated
from enum import Enum


PyObjectId = Annotated[
    str,
    BeforeValidator(
        lambda x: str(x) if isinstance(x, ObjectId) else x
    ),
]


def _object_id_validate(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    return str(v)


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


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: UserRole
    group: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id", serialization_alias="id")
    username: str
    full_name: str
    role: UserRole
    group: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None
    user_id: Optional[str] = None


class AthleteProfileCreate(BaseModel):
    user_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    stroke_types: list[str] = Field(default_factory=list)


class AthleteProfileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id", serialization_alias="id")
    user_id: PyObjectId
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    stroke_types: list[str] = Field(default_factory=list)
    created_at: datetime


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


class TrainingSessionCreate(BaseModel):
    athlete_id: str
    session_date: datetime
    start_time: datetime
    end_time: Optional[datetime] = None
    total_distance_m: float = 0.0
    heart_rate_data: list[HeartRateDataPoint] = Field(default_factory=list)
    lap_data: list[LapDataPoint] = Field(default_factory=list)
    motion_data: list[MotionDataPoint] = Field(default_factory=list)
    coach_id: Optional[str] = None
    group_name: Optional[str] = None
    status: SessionStatus = SessionStatus.IN_PROGRESS


class TrainingSessionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id", serialization_alias="id")
    athlete_id: PyObjectId
    session_date: datetime
    start_time: datetime
    end_time: Optional[datetime] = None
    total_distance_m: float = 0.0
    heart_rate_data: list[HeartRateDataPoint] = Field(default_factory=list)
    lap_data: list[LapDataPoint] = Field(default_factory=list)
    motion_data: list[MotionDataPoint] = Field(default_factory=list)
    coach_id: Optional[PyObjectId] = None
    group_name: Optional[str] = None
    status: SessionStatus
    created_at: datetime


class TrainingSessionListResponse(BaseModel):
    sessions: list[TrainingSessionResponse]
    total: int


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


class TrainingPlanCreate(BaseModel):
    athlete_id: str
    coach_id: Optional[str] = None
    plan_date: datetime
    sessions: list[TrainingPlanSession] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT


class TrainingPlanResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id", serialization_alias="id")
    athlete_id: PyObjectId
    coach_id: Optional[PyObjectId] = None
    plan_date: datetime
    sessions: list[TrainingPlanSession] = Field(default_factory=list)
    status: PlanStatus
    created_at: datetime


class TrainingSuggestionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id", serialization_alias="id")
    athlete_id: PyObjectId
    session_id: PyObjectId
    generated_at: datetime
    suggested_pace_sec_per_100m: Optional[float] = None
    suggested_rest_sec: Optional[float] = None
    reason: Optional[str] = None
    coach_modified: bool = False
    modified_pace: Optional[float] = None
    modified_rest: Optional[float] = None
    notes: Optional[str] = None


class TrainingSuggestionUpdate(BaseModel):
    coach_modified: Optional[bool] = None
    modified_pace: Optional[float] = None
    modified_rest: Optional[float] = None
    notes: Optional[str] = None


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


class MonthlyReportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(validation_alias="_id", serialization_alias="id")
    athlete_id: PyObjectId
    year: int
    month: int
    total_distance_m: float = 0.0
    stroke_breakdown: list[StrokeBreakdownItem] = Field(default_factory=list)
    heart_rate_zones: list[HeartRateZoneItem] = Field(default_factory=list)
    technique_trends: list[TechniqueTrendItem] = Field(default_factory=list)
    comparison_to_last_month: list[MonthlyComparisonItem] = Field(default_factory=list)
    file_path: Optional[str] = None
    created_at: datetime


class MonthlyReportList(BaseModel):
    reports: list[MonthlyReportResponse]
    total: int


class BandHeartRatePoint(BaseModel):
    timestamp: datetime
    bpm: int
    stroke_rate: Optional[float] = None


class BandDataUploadRequest(BaseModel):
    athlete_id: str
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    data_points: list[BandHeartRatePoint]


class TouchWallLapData(BaseModel):
    lap_number: int
    touch_timestamp: datetime
    distance_m: float
    time_sec: float
    pace: Optional[float] = None


class TouchWallTimerRequest(BaseModel):
    athlete_id: str
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    lane_number: Optional[int] = None
    laps: list[TouchWallLapData]


class CameraMotionFrame(BaseModel):
    timestamp: datetime
    frame_index: Optional[int] = None
    stroke_length_cm: Optional[float] = None
    body_rotation_deg: Optional[float] = None
    elbow_angle_deg: Optional[float] = None
    kick_frequency: Optional[float] = None
    body_position_score: Optional[float] = None


class CameraAnalysisRequest(BaseModel):
    athlete_id: str
    session_id: Optional[str] = None
    camera_id: Optional[str] = None
    video_path: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    frames: list[CameraMotionFrame]


class QualityLabel(str, Enum):
    NORMAL = "normal"
    REPAIRED = "repaired"
    ABNORMAL = "abnormal"


class AnomalySegment(BaseModel):
    source: str
    field: str
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    original_value: Optional[Any] = None
    repaired_value: Optional[Any] = None
    reason: Optional[str] = None
    action: Optional[str] = None


class DataQualityScore(BaseModel):
    completeness: float = 0.0
    consistency: float = 0.0
    reliability: float = 0.0
    overall: float = 0.0
    anomaly_count: int = 0
    warning: bool = False


class DataQualityReport(BaseModel):
    session_id: str
    quality: DataQualityScore
    anomalies: list[AnomalySegment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CoachDataAdjustment(BaseModel):
    session_id: str
    data_source: str
    field: str
    index: int
    original_value: Any
    new_value: Any
    reason: Optional[str] = None


class CoachAdjustmentLog(BaseModel):
    id: PyObjectId = Field(default=None, validation_alias="_id")
    session_id: PyObjectId
    coach_id: PyObjectId
    data_source: str
    field: str
    index: int
    original_value: Any
    new_value: Any
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CoachAdjustmentRequest(BaseModel):
    data_source: str
    field: str
    index: int
    original_value: Any
    new_value: Any
    reason: Optional[str] = None
