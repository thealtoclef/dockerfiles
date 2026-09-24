# syntax=docker/dockerfile:1.9
#
# decider-server: Mapika's `decider.serve` on CUDA.
#
# The published package already binds 0.0.0.0 and serves the TypeSafe wire
# format, so this only supplies the runtime. Weights are not baked in:
# DECIDER_MODEL is a Hub id or local dir, cached in /hf on first start.

FROM nvidia/cuda:12.6.3-runtime-ubuntu24.04

# decider-ai requires >=3.11; noble ships 3.12.
# gcc + libc6-dev + python3-dev are runtime deps: flash-linear-attention JITs
# DeltaNet kernels through Triton at import time, which needs a C toolchain.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-dev git ca-certificates curl gcc libc6-dev \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/hf \
    HF_HUB_DISABLE_PROGRESS_BARS=1 \
    TOKENIZERS_PARALLELISM=false \
    TRITON_CACHE_DIR=/hf/triton-cache

RUN pip install --upgrade pip \
 && pip install "decider-ai[serve]" \
 && python -c "import torch, decider, fastapi, fla; print('torch', torch.__version__)"

# DECIDER_WARMUP=0: the server otherwise captures its whole shape grid at
# start-up and exhausts the GPU. serve.py seals the engine right after, so it
# then never captures; every request runs eager. Bounded memory, no graph
# speedup.
# DECIDER_COMPILE=0: inert in a sealed engine, which never uses the compiled path.
# DECIDER_FP8=0: fp8 needs torch._scaled_mm, i.e. sm89+; this card is sm86.
ENV DECIDER_WARMUP=0 \
    DECIDER_COMPILE=0 \
    DECIDER_FP8=0 \
    DECIDER_MODEL=Mapika/decider-2b \
    DECIDER_MAX_STATE_TOKENS=32768

EXPOSE 8080

# First start downloads weights into /hf; later starts reuse it.
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=300s \
  CMD curl -fsS http://localhost:8080/health || exit 1

CMD ["uvicorn", "decider.serve:app", "--host", "0.0.0.0", "--port", "8080"]
