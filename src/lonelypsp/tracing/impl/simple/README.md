# Simple Standalone Tracing

This implements distributed tracing stored subscriber-side, with each subscriber
only storing traces that it was involved in.

This is intended to be used when there isn't a central tracing system available
like OpenTelemetry, e.g., in hobby projects. It has minimal overhead while also
providing lots of useful information.

To avoid slowing down the event loop, interacting with sqlite is moved to a
different thread, where memory is shared instead of copied. In GIL environments
this does impose some overhead, but sqlite3 implementations release the GIL
almost immediately so its impact should be extremely minimal, and the cost of
copying in multiprocessing would more than offset the cost of the GIL.

This does not allow pluggable storage backends in order to allow for more
performance optimizations

## Viewing

For convenience of viewing this includes a frontend exposed as a fastapi
APIRouter which can be hosted with something like:

```python
from fastapi import FastAPI
import lonelypsp.tracing.impl.simple.frontend.router as frontend_router

frontend_router.DB_PATH = 'tracing.db'

app = FastAPI()
app.include_router(router, prefix='/stats')  # will put the file at /stats/index.html
app.router.redirect_slashes = False
```

```bash
uvicorn myapp:app --port 8000
```

Which will aggregate the data and provide an explanation of how to interpret it.
Everything is served synchronously in a single file, so snapshotting is as easy
as just downloading the file. In order to avoid any dependencies this frontend
is a bit of a mess to produce, but it is intended that it is relatively easy to
read the generated file.

### Things Included

(V2)

Notify

There were XXX notifications to X broadcasters, taking XXXms (25% XXXms, 75% XXXms, 99% XXXms) to transmit XXXbytes (25% XXXbytes, 75% XXXbytes, 99% XXXbytes) of meaningful data.

Average trace:

```
0  ms-XXXms: THING 1  (25% XXXms, 75% XXXms, 99% XXXms) (in 100% of traces)
XXXms-XXXms: THING 2  (25% XXXms, 75% XXXms, 99% XXXms) (in 75% of traces)
XXXms-XXXms: THING 3  (25% XXXms, 75% XXXms, 99% XXXms) (in 100% of traces)
```

(V1)

Mostly a todo list at the moment

- [ ] since...
  - [ ] ...a specific time
  - [ ] ...the beginning of time
  - [ ] ...penultimate midnight
  - [ ] ...24 hours ago
  - [ ] ...penultimate top of the hour
  - [ ] ...1 hour ago
  - [ ] ...penultimate top of the minute
  - [ ] ...1 minute ago
- [ ] ...ending...
  - [ ] ...a specific time
  - [ ] ...now
  - [ ] ...the most recent midnight
  - [ ] ...top of the hour
  - [ ] ...top of the minute
- [ ] ...filtered by...
  - [ ] ...broadcaster
  - [ ] ...topic
  - [ ] ...topic matches glob (or glob exactly matches)
- [ ] ...number of...
  - [ ] ...stateless...
    - [ ] ...notify...
      - [ ] ...total
      - [ ] ...by number of subscribers
      - [ ] ...bytes total (of meaningful raw data)
      - [ ] ...by length log-scale up to 2^64 (so below 1 byte, below 2, below 4, etc)
    - [ ] ...subscribe exact...
      - [ ] ...total
    - [ ] ...subscribe glob...
      - [ ] ...total
    - [ ] ...unsubscribe exact...
      - [ ] ...total
    - [ ] ...unsubscribe glob...
      - [ ] ...total
    - [ ] ...set subscriptions...
      - [ ] ...total
    - [ ] ...receive
      - [ ] ...total
      - [ ] ...bytes total (of meaningful raw data)
    - [ ] ...missed
      - [ ] ...total
  - [ ] ...stateful...
    - todo
- [ ] ...time p0, p25, p50, p75, p95, p99, p99.9, p100 OR
- [ ] time since most recent...
  - [ ] ...stateless...
    - [ ] ...notify...
      - [ ] ...overall
      - [ ] ...by number of subscribers
    - [ ] ...subscribe exact...
      - [ ] ...overall
    - [ ] ...subscribe glob
      - [ ] ...overall
    - [ ] ...unsubscribe exact
      - [ ] ...overall
    - [ ] ...unsubscribe glob
      - [ ] ...overall
    - [ ] set subscriptions
      - [ ] ...overall
    - [ ] ...receive...
      - [ ] ...overall
  - [ ] ...stateful...
    - todo
- [ ] ...size bytes meaningful data p0, p25, p50, p75, p95, p99, p99.9, p100...
  - [ ] ...stateless...
    - [ ] ...notify...
      - [ ] ...overall
    - [ ] ...receive...
      - [ ] ...overall
  - [ ] ...stateful...
    - todo
