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

class FlirPresenceEventAdapter(SensorAdapter):
    """
    CONFIRMED against FLIR ITS Public API Manual V1.23, section 6
    (Events) and Appendix A (Presence event type).

    Real event message:
    {
        "eventNumber": "2",
        "messageType": "Event",
        "state": "Begin",       # or "End"
        "time": "2015-06-05T11:37:59.230+02:00",
        "type": "Presence",
        "zoneId": "2"
    }

    Begin = a vehicle entered the zone (occupied).
    End   = the zone cleared (unoccupied).
    """
    sensor_type = "FLIR-TrafiCam-Presence"

    def parse(self, raw: Dict[str, Any]) -> List[OccupancyReading]:
        if raw.get("type") != "Presence":
            return []  # not a presence event, ignore (this device sends many event types)
        sid = str(raw.get("zoneId", "0"))
        occupancy = "1" if raw.get("state") == "Begin" else "0"
        ts_ms = self._to_epoch_ms(raw.get("time"))
        return [OccupancyReading(sid=sid, occupancy=occupancy, timestamp_ms=ts_ms)]

    @staticmethod
    def _to_epoch_ms(iso_ts: Optional[str]) -> int:
        if not iso_ts:
            return now_ms()
        import datetime
        return int(datetime.datetime.fromisoformat(iso_ts).timestamp() * 1000)


class FlirIndividualDataAdapter(SensorAdapter):
    """
    CONFIRMED against FLIR ITS Public API Manual V1.23, Appendix C
    ("Individual Data AI"). Sent each time the AI detects an object
    passing through a zone.

    Real data message:
    {
        "applicationName": "CountingGroup",
        "class": "Truck",
        "classId": "5",
        "confidence": "9",
        "dataNumber": "132164",
        "frameCounter": "5202334",
        "length": "15.0",
        "messageType": "Data",
        "speed": "43.2",
        "time": "2023-09-27T09:07:31.125+00:00",
        "trackId": "2",
        "type": "IndividualDataAI",
        "zoneId": "105"
    }

    NOTE: FLIR does not report distance-to-stopline directly in this
    message. dist_to_stopline is set to 0.0 as a placeholder. If you
    need a real value, use Track Data (worldY coordinate, see the DG's
    Appendix D) combined with a configured stop-line position -- ask
    if you want that built once you confirm it's actually needed.

    NOTE: FLIR's zoneId is a single zone identifier -- there's no
    separate ApproachId/LaneId split in this schema, so both are set
    to the same zoneId value here. Adjust if your zone configuration
    encodes lane/approach info in the zone numbering scheme.
    """
    sensor_type = "FLIR-TrafiCam-IndividualDataAI"

    def parse(self, raw: Dict[str, Any]) -> List[VehicleReading]:
        if raw.get("type") != "IndividualDataAI":
            return []
        sid = str(raw.get("zoneId", raw.get("trajectoryId", "0")))
        ts_ms = self._to_epoch_ms(raw.get("time"))
        return [VehicleReading(
            sid=sid,
            vehicle_id=str(raw.get("trackId", "unknown")),
            approach_id=sid,
            lane_id=sid,
            dist_to_stopline=0.0,  # not available in this message -- see note above
            speed=float(raw.get("speed", 0.0)),
            length=float(raw.get("length", 0.0)),
            vehicle_type=str(raw.get("class", "Small vehicle")),
            timestamp_ms=ts_ms,
        )]

    @staticmethod
    def _to_epoch_ms(iso_ts: Optional[str]) -> int:
        if not iso_ts:
            return now_ms()
        import datetime
        return int(datetime.datetime.fromisoformat(iso_ts).timestamp() * 1000)


# ---------------------------------------------------------------------------
# Generic error/status check -- adapt the field names to whatever your
# sensor's response envelope actually uses (statusCode, ok, success, etc).
# ---------------------------------------------------------------------------

def check_sensor_status(response: Dict[str, Any]) -> Optional[str]:
    """
    CONFIRMED against FLIR ITS Public API Manual V1.23 ("Errors" section).
    FLIR's error responses (both REST and WebSocket) look like:
        {"messageType": "Error", "returnInfo": "...", "returnValue": "Error"}
    HTTP status codes: 200 OK, 400 Bad Request, 403 Forbidden,
    404 Not Found, 409 Conflict, 500 Internal Server Error.

    Subscription/keepalive/forceEvent responses instead nest their
    result, e.g. {"subscription": {"returnValue": "OK", ...}} -- those
    are handled separately, not by this function (this only checks for
    the generic Error message shape).
    """
    if response.get("messageType") == "Error":
        return f"FLIR API error: {response.get('returnInfo', 'no detail provided')}"
    return None
