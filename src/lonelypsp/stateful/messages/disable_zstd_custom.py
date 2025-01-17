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
class B2S_DisableZstdCustom:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberStatefulMessageType.DISABLE_ZSTD_CUSTOM]
    """discriminator value"""

    identifier: int
    """the identifier the broadcaster previously assigned to compressing with this
    dictionary
    """

    authorization: Optional[str]
    """the authorization header that shows this was sent by the broadcaster

    empty strings are converted to None for consistency with http endpoints
    """

    tracing: bytes
    """the tracing data, which may be empty"""


_headers: Collection[str] = ("x-identifier", "authorization", "x-tracing")


class B2S_DisableZstdCustomParser:
    """Satisfies B2S_MessageParser[B2S_DisableZstdCustom]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberStatefulMessageType]:
        return [BroadcasterToSubscriberStatefulMessageType.DISABLE_ZSTD_CUSTOM]

    @classmethod
    def parse(
        cls,
        flags: PubSubStatefulMessageFlags,
        type: BroadcasterToSubscriberStatefulMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_DisableZstdCustom:
        assert type == BroadcasterToSubscriberStatefulMessageType.DISABLE_ZSTD_CUSTOM

        headers = parse_simple_headers(flags, payload, _headers)
        identifier_bytes = headers["x-identifier"]
        if len(identifier_bytes) > 8:
            raise ValueError("x-identifier must be at most 8 bytes")

        identifier = int.from_bytes(identifier_bytes, "big")

        authorization_bytes = headers["authorization"]
        authorization: Optional[str] = None
        if authorization_bytes != b"":
            try:
                authorization = authorization_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("authorization must be a utf-8 string")

        tracing = headers["x-tracing"]

        return B2S_DisableZstdCustom(
            type=type,
            identifier=identifier,
            authorization=authorization,
            tracing=tracing,
        )


if TYPE_CHECKING:
    _: Type[B2S_MessageParser[B2S_DisableZstdCustom]] = B2S_DisableZstdCustomParser


def serialize_b2s_disable_zstd_custom(
    msg: B2S_DisableZstdCustom, /, *, minimal_headers: bool
) -> Union[bytes, bytearray]:
    """Satisfies MessageSerializer[B2S_DisableZstdCustom]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_headers,
        header_values=(
            int_to_minimal_unsigned(msg.identifier),
            msg.authorization.encode("utf-8") if msg.authorization is not None else b"",
            msg.tracing,
        ),
        payload=b"",
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[B2S_DisableZstdCustom] = serialize_b2s_disable_zstd_custom
