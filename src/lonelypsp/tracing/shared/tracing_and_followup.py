from typing import Generic, TypeVar

from lonelypsp.compat import fast_dataclass

T = TypeVar("T")


@fast_dataclass
class TracingAndFollowup(Generic[T]):
    tracing: bytes
    """the tracing data to transfer"""

    followup: T
    """the object that will pick up tracing (on this side) after the response"""
