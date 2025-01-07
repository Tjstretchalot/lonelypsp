import hashlib
import io
from typing import List, Literal, Optional

from lonelypsp.compat import fast_dataclass


@fast_dataclass
class StrongEtag:
    format: Literal[0]
    """reserved discriminator value"""

    etag: bytes
    """the SHA512 hash of the document"""


@fast_dataclass
class GlobAndRecovery:
    glob: str
    recovery: Optional[str]


@fast_dataclass
class TopicAndRecovery:
    topic: bytes
    recovery: Optional[str]


def _encode_recovery(recovery: Optional[str]) -> bytes:
    if recovery is None:
        return b""
    return recovery.encode("utf-8")


class _PreallocatedBytesIO:
    def __init__(self, size: int) -> None:
        self.buf = bytearray(size)
        self.pos = 0

    def write(self, data: bytes) -> None:
        assert self.pos + len(data) <= len(self.buf)
        self.buf[self.pos : self.pos + len(data)] = data
        self.pos += len(data)

    def getbuf(self) -> bytearray:
        assert self.pos == len(self.buf)
        return self.buf


def make_strong_etag(
    url: str,
    topics: List[TopicAndRecovery],
    globs: List[GlobAndRecovery],
    *,
    recheck_sort: bool = True
) -> StrongEtag:
    """Generates the strong etag for `CHECK_SUBSCRIPTIONS` and
    `SET_SUBSCRIPTIONS` in a single pass; this is useful for reference
    or when there are a small number of topics/globs, but the etag
    can be generated from streaming data using `create_strong_etag_generator`

    NOTE: the topics and globs MUST be in (bytewise) lexicographic order
    for this to be stable. If `recheck_sort` is `True`, this will raise
    `ValueError` if the topics or globs are not sorted properly. If
    explicitly set to `False`, then the caller must have already ensured
    the topics and globs are sorted properly
    """

    if recheck_sort:
        for idx, topic in enumerate(topics):
            if idx > 0 and topic.topic <= topics[idx - 1].topic:
                raise ValueError(
                    "topics must be unique and in ascending lexicographic order"
                )

        for idx, glob in enumerate(globs):
            if idx > 0 and glob.glob <= globs[idx - 1].glob:
                raise ValueError(
                    "globs must be unique and in ascending lexicographic order"
                )

    doc = io.BytesIO()
    doc.write(b"URL")

    encoded_url = url.encode("utf-8")
    doc.write(len(encoded_url).to_bytes(2, "big"))
    doc.write(encoded_url)

    doc.write(b"\nEXACT")
    for topic in topics:
        doc.write(len(topic.topic).to_bytes(2, "big"))
        doc.write(topic.topic)
        encoded_recovery = _encode_recovery(topic.recovery)
        doc.write(len(encoded_recovery).to_bytes(2, "big"))
        doc.write(encoded_recovery)

    doc.write(b"\nGLOB")
    for glob in globs:
        encoded_glob = glob.glob.encode("utf-8")
        doc.write(len(encoded_glob).to_bytes(2, "big"))
        doc.write(encoded_glob)
        encoded_recovery = _encode_recovery(glob.recovery)
        doc.write(len(encoded_recovery).to_bytes(2, "big"))
        doc.write(encoded_recovery)

    doc.write(b"\n")
    etag = hashlib.sha512(doc.getvalue()).digest()
    return StrongEtag(format=0, etag=etag)


