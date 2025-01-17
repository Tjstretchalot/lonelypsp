from typing import Generic, Protocol, TypeVar

from lonelypsp.tracing.stateless.root import (
    StatelessTracingBroadcasterRoot,
    StatelessTracingSubscriberRoot,
)

InitializerTcontra = TypeVar("InitializerTcontra", contravariant=True)
"""When using OpenTelemetry style spans, the type that allows the caller to
embed the span within some other operation. We never pass this in a keyword
argument (and enforce this with the protocol) so you can use a better name
for it
"""


class TracingBroadcasterRoot(Generic[InitializerTcontra], Protocol):
    """
    Can produce stateless or stateful roots from the broadcaster
    perspective for tracing. To avoid excessive garbage collection
    it is not intended that this produces new objects on each
    access.

    Doesn't absorb the two protocols as it is convenient for them to
    have overlapping names
    """

    @property
    def stateless(self) -> "StatelessTracingBroadcasterRoot[InitializerTcontra]":
        """Returns the stateless root"""

    # @property
    # def stateful(self) -> "StatefulTracingBroadcasterRoot[InitializerTcontra]":
    #     """Produces the stateful root"""


class TracingSubscriberRoot(Generic[InitializerTcontra], Protocol):
    """
    Can produce stateless or stateful roots from the subscriber perspective for
    tracing. To avoid excessive garbage collection it is not intended that this
    produces new objects on each access.

    Doesn't absorb the two protocols as it is convenient for them to have
    overlapping names
    """

    @property
    def stateless(self) -> "StatelessTracingSubscriberRoot[InitializerTcontra]":
        """Returns the stateless root"""

    # @property
    # def stateful(self) -> "StatefulTracingSubscriberRoot[InitializerTcontra]":
    #     """Produces the stateful root"""
