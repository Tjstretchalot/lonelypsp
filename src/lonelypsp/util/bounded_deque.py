from typing import Generic, Iterable, List, Optional, TypeVar


class BoundedDequeFullError(Exception):
    """The exception raised if a bounded deque is full and an element is
    attempted to be added"""

    pass


T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


class BoundedDequeInPlaceIter(Generic[T_co]):
    def __init__(self, parent: "BoundedDeque[T_co]") -> None:
        self.parent = parent
        self.offset = 0

    def __iter__(self) -> "BoundedDequeInPlaceIter[T_co]":
        return self

    def __next__(self) -> T_co:
        if self.offset >= self.parent.length:
            raise StopIteration
        idx = (self.parent.start + self.offset) % len(self.parent.data)
        self.offset += 1
        result = self.parent.data[idx]
        assert result is not None, "invariant violated"
        return result


class BoundedDeque(Generic[T]):
    """Functions similarly to collections.deque, but raises an error if full instead
    of silently dropping elements, plus uses the expected implementation
    (compact array) rather than the double linked list from cpython. Without
    benchmarking this is probably better on PyPy but worse in CPython

    The implementation is guarranteed in this api, meaning you can e.g.
    use resize safely

    Not thread-safe, not process-safe

    append: amortized O(1)
    pop: O(1)
    appendleft: amortized O(1)
    popleft: O(1)
    iteration: O(n), at most one out of order access assuming no resizes
    """

    def __init__(
        self, /, iterable: Optional[Iterable[T]] = None, *, maxlen: Optional[int] = None
    ) -> None:
        self.data: List[Optional[T]] = list(iterable) if iterable is not None else []
        """the data in the deque which will be resized exponentially until
        it reaches maxlen (if any)
        """

        self.start = 0
        """the first non-None entry in data"""

        self.length = len(self.data)
        """the number of non-None entries in data, all after start, wrapping
        if necessary
        """

        self.max_size = maxlen
        """the maximum allowed size, or None if unbounded"""

        if self.max_size is not None and len(self.data) > self.max_size:
            raise ValueError("iterable larger than maxlen")

    def __len__(self) -> int:
        return self.length

    def __bool__(self) -> bool:
        return bool(self.length)

    def __getitem__(self, idx: int) -> T:
        if idx < 0 or idx >= self.length:
            raise IndexError("index out of range")
        result = self.data[(self.start + idx) % len(self.data)]
        assert result is not None, "invariant violated"
        return result

    def __setitem__(self, idx: int, val: T) -> None:
        if idx < 0 or idx >= self.length:
            raise IndexError("index out of range")
        self.data[(self.start + idx) % len(self.data)] = val

    def __repr__(self) -> str:
        return f"BoundedDeque({list(self)!r}, maxlen={self.max_size!r})"

    def __str__(self) -> str:
        return f"BoundedDeque{list(self)}; maxlen={self.max_size!r}, start={self.start}, length={len(self)}, capacity={len(self.data)}"

    def resize(self, min_size: int) -> None:
        """Attempts to resize the underlying array to have at least the given
        size. Raises BoundedDequeFullError if min_size > self.max_size
        """
        if len(self.data) >= min_size:
            return

        if self.max_size is not None and min_size > self.max_size:
            raise BoundedDequeFullError

        new_data: List[Optional[T]] = [None] * min_size
        idx = self.start
        for new_idx in range(self.length):
            new_data[new_idx] = self.data[idx]
            idx += 1
            if idx == len(self.data):
                idx = 0
        self.data = new_data
        self.start = 0

    def ensure_space_for(self, n: int) -> None:
        """Ensures that there is space for n more elements in the deque.
        Raises BoundedDequeFullError if this would require expanding beyond
        min_size.

        Prefers to expand the array exponentially, but respects max_size
        """
        assert n >= 0
        min_size = self.length + n
        if min_size <= len(self.data):
            return

        next_pow_2 = 1 << (min_size - 1).bit_length()
        if self.max_size is None or next_pow_2 <= self.max_size:
            self.resize(next_pow_2)
            return

        if min_size > self.max_size:
            raise BoundedDequeFullError

        self.resize(self.max_size)

    def append(self, val: T) -> None:
        """Appends an element to the end of the deque. Raises
        BoundedDequeFullError if the deque is full
        """
        self.ensure_space_for(1)
        idx = (self.start + self.length) % len(self.data)
        self.data[idx] = val
        self.length += 1

    def pop(self) -> T:
        """Pops the last element from the deque. Raises IndexError if the
        deque is empty
        """
        if self.length == 0:
            raise IndexError("pop from an empty deque")
        idx = (self.start + self.length - 1) % len(self.data)
        result = self.data[idx]
        assert result is not None, "invariant violated"
        self.data[idx] = None
        self.length -= 1
        return result

    def appendleft(self, val: T) -> None:
        """Appends an element to the start of the deque. Raises
        BoundedDequeFullError if the deque is full
        """
        self.ensure_space_for(1)
        self.start -= 1
        if self.start == -1:
            self.start = len(self.data) - 1
        self.data[self.start] = val
        self.length += 1

    def popleft(self) -> T:
        """Pops the first element from the deque. Raises IndexError if the
        deque is empty
        """
        if self.length == 0:
            raise IndexError("pop from an empty deque")
        result = self.data[self.start]
        assert result is not None, "invariant violated"
        self.data[self.start] = None
        self.start += 1
        if self.start == len(self.data):
            self.start = 0
        self.length -= 1
        return result

    def remove(self, val: T) -> None:
        """Removes the first occurrence of val from the deque. Raises ValueError
        if val is not in the deque. This is a pretty slow operation if the
        value is in the middle
        """
        if not self:
            raise ValueError("deque is empty")

        array_idx = self.start
        real_idx = 0
        while True:
            if self.data[array_idx] == val:
                break
            real_idx += 1
            if real_idx == self.length:
                raise ValueError("value not in deque")
            array_idx += 1
            if array_idx == len(self.data):
                array_idx = 0

        if real_idx == 0:
            self.popleft()
            return
        if real_idx == self.length - 1:
            self.pop()
            return

        # need to rearrange to avoid a hole by either shifting items
        # left or right, we'll do whichever requires less movement
        hole_real_idx = real_idx
        hole_array_idx = array_idx
        del array_idx
        del real_idx

        if hole_real_idx <= (self.length // 2):
            # we have a hole at real_idx that we will fill by moving
            # every item left of the hole right 1 idx
            last = self.data[self.start]

            moving_real_idx = 1
            moving_array_idx = self.start + 1
            if moving_array_idx == len(self.data):
                moving_array_idx = 0

            while moving_real_idx <= hole_real_idx:
                tmp = self.data[moving_array_idx]
                self.data[moving_array_idx] = last
                last = tmp

                moving_real_idx += 1
                moving_array_idx += 1
                if moving_array_idx == len(self.data):
                    moving_array_idx = 0

            self.data[self.start] = None
            self.start += 1
            self.length -= 1

            if self.start == len(self.data):
                self.start = 0
            return

        # we have a hole at real_idx that we will fill by moving
        # every item right of the hole left 1 idx, replacing the right-most real index
        # with None

        moving_real_idx = hole_real_idx
        moving_array_idx = hole_array_idx

        while moving_real_idx < self.length - 1:
            next_moving_array_idx = moving_array_idx + 1
            if next_moving_array_idx == len(self.data):
                next_moving_array_idx = 0

            self.data[moving_array_idx] = self.data[next_moving_array_idx]

            moving_real_idx += 1
            moving_array_idx = next_moving_array_idx

        self.data[moving_array_idx] = None
        self.length -= 1

    def __iter__(self) -> BoundedDequeInPlaceIter[T]:
        return BoundedDequeInPlaceIter(self)
