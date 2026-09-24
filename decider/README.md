# decider

Mapika's `decider.serve` on CUDA — a trained one-pass decision model behind a
TypeSafe/Jev-compatible API.

The published package already binds `0.0.0.0` and serves the wire format, so
this image supplies the runtime and nothing else. No wrapper, no patch.

```
POST /v1/systemone    TypeSafe/Jev wire format
POST /decide          native format
GET  /v1/models  /health  /stats
```

## Build and run

```sh
docker build -t decider:0.1.0 .
docker volume create decider-hf-cache

docker run -d --name decider --gpus '"device=0"' -p 18081:8080 \
  -v decider-hf-cache:/hf \
  -e DECIDER_MODEL=Mapika/decider-2b \
  decider:0.1.0
```

Weights come from the Hub into `/hf` on first start. Nothing is baked in.

## DECIDER_WARMUP=0 is required, not tuning

At default settings the server captures its whole shape grid before it will
serve, and dies partway through:

```
17 length buckets x 6 batch sizes  ->  ~89 CUDA graphs
each graph arena sized for batch x tokens of attention and DeltaNet buffers
```

```
memory allocation failed ... free: 150,732,800 (143 MiB) of 11.62 GiB
```

This is not a model-size problem. decider-2b is 3.54 GiB of weights and fails
with **11.61 GiB of a genuinely empty card** — the grid is what grows. It is
also not a co-tenancy problem; the failure reproduces with every other service
stopped.

`serve.py` documents the knobs for this:

```
DECIDER_T_BUCKETS  DECIDER_B_BUCKETS  DECIDER_GRAPH_TOKEN_BUDGET (32768)  DECIDER_WARMUP (1)
```

With `DECIDER_WARMUP=0` the grid is skipped, and `serve.py` then calls
`eng.seal()` unconditionally — so the engine never captures later either. Every
request runs **eager**: no graph speedup, but bounded memory and no capture OOM
at runtime. `DECIDER_MAX_BATCH` does *not* bound the grid; that batch list is
hardcoded in the warmup loop.

## Weights

dtype is not configurable — `serve.py` hardcodes bfloat16 on CUDA (float16 on
MPS):

```python
return dev, (torch.float16 if dev.startswith("mps") else torch.bfloat16)
```

So there is **no quantized GPU path**. Q8_0 exists, but as a GGUF for a
different runtime; see below.

| Model | bf16 | Context |
|---|---:|---|
| `Mapika/decider-0.8b` | 1.4 GB | 32k |
| `Mapika/decider-2b` | 3.5 GB | 32k |
| `Mapika/decider-4b` | 8.4 GB | 32k |
| `Mapika/decider-35b-a3b` | 65 GB | 32k |

`DECIDER_FP8` and `DECIDER_COMPILE` stay off: fp8 needs `torch._scaled_mm`
(sm89+, this card is sm86), and torch.compile is inert in a sealed engine.

### The GGUF alternative

[`cosetoenor/decider-2b-GGUF`](https://huggingface.co/cosetoenor/decider-2b-GGUF)
publishes F16 (3.78 GB), **Q8_0 (2.01 GB)** and IQ4_NL (1.24 GB) plus a small C
shim (`code/dz_shim.c`) and a `POST /v1/systemone` server over it.

Use **Q8_0** if you take this path — it keeps 70/71 picks against bf16 with
0.003 median drift. IQ4_NL drops to 59/71 with 0.407 max drift, which is
disqualifying when the probability itself is the output.

Two constraints:

- **The shim is CPU-only.** `dz_load` hardcodes `mp.n_gpu_layers = 0` and passes
  `n_threads` to `llama_context_default_params`, so it never offloads. There is
  no GPU GGUF route here.
- **Its context budget is 8192**, passed literally to `dz_load`, not the model's
  32k.
- **It uses the questions-first layout** (`independent=False`), which upstream
  measures at **0.741 state-first vs 0.707 questions-first** held-out. The
  PyTorch server defaults to plain/state-first, so the GGUF path is the less
  accurate of the two by roughly 3 points.

`dz_shim.c` is also not installed by `pip` — it must be compiled against
`libllama`, and the server imports `decider.prompt` / `decider.systemone` from a
local copy of the upstream repo. Treating it as a deployment is real work, not a
download. This image does not do it.

## Measured on the target machine (RTX 3060 12 GB)

Eager path, `DECIDER_WARMUP=0`, co-resident with `llama-server` (embed + rerank)
and `kev-server`.

| Input | Tokens | Wall |
|---|---:|---:|
| Short ticket, 3 questions | 196 | 119 ms cold, **21.5 ms warm** |
| ~4k chars | 2,751 | 551 ms |
| ~13k chars | 9,051 | 1,604 ms |
| ~26k chars | 18,051 | **3,532 ms** |

Correctness spot-check: a refund clause buried in an 18k-token agreement scored
`noul 0.9818`; a duplicate-charge ticket routed to `billing` at 0.9791–0.9909.

Co-residency is tight — a long state can OOM when free VRAM drops under ~170 MiB.
Short states are fine with all services running; long states need a co-tenant
dropped.

## Configuration

`DECIDER_MODEL`, `DECIDER_MAX_STATE_TOKENS` (32768), `DECIDER_DEVICE` (auto),
`DECIDER_MAX_BATCH` (32), `DECIDER_MAX_WAIT_MS`, `DECIDER_T_BUCKETS`,
`DECIDER_B_BUCKETS`, `DECIDER_WARMUP`, `DECIDER_FP8`, `DECIDER_COMPILE`,
`DECIDER_SCHEMA_CACHE` (costs ~1.5 pts, uses questions-first),
`DECIDER_TEMPERATURE`. Full list in `serve.py`'s module docstring.
