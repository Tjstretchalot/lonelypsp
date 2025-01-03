# ruff: noqa: T201
"""fuzzes the bounded queue behaving like a list"""

import random
import sys
from typing import List

from lonelypsp.util.bounded_deque import BoundedDeque


def _fuzz() -> None:
    try:
        for i in range(10000):
            if i % 100 == 0:
                print("." if i % 1000 != 0 else "o", end="")
                sys.stdout.flush()
            seed = random.randint(0, 2**64 - 1)
            _test_seed(seed)
    except BaseException:
        print()
        raise

    print("done")


def _test_seed(seed: int) -> None:
    random.seed(seed)

    testing: BoundedDeque[int] = BoundedDeque()
    good: List[int] = []

    ctr = 0
    for i in range(1000):
        choice = random.choice(
            ["remove", "pop", "popleft"]
            if len(good) > 1000
            else (
                ["append", "appendleft", "remove", "pop", "popleft"]
                if good
                else ["append", "appendleft"]
            )
        )

        if choice == "append":
            testing.append(ctr)
            good.append(ctr)
            ctr += 1
        elif choice == "appendleft":
            testing.appendleft(ctr)
            good.insert(0, ctr)
            ctr += 1
        elif choice == "pop":
            testing.pop()
            good.pop()
        elif choice == "popleft":
            testing.popleft()
            good.pop(0)
        elif choice == "remove":
            to_remove = random.choice(good)
            testing.remove(to_remove)
            good.remove(to_remove)

        assert (
            list(testing) == good
        ), f"seed={seed} on iteration={i} has {testing} vs {good=}"
        # verify all unused parts are None

        real_idx = testing.length
        array_idx = (testing.start + testing.length) % len(testing.data)
        capacity = len(testing.data)
        while real_idx < capacity:
            assert (
                testing.data[array_idx] is None
            ), f"seed={seed} on iteration={i} has corrupt {testing}, {testing.data=}"
            real_idx += 1
            array_idx += 1
            if array_idx == capacity:
                array_idx = 0


if __name__ == "__main__":
    _fuzz()
