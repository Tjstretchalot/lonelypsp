# ruff: noqa: T201
"""Verifies that with cancel_and_check it is possible to use get() and put(),
though it is rather perplexing
"""

import asyncio

from lonelypsp.util.cancel_and_check import cancel_and_check
from lonelypsp.util.drainable_asyncio_queue import DrainableAsyncioQueue


async def _test() -> None:
    await _test_get_no_yield()
    print(".", end="", flush=True)
    await _test_get_with_1_yield()
    print(".", end="", flush=True)
    await _test_get_with_2_yield()
    print(".", end="", flush=True)
    await _test_put_no_yield()
    print(".", end="", flush=True)
    await _test_put_with_1_yield()
    print(".", end="", flush=True)
    await _test_put_with_2_yield()
    print(".", end="", flush=True)
    print("done")


async def _test_get_no_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue()
    getter = asyncio.create_task(q.get())
    canceler = asyncio.create_task(cancel_and_check(getter))
    q.put_nowait(1)
    assert (await canceler) == 1
    assert q.drain() == []


async def _test_get_with_1_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue()
    getter = asyncio.create_task(q.get())
    canceler = asyncio.create_task(cancel_and_check(getter))
    await asyncio.sleep(0)
    q.put_nowait(1)
    assert (await canceler) == 1
    assert q.drain() == []


async def _test_get_with_2_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue()
    getter = asyncio.create_task(q.get())
    canceler = asyncio.create_task(cancel_and_check(getter))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    q.put_nowait(1)
    result = await canceler
    assert result is None, f"{result=}"
    assert q.drain() == [1]


async def _test_put_no_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    q.put_nowait(1)
    putter = asyncio.create_task(q.put(2))
    canceler = asyncio.create_task(cancel_and_check(putter, False))
    assert q.get_nowait() == 1
    assert (await canceler) is None  # None is the result of put() on success
    assert q.drain() == [2]


async def _test_put_with_1_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    q.put_nowait(1)
    putter = asyncio.create_task(q.put(2))
    canceler = asyncio.create_task(cancel_and_check(putter, False))
    await asyncio.sleep(0)
    assert q.get_nowait() == 1
    assert (await canceler) is None  # None is the result of put() on success
    assert q.drain() == [2]


async def _test_put_with_2_yield() -> None:
    q: DrainableAsyncioQueue[int] = DrainableAsyncioQueue(max_size=1)
    q.put_nowait(1)
    putter = asyncio.create_task(q.put(2))
    canceler = asyncio.create_task(cancel_and_check(putter, False))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert q.get_nowait() == 1
    assert (await canceler) is False  # default value, meaning put() failed
    assert q.drain() == []


if __name__ == "__main__":
    asyncio.run(_test())