class StrongEtagGeneratorAtGlobs:
    """Adds glob patterns to the strong etag, then call finish() to get the strong etag"""

    def __init__(self, hasher: "hashlib._Hash", *, recheck_sort: bool = True) -> None:
        self.hasher = hasher
        self._recheck_sort = recheck_sort
        self._last_glob: Optional[bytes] = None

    def add_glob(self, *globs: GlobAndRecovery) -> "StrongEtagGeneratorAtGlobs":
        """Add the given glob or globs to the strong etag; multiple globs can be
        faster than calling add_glob multiple times as it reduces calls to the
        underlying hasher's update method, but requires more memory
        """
        if len(globs) == 0:
            return self

        encoded_globs = [g.glob.encode("utf-8") for g in globs]

        if self._recheck_sort:
            for g in encoded_globs:
                if self._last_glob is not None and g <= self._last_glob:
                    raise ValueError(
                        "globs must be unique and in ascending lexicographic order"
                    )
                self._last_glob = g

        encoded_recoveries = [_encode_recovery(g.recovery) for g in globs]

        buf = _PreallocatedBytesIO(
            4 * len(globs)
            + sum(len(g) for g in encoded_globs)
            + sum(len(r) for r in encoded_recoveries)
        )
        for encoded_glob, encoded_recovery in zip(encoded_globs, encoded_recoveries):
            buf.write(len(encoded_glob).to_bytes(2, "big"))
            buf.write(encoded_glob)
            buf.write(len(encoded_recovery).to_bytes(2, "big"))
            buf.write(encoded_recovery)

        self.hasher.update(buf.getbuf())
        return self

    def finish(self) -> StrongEtag:
        self.hasher.update(b"\n")
        return StrongEtag(format=0, etag=self.hasher.digest())


class StrongEtagGeneratorAtTopics:
    """Adds topics to the strong etag, then call finish_topics() to move onto globs"""

    def __init__(self, hasher: "hashlib._Hash", *, recheck_sort: bool = True) -> None:
        self.hasher = hasher
        self._recheck_sort = recheck_sort
        self._last_topic: Optional[bytes] = None

    def add_topic(self, *topic: TopicAndRecovery) -> "StrongEtagGeneratorAtTopics":
        """Add the given topic or topics to the strong etag; multiple topics can be
        faster than calling add_topic multiple times as it reduces calls to the
        underlying hasher's update method, but requires more memory
        """
        if len(topic) == 0:
            return self

        if self._recheck_sort:
            for t in topic:
                if self._last_topic is not None and t.topic <= self._last_topic:
                    raise ValueError(
                        "topics must be unique and in ascending lexicographic order"
                    )
                self._last_topic = t.topic

        encoded_recoveries = [_encode_recovery(t.recovery) for t in topic]

        buf = _PreallocatedBytesIO(
            4 * len(topic)
            + sum(len(t.topic) for t in topic)
            + sum(len(r) for r in encoded_recoveries)
        )
        for t, r in zip(topic, encoded_recoveries):
            buf.write(len(t.topic).to_bytes(2, "big"))
            buf.write(t.topic)
            buf.write(len(r).to_bytes(2, "big"))
            buf.write(r)

        self.hasher.update(buf.getbuf())
        return self

    def finish_topics(self) -> StrongEtagGeneratorAtGlobs:
        self.hasher.update(b"\nGLOB")
        return StrongEtagGeneratorAtGlobs(self.hasher, recheck_sort=self._recheck_sort)


def create_strong_etag_generator(
    url: str, *, recheck_sort: bool = True
) -> StrongEtagGeneratorAtTopics:
    """Returns a StrongEtagGeneratorAtTopics that can be used to add topics and
    globs to the strong etag, then call finish_topics() to get the generator for
    adding globs, then call finish() to get the strong etag. This avoids having
    to ever store the actual document being hashed but requires more calls to
    the underlying hasher's update method

    Example usage:

    ```python
    etag = (
        create_strong_etag_generator("https://example.com", recheck_sort=False)
        .add_topic(
            TopicAndRecovery(b"topic1", "recovery1"),
            TopicAndRecovery(b"topic2", "recovery2")
        )
        .finish_topics()
        .add_glob(
            GlobAndRecovery("glob1", "recovery3"),
            GlobAndRecovery("glob2", "recovery4")
        )
        .finish()
    )
    ```

    NOTE: the topics and globs MUST be in (bytewise) lexicographic order
    for this to be stable. If `recheck_sort` is `True`, this will raise
    `ValueError` if the topics or globs are not sorted properly. If
    explicitly set to `False`, then the caller must have already ensured
    the topics and globs are sorted properly
    """
    encoded_url = url.encode("utf-8")
    buf = _PreallocatedBytesIO(3 + 2 + len(encoded_url) + 6)

    buf.write(b"URL")
    buf.write(len(encoded_url).to_bytes(2, "big"))
    buf.write(encoded_url)
    buf.write(b"\nEXACT")

    hasher = hashlib.sha512(buf.getbuf())
    return StrongEtagGeneratorAtTopics(hasher, recheck_sort=recheck_sort)
