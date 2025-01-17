from typing import Generic, Protocol, TypeVar
from lonelypsp.tracing.stateless.notify import (
    StatelessTracingNotifyStart,
    StatelessTracingNotifyOnReceived,
)

InitializerT = TypeVar("InitializerT")


class StatelessTracingSubscriberRoot(Generic[InitializerT], Protocol):
    """Contains a way to produce the start of each stateless operation
    from the subscribers perspective. Many of these protocols may have
    overlapping names, so this cannot just absorb all the protocols
    """

    def notify(self, initializer: InitializerT, /) -> StatelessTracingNotifyStart:
        """About to start the process of sending a NOTIFY message to the broadcaster
        and receiving a RESPOND_NOTIFY
        """


class StatelessTracingBroadcasterRoot(Generic[InitializerT], Protocol):
    """Contains a way to produce the start of each stateless operation
    from the broadcasters perspective.  Many of these protocols may have
    overlapping names, so this cannot just absorb all the protocols
    """

    def receive_notify(
        self, initializer: InitializerT, /
    ) -> StatelessTracingNotifyOnReceived:
        """About to start the process of receiving a NOTIFY message from the subscriber
        and sending a RESPOND_NOTIFY
        """
