# openviking (local-onnx)

Custom OpenViking image: official image + self-hosted local ONNX models —
hybrid (dense+sparse) embedding **and** cross-encoder reranker
(BGE-M3 / bge-reranker-v2-m3, onnxruntime CPU). No Rust/npm/Python rebuild:
the heavy lifting is already compiled inside `ghcr.io/volcengine/openviking`.

## Where the code lives

The feature is implemented **in-tree** in the OpenViking repo — that repo is
the single source of truth. The patch here is **generated**, never
hand-edited. Run its generator from an OpenViking clone that has the feature
branch checked out:

```sh
# from the OpenViking repo root
scripts/maintenance/generate-onnx-local-patch.sh \
  -o <path-to-this-repo>/openviking/openviking-local-onnx.patch
```

The patch is gitignored in the OpenViking repo (build artifact) but committed
here, so the image build is self-contained. If `git apply` fails during a
build, upstream's image moved past the patch's base commit — rebase the
feature branch, regenerate. It fails loudly on purpose: no silent
stale-feature builds (that was the flaw of the file-overlay approach).

## Build

```sh
docker build -t <registry>/openviking:<tag> .
```

Bakes both fp32 ONNX models (~4.5 GB) into `/models`:

| Role | HF repo | Path in image |
|---|---|---|
| Embedding (dense+sparse+colbert) | `a-ivanovitch/bge-m3-onnx` | `/models/bge-m3-onnx` |
| Reranker (single relevance logit) | `a-ivanovitch/bge-reranker-v2-m3-onnx` | `/models/bge-reranker-v2-m3-onnx` |

fp32 only — the authors ship no int8 (it measurably degrades retrieval/rank
quality; see the HF READMEs).

## Runtime config

Point `ov.conf` at the baked models:

```yaml
embedding:
  hybrid:
    provider: local
    model: bge-m3-onnx
    dimension: 1024
    model_path: /models/bge-m3-onnx
rerank:
  provider: local
  model: bge-reranker-v2-m3-onnx
  model_path: /models/bge-reranker-v2-m3-onnx
```

## Endgame

Once the feature merges upstream and ships in an official image, this
Dockerfile's role shrinks to just baking `/models` (drop the patch step, or
drop this Dockerfile entirely and mount models into the official image).

## Caveats

- Base defaults to `:latest`; the patch is generated against a specific base
  commit. Pin `OPENVIKING_BASE` (e.g. `ghcr.io/volcengine/openviking:v0.4.9`)
  for reproducible builds.
- The base venv is uv-managed (no pip) — deps install via `uv pip`.
