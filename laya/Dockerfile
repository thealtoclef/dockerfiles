# syntax=docker/dockerfile:1.9
#
# ggmlc System One runtime: choice / score / noul in one forward pass.
# Serves any System One ggmlc-compiled GGUF via the `laya` binary.

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# libgomp1 is a hard dependency: the binary fails to load without it.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates libgomp1 \
 && rm -rf /var/lib/apt/lists/*

ARG LAYA_VERSION=v0.9.2
ARG LAYA_ASSET=laya-linux-x86_64-cuda-sm86.tar.gz
ARG LAYA_SHA256=334e09603c38e6e746cb00eeefb662b8b0ac8ea2f621cba08dad850fbcf52efb

RUN mkdir -p /app \
 && curl -fsSL -o /tmp/laya.tgz \
      "https://github.com/monatis/ggmlc/releases/download/${LAYA_VERSION}/${LAYA_ASSET}" \
 && echo "${LAYA_SHA256}  /tmp/laya.tgz" | sha256sum -c - \
 && tar -xzf /tmp/laya.tgz -C /tmp \
 && install -m 0755 /tmp/laya /app/laya \
 && rm -rf /tmp/laya /tmp/laya.tgz

EXPOSE 8080

ENTRYPOINT ["/app/laya"]
CMD ["serve", "--models-dir", "/models", "--port", "8080", "--device", "cuda"]
