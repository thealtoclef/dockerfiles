"""Reserve the inference arena at the configured state cap before serving.

PyTorch's caching allocator grows on demand and never returns memory, so without
this the process footprint is a function of the longest state it has ever seen
rather than of its configuration: measured 3,779 MiB idle, 4,527 MiB after a
7.9k-token request, and it stays there. That is the opposite of llama.cpp, which
reserves its KV cache for n_ctx at load and never moves afterwards.

Setting DECIDER_RESERVE=1 runs one forward pass at the cap during startup, so the
arena reaches its ceiling immediately and the figure is flat from the first
second. It costs about 1.5 s and holds the ceiling for the life of the process.

Reserving is optional, and on a shared card it is arguably the wrong trade: the
ceiling is reached either way, and the cap is what makes it a ceiling, so leaving
it on demand keeps 750 MiB free until something actually needs it. Turn it on
when you want the number to be flat from startup.

The cap itself is not optional. Without one, a single 32k-token request takes the
process to 6,983 MiB and leaves 103 MiB on the card - see docs/decider-official.md.
"""

import os
from contextlib import asynccontextmanager

import decider.serve as serve
from decider.serve import app

# Rebinding app.router.lifespan_context below must not be what _lifespan calls
# back into, or it re-enters itself.
_serve_lifespan = app.router.lifespan_context

RESERVE = os.environ.get("DECIDER_RESERVE", "0") == "1"
# The row cap is the shape a request can actually reach; the engine pads it to a
# bucket, and reserving the unpadded length would reserve less than a real
# request allocates.
CAP = int(os.environ.get("DECIDER_MAX_ROW_TOKENS", os.environ.get("DECIDER_MAX_STATE_TOKENS", "32768")))


@asynccontextmanager
async def _lifespan(app_):
    # Run the server's own startup first; it is what loads the weights and builds
    # the engine this reservation needs.
    async with _serve_lifespan(app_):
        if RESERVE:
            eng = serve.eng
            if eng is None:
                raise RuntimeError("decider.serve.eng is unset after startup; nothing to reserve")
            shape = eng.pad_len(CAP)
            took = eng.warmup(shapes=[(1, shape)])
            print(f"[reserve] arena reserved at {shape} tokens (cap {CAP}) in {took:.1f}s", flush=True)
        yield


app.router.lifespan_context = _lifespan
