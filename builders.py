"""
builders.py -- assembles the platform's standard JSON (Option 1 / Option 2).
Generic; does not change per sensor.
"""

import time
from typing import Any, Dict, List, Optional

from models import OccupancyReading, VehicleReading


def _now_ms() -> int:
    return int(time.time() * 1000)


def build_option1_payload(
    zone_readings: Dict[str, List[OccupancyReading]],
    report_rate: int,
    sampling_rate: int,
    sensor_type: str,
    timestamp_ms: Optional[int] = None,
) -> Dict[str, Any]:
    ids = []
    for sid, readings in zone_readings.items():
        if not readings:
            continue
        ids.append({"SId": sid, "Vehicles": [{"Occupancy": readings[-1].occupancy}]})

    return {
        "Ids": ids,
        "ReportRate": str(report_rate),
        "SamplingRate": str(sampling_rate),
        "SensorType": sensor_type,
        "Timestamp": str(timestamp_ms if timestamp_ms is not None else _now_ms()),
    }


def build_option2_payload(
    zone_readings: Dict[str, List[VehicleReading]],
    report_rate: int,
    sampling_rate: int,
    sensor_type: str,
    timestamp_ms: Optional[int] = None,
) -> Dict[str, Any]:
    ids = []
    for sid, readings in zone_readings.items():
        vehicles = [{
            "VehicleId": r.vehicle_id,
            "ApproachId": r.approach_id,
            "LaneId": r.lane_id,
            "DistToStopLine": str(r.dist_to_stopline),
            "Speed": str(r.speed),
            "Length": str(r.length),
            "VehicleType": r.vehicle_type,
        } for r in readings]
        ids.append({"SId": sid, "Vehicles": vehicles})

    return {
        "Ids": ids,
        "ReportRate": str(report_rate),
        "SamplingRate": str(sampling_rate),
        "SensorType": sensor_type,
        "Timestamp": str(timestamp_ms if timestamp_ms is not None else _now_ms()),
    }
