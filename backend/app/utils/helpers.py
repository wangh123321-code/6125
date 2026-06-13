from datetime import date, timedelta
from typing import Any, Dict, List

from bson import ObjectId


def object_id_to_str(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {k: object_id_to_str(v) for k, v in value.items()}
    if isinstance(value, list):
        return [object_id_to_str(item) for item in value]
    return value


def generate_monthly_dates(year: int, month: int) -> List[date]:
    dates = []
    start_date = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    current = start_date
    while current < next_month:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def calculate_heart_rate_zone(bpm: float, max_hr: int = 200) -> str:
    ratio = bpm / max_hr
    if ratio < 0.6:
        return "热身"
    elif ratio < 0.75:
        return "有氧"
    elif ratio < 0.9:
        return "无氧"
    else:
        return "极限"


def calculate_pace(seconds: float, distance_m: float) -> str:
    if distance_m <= 0 or seconds <= 0:
        return "0'00\"/100m"
    pace_seconds_per_100m = (seconds / distance_m) * 100
    minutes = int(pace_seconds_per_100m // 60)
    secs = int(pace_seconds_per_100m % 60)
    return f"{minutes}'{secs:02d}\"/100m"


def align_timestamps(*data_streams: Dict[float, float]) -> List[Dict[float, float]]:
    if not data_streams:
        return []

    all_timestamps = set()
    for stream in data_streams:
        all_timestamps.update(stream.keys())
    sorted_timestamps = sorted(all_timestamps)

    aligned_streams = []
    for stream in data_streams:
        if not stream:
            aligned_streams.append({t: 0.0 for t in sorted_timestamps})
            continue

        stream_ts = sorted(stream.keys())
        aligned = {}
        for t in sorted_timestamps:
            if t in stream:
                aligned[t] = stream[t]
                continue

            left = None
            right = None
            for st in stream_ts:
                if st < t:
                    left = st
                if st > t and right is None:
                    right = st
                    break

            if left is not None and right is not None:
                ratio = (t - left) / (right - left)
                aligned[t] = stream[left] + ratio * (stream[right] - stream[left])
            elif left is not None:
                aligned[t] = stream[left]
            elif right is not None:
                aligned[t] = stream[right]
            else:
                aligned[t] = 0.0

        aligned_streams.append(aligned)

    return aligned_streams
