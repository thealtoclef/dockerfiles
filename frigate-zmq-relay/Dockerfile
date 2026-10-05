# Merged relay image: the ZMQ relay plus a local iGPU detector it can fall back
# to, so Frigate keeps detecting when the RTX 3060 workstation is off.
#
# The base must be the garymathews ROCm 7.2.4 image, not the official
# blakeblackshear one: the official 0.18.0-rocm ships ROCm 7.2.3, whose rocBLAS
# has no gfx900 kernels, and this node's Cezanne iGPU (HSA_OVERRIDE_GFX_VERSION
# 9.0.0) aborts MIGraphX with "Illegal seek for GPU arch : gfx900".
#
# The base already ships onnxruntime with MIGraphXExecutionProvider plus numpy,
# opencv-python-headless and pyzmq; only the server and relay code are added.
FROM ghcr.io/garymathews/frigate:latest-rocm-7.2.4

WORKDIR /app

COPY relay.py /app/relay.py
COPY entrypoint.sh /app/entrypoint.sh
COPY detector/ /app/detector/
COPY models/ /app/models/

# The iGPU is reported as gfx900 unless this override is set (docs: AMD does not
# officially support integrated GPUs, this makes ROCm treat it as one it knows).
ENV HSA_OVERRIDE_GFX_VERSION=9.0.0

EXPOSE 5590

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
