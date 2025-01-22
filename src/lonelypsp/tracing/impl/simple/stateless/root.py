from typing import TYPE_CHECKING, Literal, Type

from lonelypsp.tracing.impl.simple.config import SimpleTracingConfig
from lonelypsp.tracing.impl.simple.db import SimpleTracingDBSidecar
from lonelypsp.tracing.impl.simple.stateless.notify import (
    SimpleStatelessTracingNotifyOnReceived,
    SimpleStatelessTracingNotifyStart,
)
from lonelypsp.tracing.stateless.notify import (
    StatelessTracingNotifyOnReceived,
    StatelessTracingNotifyStart,
)
from lonelypsp.tracing.stateless.root import (
    StatelessTracingBroadcasterRoot,
    StatelessTracingSubscriberRoot,
)


class SimpleStatelessTracingSubscriberRoot:
    def __init__(self, db: SimpleTracingDBSidecar, config: SimpleTracingConfig) -> None:
        self.db = db
        self.config = config

    def notify(self, initializer: Literal[None], /) -> StatelessTracingNotifyStart:
        return SimpleStatelessTracingNotifyStart(
            db=self.db,
            config=self.config,
        )


class SimpleStatelessTracingBroadcasterRoot:
    def receive_notify(
        self, initializer: Literal[None], /
    ) -> StatelessTracingNotifyOnReceived:
        return SimpleStatelessTracingNotifyOnReceived()


if TYPE_CHECKING:
    _: Type[StatelessTracingSubscriberRoot[Literal[None]]] = (
        SimpleStatelessTracingSubscriberRoot
    )
    __: Type[StatelessTracingBroadcasterRoot[Literal[None]]] = (
        SimpleStatelessTracingBroadcasterRoot
    )
