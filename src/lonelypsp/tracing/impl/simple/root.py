from typing import TYPE_CHECKING, Type

from lonelypsp.tracing.impl.simple.config import SimpleTracingConfig
from lonelypsp.tracing.impl.simple.db import SimpleTracingDBSidecar
from lonelypsp.tracing.impl.simple.stateless.root import (
    SimpleStatelessTracingBroadcasterRoot,
    SimpleStatelessTracingSubscriberRoot,
)
from lonelypsp.tracing.root import TracingBroadcasterRoot, TracingSubscriberRoot


class SimpleTracingBroadcasterRoot:
    def __init__(self) -> None:
        self.stateless = SimpleStatelessTracingBroadcasterRoot()


class SimpleTracingSubscriberRoot:
    def __init__(self, db: SimpleTracingDBSidecar, config: SimpleTracingConfig) -> None:
        self.stateless = SimpleStatelessTracingSubscriberRoot(db, config)


if TYPE_CHECKING:
    _: Type[TracingBroadcasterRoot] = SimpleTracingBroadcasterRoot
    __: Type[TracingSubscriberRoot] = SimpleTracingSubscriberRoot
