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

# The `laya` executable from the ggmlc v0.9.2 release. v0.9.2 is the release
# whose only change is "systemone: add support for handling Kev models in laya
# executable" (#28), so it is the first version that can serve Kev at all.
#
# The asset name says laya because that is the binary's name, but it is not
# Laya-specific: it is the System One runtime, and it dispatches on the
# `ggmlc.decision` metadata inside each GGUF. ggmlc's other release binaries
# (ggmlc-run, tab_completion, timesfm) are a generic tensor runner and unrelated
# model families; ggmlc-run in particular has no System One logic.
ARG GGMLC_VERSION=v0.9.2
ARG LAYA_ASSET=laya-linux-x86_64-cuda-sm86.tar.gz
ARG LAYA_BINARY_SHA256=334e09603c38e6e746cb00eeefb662b8b0ac8ea2f621cba08dad850fbcf52efb

RUN mkdir -p /app \
 && curl -fsSL -o /tmp/laya.tgz \
      "https://github.com/monatis/ggmlc/releases/download/${GGMLC_VERSION}/${LAYA_ASSET}" \
 && echo "${LAYA_BINARY_SHA256}  /tmp/laya.tgz" | sha256sum -c - \
 && tar -xzf /tmp/laya.tgz -C /tmp \
 && install -m 0755 /tmp/laya /app/laya \
 && rm -rf /tmp/laya /tmp/laya.tgz \
 && ldd /app/laya | grep -E 'libcudart|libcublas|libgomp'

EXPOSE 8080

ENTRYPOINT ["/app/laya"]
CMD ["serve", "--models-dir", "/models", "--port", "8080", "--device", "cuda", "--cuda-graph"]
