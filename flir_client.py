"""
flir_client.py -- connects OUT to the FLIR TrafiCam's WebSocket API and
subscribes to live Events and Data.

IMPORTANT STRUCTURAL DIFFERENCE from server.py: FLIR's camera does NOT
push data to a URL you host (unlike the earlier ISAPI push assumption).
Instead, the camera runs its own WebSocket endpoint, and YOUR code
connects to IT, like a client connecting to a chat server. server.py
(the HTTP listener) is not used for this device.

Confirmed against FLIR ITS Public API Manual V1.23, section 9
(Subscriptions).

HOW TO USE (once you have the real camera):
    python3 flir_client.py <camera_ip>

TO DRY-RUN WITHOUT A REAL CAMERA:
    See test_flir_client.py -- it spins up a fake local WebSocket
    server that mimics the camera's subscribe/event responses, so you
    can prove this code works before the hardware arrives.
"""

import asyncio
import json
import sys

import websockets

from adapters import FlirPresenceEventAdapter, FlirIndividualDataAdapter, check_sensor_status
from pipeline import SensorPipeline

SUBSCRIBE_EVENTS = {
    "messageType": "Subscription",
    "subscription": {"type": "Event", "action": "Subscribe"},
}
SUBSCRIBE_DATA = {
    "messageType": "Subscription",
    "subscription": {"type": "Data", "action": "Subscribe"},
}


async def run_client(camera_ip: str) -> None:
    uri = f"ws://{camera_ip}/api/subscriptions"
    print(f"Connecting to {uri} ...")

    # One pipeline per Option, both fed from the same WebSocket connection.
    presence_pipeline = SensorPipeline(
        adapter=FlirPresenceEventAdapter(), report_rate=4, sampling_rate=1, kind="occupancy"
    )
    vehicle_pipeline = SensorPipeline(
        adapter=FlirIndividualDataAdapter(), report_rate=4, sampling_rate=1, kind="vehicle"
    )

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(SUBSCRIBE_EVENTS))
        print(f"-> sent: {SUBSCRIBE_EVENTS}")
        await ws.send(json.dumps(SUBSCRIBE_DATA))
        print(f"-> sent: {SUBSCRIBE_DATA}")

        print("Subscribed. Listening for live events/data (Ctrl+C to stop)...")
        async for message in ws:
            raw = json.loads(message)

            err = check_sensor_status(raw)
            if err:
                print(f"[error] {err}")
                continue

            msg_type = raw.get("messageType")
            if msg_type == "Subscription":
                print(f"<- subscription ack: {raw['subscription']}")
                continue
            elif msg_type == "Event":
                presence_pipeline.ingest(raw)
            elif msg_type == "Data":
                vehicle_pipeline.ingest(raw)
            else:
                continue  # KeepAlive acks etc, not sensor data

            for name, pipeline in (("Presence", presence_pipeline), ("Vehicle", vehicle_pipeline)):
                payload = pipeline.maybe_report()
                if payload:
                    print(f"[{name} report] {payload}")
                    # TODO: dispatch_to_platform(payload) -- see main.py


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 flir_client.py <camera_ip>")
        sys.exit(1)
    asyncio.run(run_client(sys.argv[1]))
