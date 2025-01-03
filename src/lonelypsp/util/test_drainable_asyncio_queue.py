# ruff: noqa: T201
"""Tests that cancellation works as well as is possible and shows the
somewhat unintuitive but expected behavior, which also highlights why
wait_not_empty() combined with get_no_wait() is much easier to use 
compared to get() (and similarly, wait_not_full() with put_no_wait() is
easier to use compared to put()). Essentially, if cancellation goes
through depends on if there are event loop iterations after cancellation
"""

import asyncio

from lonelypsp.util.drainable_asyncio_queue import DrainableAsyncioQueue


async def _test() -> None:
    await _test_cancel_put_no_yield()
    print(".", end="", flush=True)
    await _test_cancel_put_with_yield()
    print(".", end="", flush=True)
    await _test_cancel_wait_not_full_no_yield()
    print(".", end="", flush=True)
    await _test_cancel_wait_not_full_with_yield()
    print(".", end="", flush=True)
    await _test_cancel_get_no_yield()
    print(".", end="", flush=True)
    await _test_cancel_get_with_yield()
    print(".", end="", flush=True)
    await _test_cancel_wait_not_empty_no_yield()
    print(".", end="", flush=True)
    await _test_cancel_wait_not_empty_with_yield()
    print(".", end="", flush=True)
    print("done")


async def _test_cancel_put_no_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    q.put_nowait(1)
    putter = asyncio.create_task(q.put(2))
    await asyncio.sleep(0)
    assert putter.cancel()  # does successfully schedule a CancelledError
    drained = q.drain()  # CancelledError hasn't been raised yet
    assert drained == [1, 2], f"{drained=}, expected [1, 2]"
    assert not putter.cancelled()  # will be able to see the cancellation hasn't run yet
    assert not putter.done()  # same as previous but for clarity
    await putter  # raises the CancelledError, detects finished normally (no error)


async def _test_cancel_put_with_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    q.put_nowait(1)
    putter = asyncio.create_task(q.put(2))
    await asyncio.sleep(0)
    assert putter.cancel()  # does successfully schedule a CancelledError
    await asyncio.sleep(0)  # raises the CancelledError
    drained = q.drain()
    assert drained == [1], f"{drained=}, expected [1]"
    assert putter.cancelled()  # will be able to see the cancellation has run
    assert putter.done()  # same as previous but for clarity


async def _test_cancel_wait_not_full_no_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    q.put_nowait(1)
    waiter = asyncio.create_task(q.wait_not_full())
    await asyncio.sleep(0)
    assert waiter.cancel()  # does successfully schedule a CancelledError
    assert q.drain() == [1]  # CancelledError hasn't been raised yet
    assert not waiter.cancelled()  # will be able to see the cancellation hasn't run yet
    assert not waiter.done()  # same as previous but for clarity
    await waiter  # raises the CancelledError, detects finished normally (no error)


async def _test_cancel_wait_not_full_with_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    q.put_nowait(1)
    waiter = asyncio.create_task(q.wait_not_full())
    await asyncio.sleep(0)
    assert waiter.cancel()  # does successfully schedule a CancelledError
    await asyncio.sleep(0)  # raises the CancelledError
    assert q.drain() == [1]
    assert waiter.cancelled()  # will be able to see the cancellation has run
    assert waiter.done()  # same as previous but for clarity


async def _test_cancel_get_no_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    getter = asyncio.create_task(q.get())
    await asyncio.sleep(0)
    assert getter.cancel()  # does successfully schedule a CancelledError
    q.put_nowait(1)  # CancelledError hasn't been raised yet
    assert not getter.cancelled()  # will be able to see the cancellation hasn't run yet
    assert not getter.done()  # same as previous but for clarity
    assert (
        await getter == 1
    )  # raises the CancelledError, detects finished normally (no error)
    drained = q.drain()
    assert drained == [], f"{drained=}, expected []"


async def _test_cancel_get_with_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    getter = asyncio.create_task(q.get())
    await asyncio.sleep(0)
    assert getter.cancel()  # does successfully schedule a CancelledError
    await asyncio.sleep(0)  # raises the CancelledError
    q.put_nowait(1)
    assert getter.cancelled()  # will be able to see the cancellation has run
    assert getter.done()  # same as previous but for clarity
    drained = q.drain()
    assert drained == [1], f"{drained=}, expected [1]"


async def _test_cancel_wait_not_empty_no_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    waiter = asyncio.create_task(q.wait_not_empty())
    await asyncio.sleep(0)
    assert waiter.cancel()  # does successfully schedule a CancelledError
    q.put_nowait(1)  # CancelledError hasn't been raised yet
    assert not waiter.cancelled()  # will be able to see the cancellation hasn't run yet
    assert not waiter.done()  # same as previous but for clarity
    await waiter  # raises the CancelledError, detects finished normally (no error)
    drained = q.drain()
    assert drained == [1], f"{drained=}, expected [1]"


async def _test_cancel_wait_not_empty_with_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    waiter = asyncio.create_task(q.wait_not_empty())
    await asyncio.sleep(0)
    assert waiter.cancel()  # does successfully schedule a CancelledError
    await asyncio.sleep(0)  # raises the CancelledError
    q.put_nowait(1)
    assert waiter.cancelled()  # will be able to see the cancellation has run
    assert waiter.done()  # same as previous but for clarity
    drained = q.drain()
    assert drained == [1], f"{drained=}, expected [1]"


if __name__ == "__main__":
    asyncio.run(_test())
