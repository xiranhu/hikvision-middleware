"""
adapters.py -- one class per vendor/sensor. This is the ONLY file you
touch to onboard a new sensor. Everything else in the middleware is
generic and does not change.

Each adapter's job: take that vendor's raw payload (however ugly) and
return a list of OccupancyReading or VehicleReading (models.py). That's
the entire contract.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time

from models import OccupancyReading, VehicleReading


def now_ms() -> int:
    return int(time.time() * 1000)


class SensorAdapter(ABC):
    """Base class every sensor adapter implements."""

    # Value written into the standard payload's "SensorType" field.
    sensor_type: str = "Unknown"

    @abstractmethod
    def parse(self, raw: Dict[str, Any]) -> List[Any]:
        """Convert one raw vendor payload into normalized readings."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# TEMPLATE -- copy this class to onboard a new sensor.
# ---------------------------------------------------------------------------

class NewSensorAdapterTemplate(SensorAdapter):
    """
    TEMPLATE. Copy this class, rename it, and fill in:
    1. sensor_type          -- string reported in the output JSON
    2. RAW_EVENT_EXAMPLE    -- a real captured payload, for your own reference
    3. parse()              -- map real field names into a Reading

    Pick ONE of OccupancyReading (presence/absence sensors -> Option 1)
    or VehicleReading (per-object tracking sensors -> Option 2) as your
    return type, matching what this sensor actually reports.
    """
    sensor_type = "TODO"

    # TODO: paste a real captured payload here for reference.
    RAW_EVENT_EXAMPLE: Dict[str, Any] = {
        "TODO": "replace with real sensor output"
    }

    def parse(self, raw: Dict[str, Any]) -> List[VehicleReading]:
        # TODO: replace every raw.get(...) with the real field name.
        sid = str(raw.get("zoneId", "0"))
        ts_ms = raw.get("timestamp_ms", now_ms())

        return [VehicleReading(
            sid=sid,
            vehicle_id=str(raw.get("vehicleId", "unknown")),
            approach_id=str(raw.get("approachId", "1")),
            lane_id=str(raw.get("laneId", "1")),
            dist_to_stopline=float(raw.get("distToStopLine", 0.0)),
            speed=float(raw.get("speed", 0.0)),
            length=float(raw.get("length", 0.0)),
            vehicle_type=str(raw.get("vehicleType", "Small vehicle")),
            timestamp_ms=int(ts_ms),
        )]


# ---------------------------------------------------------------------------
# Generic error/status check -- adapt the field names to whatever your
# sensor's response envelope actually uses (statusCode, ok, success, etc).
# ---------------------------------------------------------------------------

def check_sensor_status(response: Dict[str, Any]) -> Optional[str]:
    """
    Call this on every raw response BEFORE parsing it.
    Return an error message if the call failed, else None.
    TODO: adjust field names/success values to match your sensor's API.
    """
    status_code = response.get("statusCode")
    if status_code is not None and int(status_code) not in (0, 1):
        return f"Sensor error: statusCode={status_code} " \
               f"({response.get('statusString', '')}) " \
               f"detail={response.get('subStatusCode', 'unknown')}"
    return None
