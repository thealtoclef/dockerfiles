#!/usr/bin/env python3
"""Always-on ZMQ relay in front of one or more remote Frigate detectors.

Frigate's `type: zmq` detector re-initialises only once after a request timeout.
If the upstream is unreachable at that moment it stays permanently "not ready"
and never retries, so detection does not recover when the upstream returns.

This relay keeps Frigate's endpoint local and always responsive:

  * requests are forwarded to the first reachable upstream, primary first;
  * an upstream that fails is parked for a backoff window (COOLDOWN_S, doubling
    up to MAX_COOLDOWN_S) and retried by a later request, so a returning primary
    is picked up again automatically;
  * when no upstream is reachable, model requests are answered optimistically
    (both detectors persist the model on disk) and inference with zero
    detections.

Result: Frigate's detector is always "ready" (init never fails), recording stays
independent of the workstations, and detection resumes automatically once any
upstream returns.

Per-upstream health is exported on METRICS_PORT (/metrics), so a scrape can tell
"remote detector down, fallback serving" apart from "nothing is serving".
"""

import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import zmq

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("zmq-relay")

UPSTREAMS = [
    endpoint.strip()
    for endpoint in os.environ.get(
        "UPSTREAM_ENDPOINTS", "tcp://10.10.88.88:5590"
    ).split(",")
    if endpoint.strip()
]
BIND = os.environ.get("BIND_ENDPOINT", "tcp://*:5590")
INFER_TIMEOUT_MS = int(os.environ.get("INFER_TIMEOUT_MS", "1000"))
MODEL_TIMEOUT_MS = int(os.environ.get("MODEL_TIMEOUT_MS", "5000"))
COOLDOWN_S = float(os.environ.get("COOLDOWN_S", "3"))
MAX_COOLDOWN_S = float(os.environ.get("MAX_COOLDOWN_S", "60"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9090"))

ZERO_REPLY = [
    json.dumps({"shape": [20, 6], "dtype": "float32"}).encode("utf-8"),
    b"\x00" * (20 * 6 * 4),
]

ctx = zmq.Context.instance()
_upstreams = []


class Upstream:
    """REQ socket to one detector, parked for a backoff window after a failure."""

    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.failures = 0
        self.parked_until = 0.0
        self._sock = None
        self._connect()

    def _connect(self):
        if self._sock is not None:
            self._sock.close(linger=0)
        sock = ctx.socket(zmq.REQ)
        sock.setsockopt(zmq.LINGER, 0)
        sock.connect(self.endpoint)
        self._sock = sock

    @property
    def parked(self):
        return time.monotonic() < self.parked_until

    def request(self, frames, timeout_ms):
        """Return reply frames, or None and park this upstream on failure."""
        try:
            self._sock.setsockopt(zmq.RCVTIMEO, timeout_ms)
            self._sock.setsockopt(zmq.SNDTIMEO, timeout_ms)
            self._sock.send_multipart(frames)
            reply = self._sock.recv_multipart()
        except zmq.Again:
            self._fail("no reply within %dms" % timeout_ms)
            return None
        except zmq.ZMQError as exc:
            self._fail("zmq error: %s" % exc)
            return None

        if self.failures:
            log.info(
                "upstream %s recovered after %d failed attempt(s)",
                self.endpoint,
                self.failures,
            )
        self.failures = 0
        self.parked_until = 0.0
        return reply

    def _fail(self, reason):
        self.failures += 1
        backoff = min(COOLDOWN_S * 2 ** (self.failures - 1), MAX_COOLDOWN_S)
        self.parked_until = time.monotonic() + backoff
        log.warning(
            "upstream %s unavailable (%s); retry in %.0fs", self.endpoint, reason, backoff
        )
        # A REQ socket cannot be reused once a request timed out.
        self._connect()


def forward(frames, timeout_ms):
    """Forward frames to the first upstream that is not parked. None if nobody answers."""
    for upstream in _upstreams:
        if upstream.parked:
            continue
        reply = upstream.request(frames, timeout_ms)
        if reply is not None:
            return reply
    return None


def _json(payload):
    return [json.dumps(payload).encode("utf-8")]


def render_metrics():
    """Prometheus text exposition of per-upstream health."""
    lines = [
        "# HELP relay_upstream_up 1 while the upstream answered the last request, 0 while it is parked after a failure.",
        "# TYPE relay_upstream_up gauge",
    ]
    for upstream in _upstreams:
        state = 0 if upstream.failures else 1
        lines.append(f'relay_upstream_up{{endpoint="{upstream.endpoint}"}} {state}')
    lines += [
        "# HELP relay_upstream_failures_total Failed requests since startup; 0 means the upstream is healthy.",
        "# TYPE relay_upstream_failures_total gauge",
    ]
    for upstream in _upstreams:
        lines.append(
            f'relay_upstream_failures_total{{endpoint="{upstream.endpoint}"}} {upstream.failures}'
        )
    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404)
            return
        body = render_metrics().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def start_metrics_server():
    if not METRICS_PORT:
        return
    server = HTTPServer(("", METRICS_PORT), MetricsHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("metrics on :%d/metrics", METRICS_PORT)


def main():
    global _upstreams
    _upstreams = [Upstream(endpoint) for endpoint in UPSTREAMS]
    start_metrics_server()

    frontend = ctx.socket(zmq.REP)
    frontend.setsockopt(zmq.LINGER, 0)
    frontend.bind(BIND)
    log.info("relay bound %s -> %s", BIND, " , ".join(UPSTREAMS))

    while True:
        frames = frontend.recv_multipart()
        header = {}
        try:
            header = json.loads(frames[0].decode("utf-8"))
        except Exception:
            pass

        if "model_request" in header:
            reply = forward(frames, MODEL_TIMEOUT_MS)
            if reply is None:
                reply = _json(
                    {
                        "model_available": True,
                        "model_loaded": True,
                        "model_name": header.get("model_name"),
                        "message": "relay: no upstream reachable, assuming model persists",
                    }
                )
            frontend.send_multipart(reply)

        elif "model_data" in header:
            reply = forward(frames, MODEL_TIMEOUT_MS)
            if reply is None:
                reply = _json(
                    {
                        "model_saved": True,
                        "model_loaded": True,
                        "model_name": header.get("model_name"),
                    }
                )
            frontend.send_multipart(reply)

        else:
            reply = forward(frames, INFER_TIMEOUT_MS)
            frontend.send_multipart(reply if reply is not None else ZERO_REPLY)


if __name__ == "__main__":
    main()
