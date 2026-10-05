#!/bin/bash
# One-image supervisor: the local detector is a child, the relay is the
# foreground process Frigate depends on.
#
# The relay never depends on the child being up: it parks an upstream that fails
# and re-probes it, so the several minutes MIGraphX takes to compile the model at
# startup only mean the RTX 3060 serves until the local detector answers.
#
# The detector is restarted if it exits, so a crash cannot silently leave the
# fallback dead until the next pod restart.
set -u

LOCAL_ENDPOINT="${LOCAL_DETECTOR_ENDPOINT:-tcp://127.0.0.1:5591}"
LOCAL_PROVIDERS="${LOCAL_DETECTOR_PROVIDERS:-MIGraphXExecutionProvider CPUExecutionProvider}"
LOCAL_MODEL="${LOCAL_DETECTOR_MODEL:-/app/models/yolov9-s-320.onnx}"

python3 -u /app/relay.py &
relay_pid=$!

(
    while kill -0 "$relay_pid" 2>/dev/null; do
        # The endpoint keeps its tcp:// scheme: the server binds what it is given.
        python3 -u /app/detector/zmq_onnx_client.py \
            --endpoint "$LOCAL_ENDPOINT" \
            --providers $LOCAL_PROVIDERS \
            --model "$LOCAL_MODEL"
        sleep 5
    done
) &
detector_pid=$!

trap 'kill -TERM "$detector_pid" "$relay_pid" 2>/dev/null || true' TERM INT

# The relay exiting is what ends the container; the detector follows it.
wait "$relay_pid" || true
kill -TERM "$detector_pid" 2>/dev/null || true
