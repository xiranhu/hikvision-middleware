"""
config.py -- the sensor registry. This is the second (and last) file you
touch to onboard a new sensor -- register it here after writing its
adapter in adapters.py.

To add a sensor:
1. Write its adapter class in adapters.py.
2. Add one entry below.
Nothing else in the middleware needs to change.
"""

from adapters import NewSensorAdapterTemplate  # replace with your real adapters

SENSOR_REGISTRY = {
    # sensor_id: (adapter_class, report_rate, sampling_rate, kind)
    "example-sensor-1": (NewSensorAdapterTemplate, 4, 1, "vehicle"),
    # "junction-42-loop":  (LoopAdapter, 4, 1, "occupancy"),
    # "junction-42-radar": (RadarAdapter, 4, 1, "vehicle"),
}
