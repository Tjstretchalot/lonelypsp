import asyncio
from typing import Optional, TypeVar, Union, overload

T = TypeVar("T")
D = TypeVar("D")


@overload
async def cancel_and_check(task: asyncio.Task[T]) -> Optional[T]: ...


@overload
async def cancel_and_check(task: asyncio.Task[T], default: D) -> Union[T, D]: ...


async def cancel_and_check(
    task: asyncio.Task[T], default: Optional[D] = None
) -> Optional[Union[T, D]]:
    """If the task is finished, returns the result. If the task is errored,
    raises the error. If the task is cancelled, returns the default value.
    If the task is running, schedules asyncio.CancelledError to be raised
    at the current checkpoint and waits for the callbacks to finish, then
    rechecks the state of the task (which will no longer be running). Takes
    an arbitrary number of event loop iterations to complete.

    When using this, _if_ this is not canceled, then this always
    retrieves exceptions

    This is surprisingly difficult to do correctly
    """
    if not task.cancel():
        return task.result()

    try:
        await task
    except BaseException:
        ...

    if task.cancelled():
        return default
    return task.result()
