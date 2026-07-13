"""
buffer.py -- keeps the rolling window of samples per zone. Generic;
does not change per sensor.
"""

from collections import defaultdict, deque
from typing import Any, Deque, Dict, List


class SampleBuffer:
    """Keeps up to `report_rate` most recent readings per zone."""

    def __init__(self, report_rate: int):
        self.report_rate = report_rate
        self._buffers: Dict[str, Deque[Any]] = defaultdict(
            lambda: deque(maxlen=report_rate)
        )

    def add(self, sid: str, reading: Any) -> None:
        self._buffers[sid].append(reading)

    def snapshot(self) -> Dict[str, List[Any]]:
        return {sid: list(dq) for sid, dq in self._buffers.items()}
