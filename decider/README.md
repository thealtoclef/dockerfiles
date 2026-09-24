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

## Oversized states are silently truncated by default

`prompt.py` cuts the state with a plain slice:

```python
ctx_ids = tok.encode("Context:\n" + example.context, add_special_tokens=False)[:max_ctx_tokens]
```

and the admission check is looser than that cap:

```
DECIDER_MAX_STATE_TOKENS = 32768   the state is truncated here
DECIDER_MAX_ROW_TOKENS   = 36864   rows are admitted up to here
                           ^ 4096-token gap = the tail is dropped, 200 returned
```

Measured on this card, decisive clause at the **end** of the state:

| Input | Reported tokens | noul |
|---|---:|---:|
| 31,260 | 31,260 | 0.9818 |
| 32,798 | 32,798 | **0.2398** |
| 32,798 (bigger input) | 32,798 | **0.2398** |

Every oversized input reports the identical 32,798 — the tail never reaches the
model. With the clause at the **start** of the same oversized state the answer
stays 0.9863, which is what proves it is truncation and not a long-context
weakness. It returns HTTP 200 either way.

`DECIDER_MAX_ROW_TOKENS=32768` closes the gap so an oversized row is rejected:

```
413 {"detail":"too many tokens: one row has 32798 tokens, the limit is 32768 per row"}
```

A state within the cap still works. The cost is that a state within a few
tokens of the cap is rejected rather than truncated, which is the safe side of
that trade.

## CUDA graphs are not worth it on this card

`DECIDER_WARMUP=1` with a reduced grid does work:

```
DECIDER_T_BUCKETS=64,128,256,512,1024  DECIDER_B_BUCKETS=1,2,4,8
-> 20 graphs captured in 21s, served normally
```

But the measured gain does not justify the memory:

| Question count | Eager | With graphs |
|---:|---:|---:|
| 1 | 21.2 ms | 19.1 ms |
| 4 | 50.2 ms | 48.2 ms |
| 8 | 91.9 ms | 89.0 ms |

~10%, because on a 3060 the forward compute dominates kernel launch overhead.
The pools cost ~820 MiB and pushed free VRAM from 3.3 GiB to 121 MiB, at which
point every state above ~3k tokens failed with OOM — including states that the
eager path had just served. Graphs trade long-state capability for a 2 ms
saving on short ones, so the image leaves `DECIDER_WARMUP=0`.

The author's "3.2 ms with CUDA graphs" is measured on a B300, where launch
overhead does dominate.

Long-state latency is therefore inherent, not a configuration problem: the
eager path is compute-bound, ~3.5 s at 18k tokens on this GPU. Short states are
the fast path at ~20 ms.

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
