#!/usr/bin/env python3
"""Always-on ZMQ relay in front of the remote Frigate detector.

Frigate's `type: zmq` detector re-initialises only once after a request timeout.
If the remote is unreachable at that moment it stays permanently "not ready"
and never retries, so detection does not recover when the workstation returns.

This relay keeps Frigate's endpoint local and always responsive:
  * model requests / model data are forwarded to the workstation when reachable,
    otherwise answered optimistically (the remote persists the model on disk);
  * inference requests are forwarded, otherwise answered with zero detections.

Result: Frigate's detector is always "ready" (init never fails), recording stays
independent, and detection resumes automatically once the workstation returns.
"""

import json
import logging
import os
import time

import zmq

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("zmq-relay")

UPSTREAM = os.environ.get("UPSTREAM_ENDPOINT", "tcp://10.10.88.88:5590")
BIND = os.environ.get("BIND_ENDPOINT", "tcp://*:5590")
INFER_TIMEOUT_MS = int(os.environ.get("INFER_TIMEOUT_MS", "1000"))
MODEL_TIMEOUT_MS = int(os.environ.get("MODEL_TIMEOUT_MS", "5000"))
COOLDOWN_S = float(os.environ.get("COOLDOWN_S", "3"))

ZERO_REPLY = [
    json.dumps({"shape": [20, 6], "dtype": "float32"}).encode("utf-8"),
    b"\x00" * (20 * 6 * 4),
]

ctx = zmq.Context.instance()
_upstream = None
_down_until = 0.0


def _connect():
    global _upstream
    if _upstream is not None:
        _upstream.close(linger=0)
    sock = ctx.socket(zmq.REQ)
    sock.setsockopt(zmq.LINGER, 0)
    sock.connect(UPSTREAM)
    _upstream = sock


def forward(frames, timeout_ms):
    """Forward frames to the remote detector. Returns reply frames or None."""
    global _down_until
    if time.time() < _down_until:
        return None
    try:
        _upstream.setsockopt(zmq.RCVTIMEO, timeout_ms)
        _upstream.setsockopt(zmq.SNDTIMEO, timeout_ms)
        _upstream.send_multipart(frames)
        return _upstream.recv_multipart()
    except zmq.Again:
        log.warning("upstream timeout after %dms; cooling down %.1fs", timeout_ms, COOLDOWN_S)
    except zmq.ZMQError as exc:
        log.warning("upstream ZMQ error: %s; cooling down %.1fs", exc, COOLDOWN_S)
    _down_until = time.time() + COOLDOWN_S
    _connect()
    return None


def _json(payload):
    return [json.dumps(payload).encode("utf-8")]


def main():
    _connect()
    frontend = ctx.socket(zmq.REP)
    frontend.setsockopt(zmq.LINGER, 0)
    frontend.bind(BIND)
    log.info("relay bound %s -> %s", BIND, UPSTREAM)

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
                reply = _json({
                    "model_available": True,
                    "model_loaded": True,
                    "model_name": header.get("model_name"),
                    "message": "relay: upstream unavailable, assuming model persists",
                })
            frontend.send_multipart(reply)

        elif "model_data" in header:
            reply = forward(frames, MODEL_TIMEOUT_MS)
            if reply is None:
                reply = _json({
                    "model_saved": True,
                    "model_loaded": True,
                    "model_name": header.get("model_name"),
                })
            frontend.send_multipart(reply)

        else:
            reply = forward(frames, INFER_TIMEOUT_MS)
            frontend.send_multipart(reply if reply is not None else ZERO_REPLY)


if __name__ == "__main__":
    main()
