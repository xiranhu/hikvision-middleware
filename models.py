"""
models.py -- normalized internal readings.

Every adapter, regardless of vendor, must produce one of these two types.
This is the contract that decouples "whatever the sensor sends" from
"whatever the platform needs" -- add a new sensor by writing an adapter
that emits these, nothing downstream has to change.
"""

from dataclasses import dataclass


@dataclass
class OccupancyReading:
    """One sample for one zone from a presence/absence-style sensor."""
    sid: str
    occupancy: str          # "0" or "1"
    timestamp_ms: int


@dataclass
class VehicleReading:
    """One vehicle observation for one zone from an object-tracking sensor."""
    sid: str
    vehicle_id: str
    approach_id: str
    lane_id: str
    dist_to_stopline: float
    speed: float
    length: float
    vehicle_type: str
    timestamp_ms: int
