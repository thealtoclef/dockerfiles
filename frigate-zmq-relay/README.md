# frigate-zmq-relay

One container that serves Frigate's `type: zmq` detector endpoint — a front-end
relay plus a GPU detector it can fall back to, so an offline remote GPU no
longer means missed detections.

```
Frigate (REQ) ──> relay (REP) ──┬──> tcp://<gpu-host>:5590     remote GPU, ONNX Runtime + CUDA
                                │     (primary, from UPSTREAM_ENDPOINTS)
                                └──> tcp://127.0.0.1:5591     in this container: AMD iGPU,
                                      (fallback)              ONNX Runtime + MIGraphX
```

Both detectors speak the same protocol — an NCHW float32 tensor in, a `[20, 6]`
float32 detection array out — so Frigate cannot tell which one answered. ZMQ is
only the transport; the compute behind it is CUDA on one side and MIGraphX on
the other.

The image name stays `frigate-zmq-relay`: from Frigate's side this is still one
always-answering relay endpoint, and a renamed image would be a new GHCR package
(private by default, needing a pull secret).

## Why it exists

Frigate's zmq client re-initialises only once after a request timeout. If the
upstream is unreachable at that moment it stays permanently "not ready" and
never retries, so detection does not recover when the remote GPU returns. This
endpoint therefore has to answer *always*:

- the relay prefers the first **healthy** upstream, in `UPSTREAM_ENDPOINTS` order;
- an upstream that fails is parked with exponential backoff (3s..60s) and
  re-admitted only by a background probe, so a real detection request never pays
  a dead upstream's timeout before falling through;
- every unparked upstream is probed, healthy ones included, so a fallback that
  is never exercised while the primary answers is still reported honestly;
- with no upstream reachable, model requests are answered optimistically (both
  detectors persist the model on disk) and inference with zero detections.

`relay_upstream_up{upstream=...}` / `relay_upstream_failures_total{upstream=...}`
on `:9090/metrics` report which upstream is serving. The label is deliberately
`upstream` and not `endpoint`: Prometheus overwrites a scraped `endpoint` label
with the Service port name.

## Configuration

| Env | Default | Meaning |
|---|---|---|
| `UPSTREAM_ENDPOINTS` | *(required)* | Comma-separated detectors, in priority order |
| `BIND_ENDPOINT` | `tcp://*:5590` | Endpoint Frigate connects to |
| `INFER_TIMEOUT_MS` | `800` | Per-upstream inference timeout; must stay well under Frigate's `request_timeout_ms` |
| `MODEL_TIMEOUT_MS` | `5000` | Per-upstream model handshake timeout |
| `COOLDOWN_S` / `MAX_COOLDOWN_S` | `3` / `60` | Backoff bounds for a parked upstream |
| `PROBE_INTERVAL_S` | `30` | Health-probe cadence |
| `METRICS_PORT` | `9090` | Prometheus text endpoint |

## Layout

```
Dockerfile          base = ghcr.io/garymathews/frigate:latest-rocm-7.2.4 (public)
entrypoint.sh       the relay is foreground, the local detector a supervised child
relay.py            failover, backoff, probe loop, metrics
detector/           ZMQ detector server (provider-agnostic; CUDA or MIGraphX)
models/             yolov9-s-320.onnx, served to the remote detector on request
version.txt         bump to publish via CI
```

## Base image

Must be the `garymathews` ROCm 7.2.4 image, not the official `blakeblackshear`
one: the official `0.18.0-rocm` ships ROCm 7.2.3, whose rocBLAS has no gfx900
kernels, so MIGraphX aborts on this Cezanne iGPU with
`Illegal seek for GPU arch : gfx900`. The base also provides onnxruntime (with
MIGraphXExecutionProvider), numpy, opencv-python-headless and pyzmq.

MIGraphX compiles the model on every container start (~4 min). During that
window the local upstream fails probes and parks; the primary serves, and the
fallback is adopted by a later probe.

## The detector server

`detector/` is provider-agnostic: the same server runs on the remote GPU with
`CUDAExecutionProvider` and in this container with
`MIGraphXExecutionProvider`, selected by `--providers`. `entrypoint.sh` passes
the endpoint with its `tcp://` scheme, which the server binds verbatim.

## Deployed by

A Kubernetes Deployment + Service (GitOps), one pod per cluster. The primary
endpoint is whatever the GitOps manifest puts first in `UPSTREAM_ENDPOINTS`; the
fallback is the detector in the same container.
