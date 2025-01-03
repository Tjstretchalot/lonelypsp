import hashlib
import io
from typing import List, Literal

from lonelypsp.compat import fast_dataclass


@fast_dataclass
class StrongEtag:
    format: Literal[0]
    """reserved discriminator value"""

    etag: bytes
    """the SHA512 hash of the document"""


def make_strong_etag(url: str, topics: List[bytes], globs: List[str]) -> StrongEtag:
    """Generates the strong etag for `CHECK_SUBSCRIPTIONS` and
    `SET_SUBSCRIPTIONS` in a single pass; this is useful for reference
    or when there are a small number of topics/globs, but the etag
    can be generated from streaming data using `create_strong_etag_generator`
    """

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

    def __init__(self, hasher: "hashlib._Hash") -> None:
        self.hasher = hasher

    def add_glob(self, *globs: str) -> "StrongEtagGeneratorAtGlobs":
        """Add the given glob or globs to the strong etag; multiple globs can be
        faster than calling add_glob multiple times as it reduces calls to the
        underlying hasher's update method, but requires more memory
        """
        if len(globs) == 0:
            return self

        encoded_globs = [g.encode("utf-8") for g in globs]
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

    def __init__(self, hasher: "hashlib._Hash") -> None:
        self.hasher = hasher

    def add_topic(self, *topic: bytes) -> "StrongEtagGeneratorAtTopics":
        """Add the given topic or topics to the strong etag; multiple topics can be
        faster than calling add_topic multiple times as it reduces calls to the
        underlying hasher's update method, but requires more memory
        """
        if len(topic) == 0:
            return self

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
        return StrongEtagGeneratorAtGlobs(self.hasher)


def create_strong_etag_generator(url: str) -> StrongEtagGeneratorAtTopics:
    """Returns a StrongEtagGeneratorAtTopics that can be used to add topics and
    globs to the strong etag, then call finish_topics() to get the generator for
    adding globs, then call finish() to get the strong etag. This avoids having
    to ever store the actual document being hashed but requires more calls to
    the underlying hasher's update method

    Example usage:

    ```python
    etag = (
        create_strong_etag_generator("https://example.com")
        .add_topic(b"topic1", b"topic2")
        .finish_topics()
        .add_glob("glob1", "glob2")
        .finish()
    )
    ```
    """
    encoded_url = url.encode("utf-8")
    buf = bytearray(3 + 2 + len(encoded_url) + 6)
    buf[0:3] = b"URL"
    buf[3:5] = len(encoded_url).to_bytes(2, "big")
    buf[5:-6] = encoded_url
    buf[-6:] = b"\nEXACT"

    hasher = hashlib.sha512(buf)
    return StrongEtagGeneratorAtTopics(hasher)
