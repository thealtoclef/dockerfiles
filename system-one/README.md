# system-one

The [ggmlc](https://github.com/monatis/ggmlc) System One decision engine: typed
`choice` / `score` / `noul` questions scored in one forward pass, no generated
tokens, no Python. A standalone C++/CUDA binary.

**One binary serves every ggmlc-compiled checkpoint.** A model's tokenizer,
sequence program, and postprocess are baked into the GGUF under the
`ggmlc.decision` key, so the runner does not switch on model family — what it
can serve is decided at GGUF compile time, not by this image. That is how the
same `laya` executable serves both the Laya encoder families and the Kev
decoder families.

## Build and run

```sh
docker build -t system-one:0.9.2 .
```

```sh
docker run -d --name system-one --gpus '"device=0"' -p 18081:8080 \
  -v /path/to/models:/models:ro \
  system-one:0.9.2
```

`--models-dir` scans the mount, reads each GGUF's `ggmlc.decision` metadata, and
registers every model it finds. `GET /health` reports the catalog:

```
{"status":"ok","device":"cuda:0","families":["kev-0.8b"],"family":"auto","model":"kev-0.8b"}
```

Routes: `POST /v1/systemone` (TypeSafe wire format), `GET /v1/models`,
`GET /health`, plus a Decision Studio web UI at `/`. Set `LAYA_API_KEY` or
`TYPESAFE_API_KEY` to require bearer auth.

`libgomp1` is a hard runtime dependency — without it the binary fails to load
with `libgomp.so.1: cannot open shared object file`.

## Kev via ggmlc

[`mys/kev-0.8b-GGUF`](https://huggingface.co/mys/kev-0.8b-GGUF),
[`mys/kev-4b-GGUF`](https://huggingface.co/mys/kev-4b-GGUF) and `kev-0.5b` are
ggmlc-compiled Kev, each in F16 / Q8_0 / UD_Q4_K_M. They are **not** llama.cpp
GGUFs and will fail to load there.

Verified loading `kev_0.8b_q8_0.gguf`:

```
[laya] catalog kev-0.8b <- /models/kev_0.8b_q8_0.gguf  [ggmlc.decision]
[laya] ready  kind=kev  recipe=gguf  max_len=2048 max_opts=16 max_batch=8 dynamic=b,s
temperature: [2.40605, 2.40605, 2.40605]  (baked into weights)
```

The temperature matches what `jaredpalmer/kev-0.8b` reports natively (2.41), so
the LoRA merge and export are faithful.

### Context: 2048, and it truncates silently

| Artifact | Context |
|---|---:|
| `kev_0.5b` / `kev_0.8b` / `kev_4b` GGUF | **2048** |
| Laya english | 512 |
| Laya multilingual / typed-decisions | 1024 |

Kev's Python runtime serves 8192, but **the ggmlc GGUF is compiled at 2048** —
the README states it plainly: *"`max_len` is 512 for English, 1024 for the other
Laya families, 2048 for Kev."* The cap is a property of the compiled artifact,
so it is not something this image can raise.

Oversized states are **truncated without an error**. Measured:

| Input | Reported tokens | noul |
|---|---:|---:|
| ~1400 tok | 2048 | 0.9619 |
| ~2100 tok | 2048 | **0.9619** |
| ~4600 tok | 2048 | **0.9619** |

Every oversized input reports exactly 2048 and returns the identical answer, so
the tail never reaches the model and the caller sees HTTP 200. Keep states under
2048 tokens, and treat a decision made near that ceiling as suspect.

### Measured latency (RTX 3060, Kev-0.8B Q8_0)

| Questions | Wall |
|---:|---:|
| 1 | 17.9 ms |
| 2 | 30.1 ms |
| 4 | 56.0 ms |
| 8 | 109.1 ms |

## Quants

| File | 0.8b | 4b |
|---|---:|---:|
| F16 | ~1.46 GB | ~8.05 GB |
| **Q8_0** | **790 MB** | **4.29 GB** |
| UD_Q4_K_M | ~914 MB | ~4.02 GB |

Q8_0 is the default choice: uniform, and the largest quant that fits this card
comfortably. UD_Q4_K_M keeps the embedding at F16 and sensitive projections at
Q8_0 with the rest at Q4_0, which makes it *larger* than Q8_0 on the 0.8b
because of the 248k vocabulary.
