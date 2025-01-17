# Tracing

## High Level

This protocol and library allow for and implement distributed tracing intended
for consumption primarily by system administrators, but also is intended to be
useful for the developers of lonelypsp and its respective clients for debugging
and performance analysis.

Since it is intended to produce a useful amount of data for system
administrators, a typical ad-hoc process of adding tracing is not used as the
required documentation and consistency would not be present. Instead, every
possible tracing point is defined clearly, the order is documented, and a
reasonable amount of static analysis is possible to ensure the order of calls is
unambiguously defined.

Since `lonelypsp` is intended to be extremely friendly to hobby projects, it is
quite possible that there is no existing observability infrastructure to plug into.
For this case, an out of the box implementation will store the relevant traces in
SQLite on the subscriber side where it easiest to access and view, and naturally
segments out the performance data to see which subscriber is the bottleneck.

Since `lonelypsp` is intended to be compatible with large projects, it is quite
possible that there is an existing observability infrastructure that must be
used. Thus, the interface is designed to be relatively straightforward to
integrate with OpenTelemetry, and such an implementation would be accepted via
pull request.

## Example

Tracing is best understood by the prototypical example of the stateless
`SUBSCRIBE_EXACT` message. This message is initiated by the subscriber,
so the first trace object is initialized on the subscriber side, it will
receive some synchronous callbacks at relevant points, then will serialize
itself for the wire and be transferred to the broadcaster. It will be
verified via the authorization mechanism (e.g., hmac), then deserialized on
the broadcaster side, receive some synchronous callbacks at relevant points,
then serialize itself for the wire and be transferred back to the subscriber.
It will be verified via the authorization mechanism, then deserialized on
the subscriber side, receive some synchronous callbacks at relevant points,
then the trace object will be destroyed.

It's expected that many of the tracing objects will want to use asyncio, but
they are required to manage pushing to their own queue, especially since it will
often be helpful to have tracing at least moved to a separate thread/event loop,
if not a separate process/event loop. If lonelypsp used the asyncio event loop
for tracing it would either have to implement its own asyncio queue (leading to
pointless inefficiency if the tracing object is then just dumping to another
queue) or have very specific timing/cancellation requirements which would be
error-prone to implement.

### Trace Object Protocol

The trace object protocols have an enormous number of definitions that allow
for the exact control flow to be statically analyzed. For example, for
`SUBSCRIBE_EXACT`, it starts with a protocol like

```python
class StatelessTracingSubscribeExactOnStart(Protocol):
    def on_start(self) -> "StatelessTracingSubscribeExactOnTechniqueDetermined":
        ...

class StatelessTracingSubscribeExactOnTechniqueDetermined(Protocol):
    def on_use_direct(self) -> "StatelessTracingSubscribeExactOnDirectUsed":
        ...

    def on_use_bulk(self) -> "StatelessTracingSubscribeExactOnBulkUsed":
        ...
```

and it continues like that. It's expected that when you implement these protocols
you don't use such long trees, instead, you have a single object that implements
all the related protocols and each of the functions returns `self`. This makes the
control flow explicit and static analysable without actually inducing an excessive
amount of object creation overhead.

Tracing is very implementation aware so it's expected that if using e.g. a rust client
it will have its own tracing implementation that expects to be using a rust server,
with the factorial explosion that implies, but as the protocol becomes more stable and
the implementations more mature, tracing will get less granular (as it will be clear
which points actually matter) and more interoperable.
