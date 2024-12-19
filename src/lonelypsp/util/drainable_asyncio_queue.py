import asyncio
from types import TracebackType
from typing import TYPE_CHECKING, List, Optional, Tuple, Type, TypeVar, Generic

from lonelypsp.util.async_queue_like import AsyncQueueLike
from lonelypsp.util.bounded_deque import BoundedDeque


T = TypeVar("T")


class QueueDrained(Exception):
    """The exception raised when a drained queue is attempted to be accessed"""


class DrainableAsyncioQueue(Generic[T]):
    """Satisfies AsyncioQueueLike[T] but adds the following functionality:

    - max size of 0 means that the queue is always full instead of an unbounded
      queue. a value of None is now also allowed and means an unbounded queue

    - adds optional maximum number of pending get() tasks when the queue is empty

    - adds optional maximum number of pending put() tasks when the queue is full

    - drain() method which empties the queue and raises a QueueDrained exception
      for any future get() or put() calls

    - can be used as an asynchronous context manager, which calls drain() when exiting
    """

    def __init__(
        self,
        /,
        *,
        max_size: Optional[int] = None,
        max_getters: Optional[int] = None,
        max_putters: Optional[int] = None,
    ) -> None:
        self._items: BoundedDeque[T] = BoundedDeque(maxlen=max_size)
        self._getters: BoundedDeque[asyncio.Future[T]] = BoundedDeque(
            maxlen=max_getters
        )
        self._putters: BoundedDeque[Tuple[asyncio.Future[None], T]] = BoundedDeque(
            maxlen=max_putters
        )
        # after draining _items will have maxlen 0, but we raise a different
        # error
        self._drained = False

    async def __aenter__(self) -> "DrainableAsyncioQueue[T]":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.drain()

    def _on_put_one(self) -> bool:
        """Internal function to implement _on_put and _on_get; alerts the next
        getter if there is one and returns True, otherwise returns False

        Note that if there is a getter then we may now have space for another
        putter
        """
        if not self._getters:
            return False

        getter = self._getters.popleft()
        item = self._items.popleft()
        getter.set_result(item)
        return True

    def _on_get_one(self) -> bool:
        """Internal function to implement _on_put and _on_get; alerts the next
        putter if there is one and returns True, otherwise returns False

        Note that if there is a putter then we may now have space for another
        getter
        """
        if not self._putters:
            return False

        putter = self._putters.popleft()
        putter[0].set_result(None)
        self._items.append(putter[1])
        return True

    def _on_put(self) -> None:
        """Internal function called when a new item was put into the queue"""

        # utilizing short circuiting
        while self._on_put_one() and self._on_get_one():
            pass

    def _on_get(self) -> None:
        """Internal function called when an item was gotten from the queue"""

        # utilizing short circuiting
        while self._on_get_one() and self._on_put_one():
            pass

    def qsize(self) -> int:
        return len(self._items)

    def empty(self) -> bool:
        return not self._items

    def full(self) -> bool:
        return len(self._items) == self._items.max_size

    async def put(self, item: T) -> None:
        if not self.full():
            self._items.append(item)
            self._on_put()
            return

        if self._drained:
            raise QueueDrained

        future: asyncio.Future[None] = asyncio.Future()
        self._putters.append((future, item))
        await future

    def put_nowait(self, item: T) -> None:
        if not self.full():
            self._items.append(item)
            self._on_put()
            return

        if self._drained:
            raise QueueDrained

        raise asyncio.QueueFull

    async def get(self) -> T:
        if not self.empty():
            result = self._items.popleft()
            self._on_get()
            return result

        if self._drained:
            raise QueueDrained

        future: asyncio.Future[T] = asyncio.Future()
        self._getters.append(future)
        return await future

    def get_nowait(self) -> T:
        if not self.empty():
            result = self._items.popleft()
            self._on_get()
            return result

        if self._drained:
            raise QueueDrained

        raise asyncio.QueueEmpty

    def drain(self) -> List[T]:
        """Drains out the queue.

        If there are no items in the queue, causes any pending get calls
        to raise QueueDrained, then causes all future get or put calls to
        raise QueueDrained and returns an empty list.

        If there are items in the queue, moves those items into a list, allowing
        all pending put calls to be resolved (with their items included in the
        result), then causes all future get or put calls to raise QueueDrained
        and returns the list of items.
        """
        if self._drained:
            return []

        result = []
        while True:
            try:
                result.append(self.get_nowait())
            except asyncio.QueueEmpty:
                break

        self._drained = True
        for getter in self._getters:
            getter.set_exception(QueueDrained)
        assert not self._putters

        result = list(self._items)
        self._items = BoundedDeque(maxlen=0)
        self._getters = BoundedDeque(maxlen=0)
        self._putters = BoundedDeque(maxlen=0)
        return result


if TYPE_CHECKING:
    _: Type[AsyncQueueLike] = DrainableAsyncioQueue
