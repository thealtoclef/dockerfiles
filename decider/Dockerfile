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
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Pinned because the model repository was re-released two days before this image
# was written and the checkpoint's own behaviour keys off `version` in
# decider_config.json. Serving is a measured configuration here; an implicit
# upgrade should be a deliberate one.
#
# The extra pulls fastapi, uvicorn, httpx. --system installs into the
# interpreter's own site-packages, where torch, triton and numpy already satisfy
# decider-ai; PEP 668 marks that environment externally managed, hence
# --break-system-packages. A venv would duplicate 3 GB of torch to no benefit.
# --compile-bytecode matches what pip would have done for free. --no-cache leaves
# no download cache, and the tmpfs over /tmp leaves no lock file or staging tree.
RUN --mount=type=tmpfs,target=/tmp \
    uv pip install --no-cache --system --break-system-packages --compile-bytecode "decider-ai[serve]==1.3.0" \
 && python -c "import torch, triton, decider.serve; print('torch', torch.__version__, 'triton', triton.__version__, 'cuda', torch.cuda.is_available())"

# Optional arena reservation at the state cap; see the module docstring. With
# DECIDER_RESERVE unset the app is re-exported unchanged.
COPY reserve.py /app/reserve.py
WORKDIR /app
RUN python -c "import reserve; print('reserve gate:', reserve.RESERVE, 'cap', reserve.CAP)"

# Unconditional: no apt state survives in the runtime image, whether or not the
# steps above installed anything.
RUN rm -rf /var/lib/apt/lists/* /var/cache/apt/*

EXPOSE 8000

ENTRYPOINT ["uvicorn", "reserve:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
