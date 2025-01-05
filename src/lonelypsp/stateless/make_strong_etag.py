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


def make_strong_etag(
    url: str, topics: List[bytes], globs: List[str], *, recheck_sort: bool = True
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
            if idx > 0 and topic <= topics[idx - 1]:
                raise ValueError(
                    "topics must be unique and in ascending lexicographic order"
                )

        for idx, glob in enumerate(globs):
            if idx > 0 and glob <= globs[idx - 1]:
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
        doc.write(len(topic).to_bytes(2, "big"))
        doc.write(topic)

    doc.write(b"\nGLOB")
    for glob in globs:
        encoded_glob = glob.encode("utf-8")
        doc.write(len(encoded_glob).to_bytes(2, "big"))
        doc.write(encoded_glob)

    doc.write(b"\n")
    etag = hashlib.sha512(doc.getvalue()).digest()
    return StrongEtag(format=0, etag=etag)


class StrongEtagGeneratorAtGlobs:
    """Adds glob patterns to the strong etag, then call finish() to get the strong etag"""

    def __init__(self, hasher: "hashlib._Hash", *, recheck_sort: bool = True) -> None:
        self.hasher = hasher
        self._recheck_sort = recheck_sort
        self._last_glob: Optional[bytes] = None

    def add_glob(self, *globs: str) -> "StrongEtagGeneratorAtGlobs":
        """Add the given glob or globs to the strong etag; multiple globs can be
        faster than calling add_glob multiple times as it reduces calls to the
        underlying hasher's update method, but requires more memory
        """
        if len(globs) == 0:
            return self

        encoded_globs = [g.encode("utf-8") for g in globs]

        if self._recheck_sort:
            for g in encoded_globs:
                if self._last_glob is not None and g <= self._last_glob:
                    raise ValueError(
                        "globs must be unique and in ascending lexicographic order"
                    )
                self._last_glob = g

        buf = bytearray(2 * len(globs) + sum(len(g) for g in encoded_globs))
        pos = 0
        for encoded_glob in encoded_globs:
            buf[pos : pos + 2] = len(encoded_glob).to_bytes(2, "big")
            pos += 2
            buf[pos : pos + len(encoded_glob)] = encoded_glob
            pos += len(encoded_glob)

        self.hasher.update(buf)
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

    def add_topic(self, *topic: bytes) -> "StrongEtagGeneratorAtTopics":
        """Add the given topic or topics to the strong etag; multiple topics can be
        faster than calling add_topic multiple times as it reduces calls to the
        underlying hasher's update method, but requires more memory
        """
        if len(topic) == 0:
            return self

        if self._recheck_sort:
            for t in topic:
                if self._last_topic is not None and t <= self._last_topic:
                    raise ValueError(
                        "topics must be unique and in ascending lexicographic order"
                    )
                self._last_topic = t

        buf = bytearray(2 * len(topic) + sum(len(t) for t in topic))
        pos = 0
        for t in topic:
            buf[pos : pos + 2] = len(t).to_bytes(2, "big")
            pos += 2
            buf[pos : pos + len(t)] = t
            pos += len(t)

        self.hasher.update(buf)
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
        .add_topic(b"topic1", b"topic2")
        .finish_topics()
        .add_glob("glob1", "glob2")
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
    buf = bytearray(3 + 2 + len(encoded_url) + 6)
    buf[0:3] = b"URL"
    buf[3:5] = len(encoded_url).to_bytes(2, "big")
    buf[5:-6] = encoded_url
    buf[-6:] = b"\nEXACT"

    hasher = hashlib.sha512(buf)
    return StrongEtagGeneratorAtTopics(hasher, recheck_sort=recheck_sort)
