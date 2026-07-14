"""
server.py -- a minimal HTTP listener the camera can actually push events to.

Uses only Python's built-in http.server -- no pip installs needed.
This is deliberately bare-bones; swap in Flask/FastAPI later if you want
nicer routing, but this works today with zero dependencies.

HOW TO USE:
1. Run: python3 server.py
   It listens on http://0.0.0.0:8000/events
2. On your camera's admin web page, find the event notification / HTTP
   listening host settings (usually under Configuration > Network >
   Advanced Settings > Notification, or similar in ISAPI-based UIs).
3. Set the destination to your computer's IP address, port 8000, path /events.
   (Camera and computer must be on the same network for this to work --
   check with your supervisor/IT if the camera is on a separate VLAN.)
4. Trigger something in front of the camera -- you should see it print
   in this terminal.

TO TEST WITHOUT A REAL CAMERA (dry run):
    curl -X POST http://localhost:8000/events \\
         -H "Content-Type: application/json" \\
         -d '{"statusCode":1,"zoneId":"1","vehicleId":"42","approachId":"1",
              "laneId":"1","distToStopLine":3.5,"speed":40.0,"length":4.5,
              "vehicleType":"Small vehicle","timestamp_ms":1234567890000}'

If you don't know the sensor_id the camera will send, this demo defaults
everything to "example-sensor-1" (see ROUTE_ALL_TO below) -- once you know
how the real camera identifies itself (channelID? deviceID? IP?), update
route_sensor_id() to read that from the payload instead.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from config import SENSOR_REGISTRY
from main import build_pipelines, handle_incoming_event, dispatch_to_platform

# TODO: while you only have one sensor registered, everything routes here.
# Once you have multiple real sensors, replace route_sensor_id() below to
# pull the real ID out of the payload (e.g. raw.get("channelID")).
ROUTE_ALL_TO = next(iter(SENSOR_REGISTRY.keys()))


def route_sensor_id(raw: dict) -> str:
    # TODO: once you know the real field the camera uses to identify
    # itself, use it here, e.g.:
    #   return str(raw.get("channelID", ROUTE_ALL_TO))
    return ROUTE_ALL_TO


pipelines = build_pipelines()


class EventHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/events":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            raw = json.loads(body)
        except json.JSONDecodeError:
            print(f"Non-JSON body received: {body[:200]!r}")
            self.send_response(400)
            self.end_headers()
            return

        sensor_id = route_sensor_id(raw)
        print(f"Received event for '{sensor_id}': {raw}")
        handle_incoming_event(pipelines, sensor_id, raw)

        pipeline = pipelines.get(sensor_id)
        if pipeline:
            payload = pipeline.maybe_report()
            if payload:
                dispatch_to_platform(payload)

        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # silence default request logging; we print our own above


if __name__ == "__main__":
    port = 8000
    print(f"Listening for camera events on http://0.0.0.0:{port}/events")
    print("Try the curl command in this file's docstring to test without a real camera.")
    HTTPServer(("0.0.0.0", port), EventHandler).serve_forever()
