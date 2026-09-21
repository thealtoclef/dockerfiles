# syntax=docker/dockerfile:1.9
#
# Laya System One decision server: choice / score / noul.
# The runtime and model are baked into the image; no host model mount is required.
# Laya GGUFs use the ggmlc architecture and are not llama.cpp models.

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ARG LAYA_VERSION=v0.9.0
ARG LAYA_ASSET=laya-linux-x86_64-cuda-sm86.tar.gz
ARG LAYA_BINARY_SHA256=09da6089a23fef640c6800da06e6d9cb093ec131f2194e86d5522eaae72487e1

ARG LAYA_MODEL_URL=https://huggingface.co/mys/laya-multilingual-GGUF/resolve/main/laya_multilingual_q8_0.gguf
ARG LAYA_MODEL_SHA256=757c1a4b1f0f41824113dde76d6cd06b0881d37b796103a338de77f9f9b935c3

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# Official GGMLC CUDA runtime; sm86 targets the RTX 3060 / compute capability 8.6.
RUN mkdir -p /app \
 && curl -fsSL -o /tmp/laya.tgz \
      "https://github.com/monatis/ggmlc/releases/download/${LAYA_VERSION}/${LAYA_ASSET}" \
 && echo "${LAYA_BINARY_SHA256}  /tmp/laya.tgz" | sha256sum -c - \
 && tar -xzf /tmp/laya.tgz -C /tmp \
 && install -m 0755 /tmp/laya /app/laya \
 && rm -rf /tmp/laya /tmp/laya.tgz \
 && ldd /app/laya | grep -E 'libcudart|libcublas|libgomp'

# Pin the model artifact in the image and verify its exact content.
RUN mkdir -p /app/models \
 && curl -fsSL -o /app/models/laya_multilingual_q8_0.gguf "${LAYA_MODEL_URL}" \
 && echo "${LAYA_MODEL_SHA256}  /app/models/laya_multilingual_q8_0.gguf" | sha256sum -c - \
 && chmod 0444 /app/models/laya_multilingual_q8_0.gguf

EXPOSE 8080
ENTRYPOINT ["/app/laya"]
CMD ["serve", "/app/models/laya_multilingual_q8_0.gguf", "--port", "8080", "--device", "cuda", "--cuda-graph"]
