import asyncio
from enum import Enum, auto
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
)

from lonelypsp.compat import fast_dataclass
from lonelypsp.util.async_queue_like import AsyncQueueLike
from lonelypsp.util.bounded_deque import BoundedDeque

T = TypeVar("T")


class QueueDrained(Exception):
    """The exception raised when a drained queue is attempted to be accessed"""


class _GetType(Enum):
    GET = auto()
    WAIT = auto()


@fast_dataclass
class _GetterGet(Generic[T]):
    type: Literal[_GetType.GET]
    future: asyncio.Future[T]


@fast_dataclass
class _GetterWait:
    type: Literal[_GetType.WAIT]
    future: asyncio.Future[None]


class _PutType(Enum):
    PUT = auto()
    WAIT = auto()


@fast_dataclass
class _PutterPut(Generic[T]):
    type: Literal[_PutType.PUT]
    item: T
    future: asyncio.Future[None]


@fast_dataclass
class _PutterWait:
    type: Literal[_PutType.WAIT]
    future: asyncio.Future[None]


class DrainableAsyncioQueue(Generic[T]):
    """Satisfies AsyncioQueueLike[T] but adds the following functionality:

    - max size of 0 means that the queue is always full instead of an unbounded
      queue. a value of None is now also allowed and means an unbounded queue

    - adds optional maximum number of pending get() tasks when the queue is empty

    - adds optional maximum number of pending put() tasks when the queue is full

    - drain() method which empties the queue and raises a QueueDrained exception
      for any future get() or put() calls

    - wait_not_empty() and wait_not_full() methods which are non-consuming version of get/put
      which are safely cancelable at the cost of being inefficient if there are multiple
      consumers/producers respectively.

    - can be used as an asynchronous context manager, which calls drain() when exiting
    """

    def __init__(
        self,
        items: Optional[Iterable[T]] = None,
        /,
        *,
        max_size: Optional[int] = None,
        max_getters: Optional[int] = None,
        max_putters: Optional[int] = None,
    ) -> None:
        self._items: BoundedDeque[T] = BoundedDeque(maxlen=max_size)
        self._getters: BoundedDeque[Union[_GetterGet[T], _GetterWait]] = BoundedDeque(
            maxlen=max_getters
        )
        self._putters: BoundedDeque[Union[_PutterPut[T], _PutterWait]] = BoundedDeque(
            maxlen=max_putters
        )
        # after draining _items will have maxlen 0, but we raise a different
        # error
        self._drained = False

        if items is not None:
            for item in items:
                self._items.append(item)

    async def __aenter__(self) -> "DrainableAsyncioQueue[T]":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.drain()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self._items)!r})"

    def __str__(self) -> str:
        return f"{{{self.__class__.__name__}; items=({self._items}) drained={self._drained} getters={len(self._getters)} putters={len(self._putters)}}}"

    def _on_put_one(self) -> bool:
        """Internal function to implement _on_put and _on_get; alerts the next
        getter if there is one and returns True, otherwise returns False

        Note that if there is a getter then we may now have space for another
        putter
        """
        while True:
            if not self._getters:
                return False

            getter = self._getters.popleft()
            if getter.type == _GetType.WAIT:
                getter.future.set_result(None)
                continue

            item = self._items.popleft()
            getter.future.set_result(item)
            return True

    def _on_get_one(self) -> bool:
        """Internal function to implement _on_put and _on_get; alerts the next
        putter if there is one and returns True, otherwise returns False

        Note that if there is a putter then we may now have space for another
        getter
        """
        while True:
            if not self._putters:
                return False

            putter = self._putters.popleft()
            if putter.type == _PutType.WAIT:
                putter.future.set_result(None)
                continue

            putter.future.set_result(None)
            self._items.append(putter.item)
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

        putter: _PutterPut[T] = _PutterPut(
            type=_PutType.PUT, item=item, future=asyncio.Future()
        )
        self._putters.append(putter)
        try:
            await asyncio.wait([putter.future])
        except asyncio.CancelledError:
            if putter.future.cancel():
                self._putters.remove(putter)
                raise
            putter.future.result()

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

        getter: _GetterGet[T] = _GetterGet(type=_GetType.GET, future=asyncio.Future())
        self._getters.append(getter)
        try:
            await asyncio.wait([getter.future])
        except asyncio.CancelledError:
            if getter.future.cancel():
                self._getters.remove(getter)
                raise
            return await getter.future

        return getter.future.result()

    def get_nowait(self) -> T:
        if not self.empty():
            result = self._items.popleft()
            self._on_get()
            return result

        if self._drained:
            raise QueueDrained

        raise asyncio.QueueEmpty

    async def wait_not_empty(self) -> None:
        """Between this entering and the returned coroutine returning normally, at some
        point the queue will have had an item available for get() call

        This is generally helpful iff there is a single consumer; if there are multiple
        consumers, between the caller being scheduled and being run the item may have already
        been consumed, leading to wasted cycles. However, a big advantage of this is it can
        be freely canceled without having to worry about if it completed or not

        Raises QueueDrained if the queue has been drained before this call or before an item
        is added
        """
        if not self.empty():
            return

        if self._drained:
            raise QueueDrained

        getter = _GetterWait(type=_GetType.WAIT, future=asyncio.Future())
        self._getters.append(getter)
        try:
            await asyncio.wait([getter.future])
        except asyncio.CancelledError:
            if getter.future.cancel():
                self._getters.remove(getter)
                raise
            await getter.future

    async def wait_not_full(self) -> None:
        """Between this entering and the returned coroutine returning normally, at some
        point the queue will have had space available for a put() call

        This is generally helpful iff there is a single producer; if there are multiple
        producers, between the caller being scheduled and being run the queue may have already
        been filled, leading to wasted cycles. However, a big advantage of this is it can
        be freely canceled without having to worry about if it completed or not

        Raises QueueDrained if the queue has been drained before this call, will complete
        normally if drained after being put into the queue
        """
        if not self.full():
            return

        if self._drained:
            raise QueueDrained

        putter = _PutterWait(type=_PutType.WAIT, future=asyncio.Future())
        self._putters.append(putter)
        try:
            await asyncio.wait([putter.future])
        except asyncio.CancelledError:
            if putter.future.cancel():
                self._putters.remove(putter)
                raise
            await putter.future

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
            getter.future.set_exception(QueueDrained)
        assert not self._putters

        self._items = BoundedDeque(maxlen=0)
        self._getters = BoundedDeque(maxlen=0)
        self._putters = BoundedDeque(maxlen=0)
        return result


if TYPE_CHECKING:
    _: Type[AsyncQueueLike] = DrainableAsyncioQueue
