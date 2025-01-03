"""Protocol describing something that has the semantics of asyncio.Queue"""

import asyncio
from typing import TYPE_CHECKING, Generic, Protocol, Type, TypeVar

T = TypeVar("T")


class AsyncQueueLike(Generic[T], Protocol):
    def qsize(self) -> int:
        """length of the queue; guaranteed to be accurate, as async is cooperative"""

    # maxsize purposely not allowed since asyncio.Queue uses 0 to mean unbounded,
    # but we don't want to promsie that

    def empty(self) -> bool:
        """True if the queue is empty, False otherwise"""

    def full(self) -> bool:
        """True if the queue is full, False otherwise"""

    async def put(self, item: T) -> None:
        """Put an item into the queue"""

    def put_nowait(self, item: T) -> None:
        """Put an item into the queue without blocking, raising
        asyncio.QueueFull if the queue is full
        """

    async def get(self) -> T:
        """Get an item from the queue, waiting until one is available
        if empty
        """

    def get_nowait(self) -> T:
        """Get an item from the queue without blocking, raising
        asyncio.QueueEmpty if the queue is empty
        """

    # we don't care about the task unfinished/finished stuff usually
    # since that can be accomplished is semantically simpler using events
    # and locks explicitly


if TYPE_CHECKING:
    _: Type[AsyncQueueLike] = asyncio.Queue
