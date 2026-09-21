# syntax=docker/dockerfile:1.9
#
# Laya System One decision runtime: choice / score / noul.
# Model artifacts are supplied through a read-only /models mount.
# Laya GGUFs use the ggmlc architecture and are not llama.cpp models.

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ARG LAYA_VERSION=v0.9.0
ARG LAYA_ASSET=laya-linux-x86_64-cuda-sm86.tar.gz
ARG LAYA_BINARY_SHA256=09da6089a23fef640c6800da06e6d9cb093ec131f2194e86d5522eaae72487e1


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


EXPOSE 8080
ENTRYPOINT ["/app/laya"]
CMD ["serve", "--models-dir", "/models", "--port", "8080", "--device", "cuda", "--cuda-graph"]
