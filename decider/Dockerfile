# syntax=docker/dockerfile:1.9
#
# Official decider server: a state and typed questions go in, calibrated
# probabilities come out, one forward pass, no decoding. This runs Mapika's
# PyTorch implementation from the decider-ai package, which is the supported
# path for these checkpoints. The ggmlc conversion is not used: the runtime's
# byte-level tokenizer branch mis-segments accented Latin script and the forward
# pass disagrees with the reference independently of that.
#
# The base is the torch release this checkpoint was verified against, so the
# CUDA, cuDNN and triton stack come as a consistent set instead of being
# assembled from a bare CUDA image.

FROM pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# The extra pulls fastapi, uvicorn, httpx. --break-system-packages is deliberate:
# this image exists only to run this server, and torch, triton and numpy already
# live in the system site-packages at versions that satisfy it. A venv without
# --system-site-packages would duplicate 3 GB of torch to no benefit.
RUN pip install --no-cache-dir --break-system-packages "decider-ai[serve]" \
 && python -c "import torch, triton, decider.serve; print('torch', torch.__version__, 'triton', triton.__version__, 'cuda', torch.cuda.is_available())"

EXPOSE 8000

ENTRYPOINT ["uvicorn", "decider.serve:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
