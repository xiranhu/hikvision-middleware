"""
pipeline.py -- wires adapter + buffer + builder together for one sensor.
Generic; does not change per sensor. What changes per sensor lives in
config.py (registry.py in a larger project).
"""

import time
from typing import Any, Dict, Optional

from adapters import SensorAdapter, check_sensor_status
from buffer import SampleBuffer
from builders import build_option1_payload, build_option2_payload


class SensorPipeline:
    def __init__(
        self,
        adapter: SensorAdapter,
        report_rate: int = 4,
        sampling_rate: int = 1,
        kind: str = "occupancy",   # "occupancy" -> Option 1, "vehicle" -> Option 2
    ):
        assert kind in ("occupancy", "vehicle")
        self.adapter = adapter
        self.report_rate = report_rate
        self.sampling_rate = sampling_rate
        self.kind = kind
        self.buffer = SampleBuffer(report_rate=report_rate)
        self._last_report_time = float("-inf")

    def ingest(self, raw: Dict[str, Any]) -> Optional[str]:
        """
        Call every time new raw data arrives from the sensor (should
        happen >= report_rate times per second). Returns an error string
        and skips ingestion if the sensor's own response indicates a
        failure; otherwise returns None.
        """
        err = check_sensor_status(raw)
        if err:
            return err
        for reading in self.adapter.parse(raw):
            self.buffer.add(reading.sid, reading)
        return None

    def maybe_report(self, now: Optional[float] = None) -> Optional[str]:
        """Call on a scheduler tick. Emits standard JSON every
        `sampling_rate` seconds, else returns None."""
        import json
        now = now if now is not None else time.time()
        if now - self._last_report_time < self.sampling_rate:
            return None
        self._last_report_time = now

        snapshot = self.buffer.snapshot()
        builder = build_option1_payload if self.kind == "occupancy" else build_option2_payload
        payload = builder(snapshot, self.report_rate, self.sampling_rate, self.adapter.sensor_type)
        return json.dumps(payload)
