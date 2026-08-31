# syntax=docker/dockerfile:1.9
#
# OpenViking with self-hosted local hybrid (dense+sparse) embedding running
# in-process on CPU (onnxruntime), instead of vendor APIs. Cheap to build:
# starts from the prebuilt official image — no Rust/npm/Python rebuild — and
# adds the runtime deps, the generated source patch (openviking-local-onnx.
# patch; git apply fails the build if the base image no longer matches it,
# by design), and the fp32 ONNX model baked into /models. See README.md for
# patch provenance and ov.conf.
ARG OPENVIKING_BASE=ghcr.io/volcengine/openviking:latest
FROM ${OPENVIKING_BASE}

# 1. Runtime deps. The base venv is uv-managed and has no pip, so drive it
# with uv. onnxruntime + numpy are small; transformers provides only the
# tokenizer (no torch needed — the code uses return_tensors="np").
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN uv pip install --python /app/.venv/bin/python --no-cache \
    "onnxruntime>=1.17" \
    "numpy>=1.24" \
    "transformers"

# 2. Apply the generated feature patch into the installed (non-editable)
# site-packages tree. The base image ships git (no `patch` utility), and
# git apply is atomic: it FAILS the build, loudly, when the base image no
# longer matches the code the patch was generated against — never silently
# succeed with a stale or half-applied feature.
ARG SITE_PACKAGES=/app/.venv/lib/python3.13/site-packages
COPY openviking-local-onnx.patch /tmp/openviking-local-onnx.patch
RUN cd "${SITE_PACKAGES}" && git apply /tmp/openviking-local-onnx.patch \
 && rm /tmp/openviking-local-onnx.patch

# 3. Bake the fp32 ONNX model (a-ivanovitch export; the only one exposing
# dense+sparse+colbert outputs). ~2.2 GB.
# huggingface_hub is a BUILD-only need (snapshot_download); `uv run --with`
# uses an ephemeral env so it never ships in the image.
RUN mkdir -p /models && uv run --no-cache --with "huggingface_hub" python - <<'PYEOF'
from huggingface_hub import snapshot_download

snapshot_download("a-ivanovitch/bge-m3-onnx", local_dir="/models/bge-m3-onnx")
PYEOF
