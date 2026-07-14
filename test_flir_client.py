"""
test_flir_client.py -- a FAKE camera. Spins up a local WebSocket server
that mimics the real FLIR camera's subscribe/event behavior, closely
following the FLIR ITS Public API Manual V1.23 examples, so you can
prove flir_client.py actually works before the real hardware arrives.

HOW TO RUN THE DRY RUN:
    Terminal 1: python3 test_flir_client.py
    Terminal 2: python3 flir_client.py localhost:8765

You should see flir_client.py print the subscription acks, then a
stream of fake Presence events and IndividualDataAI vehicle data, then
the transformed Option 1 / Option 2 JSON reports.
"""

import asyncio
import json

import websockets

FAKE_PRESENCE_EVENTS = [
    {"eventNumber": "1", "messageType": "Event", "state": "Begin",
     "time": "2024-05-01T14:11:00.000+00:00", "type": "Presence", "zoneId": "1"},
    {"eventNumber": "2", "messageType": "Event", "state": "End",
     "time": "2024-05-01T14:11:03.000+00:00", "type": "Presence", "zoneId": "1"},
]

FAKE_VEHICLE_DATA = [
    {"applicationName": "CountingGroup", "class": "Car", "classId": "5",
     "confidence": "9", "dataNumber": "1", "length": "4.5",
     "messageType": "Data", "speed": "42.0",
     "time": "2024-05-01T14:11:01.000+00:00", "trackId": "101",
     "type": "IndividualDataAI", "zoneId": "105"},
    {"applicationName": "CountingGroup", "class": "Truck", "classId": "13",
     "confidence": "8", "dataNumber": "2", "length": "12.0",
     "messageType": "Data", "speed": "35.0",
     "time": "2024-05-01T14:11:02.000+00:00", "trackId": "102",
     "type": "IndividualDataAI", "zoneId": "105"},
]


async def handler(websocket):
    print("Fake camera: client connected")
    async for message in websocket:
        msg = json.loads(message)
        print(f"Fake camera received: {msg}")

        if msg.get("messageType") == "Subscription":
            sub_type = msg["subscription"]["type"]
            await websocket.send(json.dumps({
                "messageType": "Subscription",
                "subscription": {"returnValue": "OK", "type": sub_type},
            }))

            # After acking, start streaming fake data for that subscription type.
            if sub_type == "Event":
                for event in FAKE_PRESENCE_EVENTS:
                    await asyncio.sleep(0.5)
                    await websocket.send(json.dumps(event))
            elif sub_type == "Data":
                for data in FAKE_VEHICLE_DATA:
                    await asyncio.sleep(0.5)
                    await websocket.send(json.dumps(data))


async def main():
    print("Fake FLIR camera listening on ws://localhost:8765/api/subscriptions")
    print("In another terminal, run: python3 flir_client.py localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
