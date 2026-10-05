# frigate-zmq-relay

One container that serves Frigate's `type: zmq` detector endpoint — a front-end
relay plus a GPU detector it can fall back to, so an offline workstation no
longer means missed detections.

```
Frigate (REQ) ──> relay (REP) ──┬──> tcp://10.10.88.88:5590   itx: RTX 3060, ONNX Runtime + CUDA
                                │     (primary)
                                └──> tcp://127.0.0.1:5591     in this container: AMD iGPU,
                                      (fallback)              ONNX Runtime + MIGraphX
```

The name is kept deliberately: from Frigate's side this is a relay in front of
detectors, and a renamed image would be a new GHCR package (private by default,
needing a pull secret). Both detectors speak the same protocol — an NCHW
float32 tensor in, a `[20, 6]` float32 detection array out — so Frigate cannot
tell which one answered. ZMQ is only the transport; the compute behind it is
CUDA on one side and MIGraphX on the other.

## Why it exists

Frigate's zmq client re-initialises only once after a request timeout. If the
upstream is unreachable at that moment it stays permanently "not ready" and
never retries, so detection does not recover when the workstation returns. This
endpoint therefore has to answer *always*:

- the relay prefers the first **healthy** upstream, workstation first;
- an upstream that fails is parked with exponential backoff (3s..60s) and
  re-admitted only by a background probe, so a real detection request never pays
  a dead upstream's timeout before falling through;
- with no upstream reachable, model requests are answered optimistically (both
  detectors persist the model on disk) and inference with zero detections.

`relay_upstream_up{upstream=...}` / `relay_upstream_failures_total{upstream=...}`
on `:9090/metrics` report which upstream is serving.

## Layout

```
Dockerfile          base = ghcr.io/garymathews/frigate:latest-rocm-7.2.4 (public)
entrypoint.sh       the relay is foreground, the local detector a supervised child
relay.py            failover, backoff, probe loop, metrics
detector/           ZMQ detector server (provider-agnostic; see upstream below)
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
window the local upstream fails probes and parks; the workstation serves, and
the fallback is adopted by a later probe.

## Deployed by

`apps/frigate/relay.yaml` in the homelab repo (Deployment + Service). The same
server runs standalone on the workstation, built from the sibling
`~/repos/frigate-detector` repo with CUDA instead of MIGraphX.
