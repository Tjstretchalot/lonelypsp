import sys
from dataclasses import dataclass as fast_dataclass
from functools import partial
from typing import TypeVar

__all__ = ["fast_dataclass", "assert_never"]

T = TypeVar("T")
if sys.version_info >= (3, 10):

    def make_dataclass_fast(x: T) -> T:
        return partial(x, frozen=True, slots=True)  # type: ignore

    fast_dataclass = make_dataclass_fast(fast_dataclass)
else:

    def make_dataclass_fast(x: T) -> T:
        return partial(x, frozen=True)  # type: ignore

    fast_dataclass = make_dataclass_fast(fast_dataclass)


if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from typing import NoReturn
    from typing import NoReturn as Never

    def assert_never(value: Never) -> NoReturn:
        raise AssertionError(f"Unhandled type: {value!r}")
