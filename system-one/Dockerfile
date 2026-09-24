# syntax=docker/dockerfile:1.9
#
# ggmlc System One decision engine: choice / score / noul in one forward pass.
#
# One binary serves every ggmlc-compiled checkpoint — the Laya encoder families
# and the Kev decoder families alike. The model's tokenizer, sequence program,
# and postprocess live inside the GGUF under the `ggmlc.decision` key, so the
# runner does not switch on model family; which models it can serve is decided
# at GGUF compile time, not here.
#
# Model artifacts are supplied through a read-only /models mount.

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# libgomp1 is a hard runtime dependency of the binary: without it the loader
# fails with "libgomp.so.1: cannot open shared object file".
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# Official ggmlc CUDA runtime; sm86 targets the RTX 3060 / compute capability 8.6.
ARG GGMLC_VERSION=v0.9.2
ARG GGMLC_ASSET=laya-linux-x86_64-cuda-sm86.tar.gz
ARG GGMLC_BINARY_SHA256=334e09603c38e6e746cb00eeefb662b8b0ac8ea2f621cba08dad850fbcf52efb

RUN mkdir -p /app \
 && curl -fsSL -o /tmp/laya.tgz \
      "https://github.com/monatis/ggmlc/releases/download/${GGMLC_VERSION}/${GGMLC_ASSET}" \
 && echo "${GGMLC_BINARY_SHA256}  /tmp/laya.tgz" | sha256sum -c - \
 && tar -xzf /tmp/laya.tgz -C /tmp \
 && install -m 0755 /tmp/laya /app/laya \
 && rm -rf /tmp/laya /tmp/laya.tgz \
 && ldd /app/laya | grep -E 'libcudart|libcublas|libgomp'

EXPOSE 8080

ENTRYPOINT ["/app/laya"]
CMD ["serve", "--models-dir", "/models", "--port", "8080", "--device", "cuda", "--cuda-graph"]
