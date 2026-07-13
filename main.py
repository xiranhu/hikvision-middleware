"""
main.py -- entrypoint. Builds one SensorPipeline per registered sensor
and shows the ingest -> report cycle. Wire `ingest()` to wherever your
raw sensor data actually arrives (HTTP webhook handler, polling loop,
message queue consumer, etc) and `maybe_report()` to a scheduler tick
(e.g. called every 250ms, or on a timer thread).
"""

from typing import Dict

from config import SENSOR_REGISTRY
from pipeline import SensorPipeline


def build_pipelines() -> Dict[str, SensorPipeline]:
    pipelines = {}
    for sensor_id, (adapter_cls, report_rate, sampling_rate, kind) in SENSOR_REGISTRY.items():
        pipelines[sensor_id] = SensorPipeline(
            adapter=adapter_cls(),
            report_rate=report_rate,
            sampling_rate=sampling_rate,
            kind=kind,
        )
    return pipelines


def handle_incoming_event(pipelines: Dict[str, SensorPipeline], sensor_id: str, raw: dict) -> None:
    """Call this from wherever raw sensor data lands (webhook, poller, etc)."""
    pipeline = pipelines.get(sensor_id)
    if pipeline is None:
        print(f"Unknown sensor_id: {sensor_id}")
        return
    err = pipeline.ingest(raw)
    if err:
        print(f"[{sensor_id}] {err}")


def dispatch_to_platform(payload_json: str) -> None:
    """
    TODO: replace with your actual platform call, e.g.:
        requests.post(PLATFORM_URL, data=payload_json,
                       headers={"Content-Type": "application/json"})
    """
    print(payload_json)


if __name__ == "__main__":
    pipelines = build_pipelines()

    # --- Demo: simulate one raw event arriving, then force a report ---
    demo_raw_event = {
        "statusCode": 1,
        "zoneId": "1",
        "vehicleId": "42",
        "approachId": "1",
        "laneId": "1",
        "distToStopLine": 3.5,
        "speed": 40.0,
        "length": 4.5,
        "vehicleType": "Small vehicle",
        "timestamp_ms": 1234567890000,
    }
    handle_incoming_event(pipelines, "example-sensor-1", demo_raw_event)

    for sensor_id, pipeline in pipelines.items():
        payload = pipeline.maybe_report(now=0)  # now=0 forces emission in this demo
        if payload:
            print(f"--- {sensor_id} ---")
            dispatch_to_platform(payload)
