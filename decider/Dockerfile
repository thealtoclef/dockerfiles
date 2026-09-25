# syntax=docker/dockerfile:1.9

FROM pytorch/pytorch:2.14.0-cuda12.6-cudnn9-runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Pinned: the checkpoint's behaviour keys off `version` in its decider_config.json.
# --system installs beside the base image's torch, triton and numpy; a venv would
# duplicate 3 GB of torch.
RUN --mount=type=tmpfs,target=/tmp \
    uv pip install --no-cache --system --break-system-packages --compile-bytecode "decider-ai[serve]==1.3.0" \
 && python -c "import decider.serve, torch; assert torch.version.cuda"

EXPOSE 8000

ENTRYPOINT ["uvicorn", "decider.serve:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
