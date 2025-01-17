from typing import TYPE_CHECKING, Collection, List, Literal, Optional, Type, Union

from lonelypsp.compat import fast_dataclass
from lonelypsp.stateful.constants import (
    BroadcasterToSubscriberStatefulMessageType,
    PubSubStatefulMessageFlags,
)
from lonelypsp.stateful.generic_parser import B2S_MessageParser
from lonelypsp.stateful.parser_helpers import parse_simple_headers
from lonelypsp.stateful.serializer_helpers import (
    MessageSerializer,
    int_to_minimal_unsigned,
    serialize_simple_message,
)
from lonelypsp.sync_io import SyncReadableBytesIO


@fast_dataclass
class B2S_EnableZstdCustom:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberStatefulMessageType.ENABLE_ZSTD_CUSTOM]
    """discriminator value"""

    identifier: int
    """the identifier the broadcaster has assigned to compressing with this
    dictionary
    """

    compression_level: int
    """the compression level (any negative integer up to and including positive 22)
    that the broadcaster recommends for this dictionary; the subscriber is free to
    ignore this recommendation
    """

    min_size: int
    """the minimum in size in bytes that the broadcaster recommends for using
    this preset; the subscriber is free to ignore this recommendation
    """

    max_size: int
    """the maximum in size in bytes that the broadcaster recommends for using
    this preset; the subscriber is free to ignore this recommendation. 2**64-1
    for no limit
    """

    dictionary: bytes
    """the compression dictionary, in bytes, that is referenced when compressing
    with this identifier
    """

    authorization: Optional[str]
    """the authorization header that shows this was sent by the broadcaster

    empty strings are converted to None for consistency with http endpoints
    """

    tracing: bytes
    """the tracing data, which may be empty"""

    sha512: bytes
    """the sha512 hash of the dictionary, for authorization"""


_headers: Collection[str] = (
    "x-identifier",
    "x-compression-level",
    "x-min-size",
    "x-max-size",
    "authorization",
    "x-tracing",
    "x-sha512",
)


class B2S_EnableZstdCustomParser:
    """Satisfies B2S_MessageParser[B2S_EnableZstdCustom]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberStatefulMessageType]:
        return [BroadcasterToSubscriberStatefulMessageType.ENABLE_ZSTD_CUSTOM]

    @classmethod
    def parse(
        cls,
        flags: PubSubStatefulMessageFlags,
        type: BroadcasterToSubscriberStatefulMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_EnableZstdCustom:
        assert type == BroadcasterToSubscriberStatefulMessageType.ENABLE_ZSTD_CUSTOM

        headers = parse_simple_headers(flags, payload, _headers)
        identifier_bytes = headers["x-identifier"]
        if len(identifier_bytes) > 8:
            raise ValueError("x-identifier must be at most 8 bytes")

        identifier = int.from_bytes(identifier_bytes, "big")

        compression_level_bytes = headers["x-compression-level"]
        if len(compression_level_bytes) > 2:
            raise ValueError("x-compression-level max 2 bytes")

        compression_level = int.from_bytes(compression_level_bytes, "big", signed=True)

        min_size_bytes = headers["x-min-size"]
        if len(min_size_bytes) > 4:
            raise ValueError("x-min-size max 4 bytes")

        min_size = int.from_bytes(min_size_bytes, "big")

        max_size_bytes = headers["x-max-size"]
        if len(max_size_bytes) > 8:
            raise ValueError("x-max-size max 8 bytes")

        max_size = int.from_bytes(max_size_bytes, "big")

        dictionary = payload.read(-1)

        authorization_bytes = headers["authorization"]
        authorization: Optional[str] = None
        if authorization_bytes != b"":
            try:
                authorization = authorization_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("authorization must be a utf-8 string")

        tracing = headers["x-tracing"]
        sha512 = headers["x-sha512"]
        if len(sha512) != 64:
            raise ValueError("sha512 must be 64 bytes")

        return B2S_EnableZstdCustom(
            type=type,
            identifier=identifier,
            compression_level=compression_level,
            min_size=min_size,
            max_size=max_size,
            dictionary=dictionary,
            authorization=authorization,
            tracing=tracing,
            sha512=sha512,
        )


if TYPE_CHECKING:
    _: Type[B2S_MessageParser[B2S_EnableZstdCustom]] = B2S_EnableZstdCustomParser


def serialize_b2s_enable_zstd_custom(
    msg: B2S_EnableZstdCustom, /, *, minimal_headers: bool
) -> Union[bytes, bytearray]:
    """Satisfies MessageSerializer[B2S_EnableZstdCustom]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_headers,
        header_values=(
            int_to_minimal_unsigned(msg.identifier),
            msg.compression_level.to_bytes(2, "big", signed=True),
            int_to_minimal_unsigned(msg.min_size),
            int_to_minimal_unsigned(msg.max_size),
            msg.authorization.encode("utf-8") if msg.authorization is not None else b"",
            msg.tracing,
            msg.sha512,
        ),
        payload=msg.dictionary,
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[B2S_EnableZstdCustom] = serialize_b2s_enable_zstd_custom
