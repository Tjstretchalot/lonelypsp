from typing import TYPE_CHECKING, Collection, List, Literal, Type, Union

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


_headers: Collection[str] = ("x-identifier",)


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

        return B2S_DisableZstdCustom(
            type=type,
            identifier=identifier,
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
        header_values=(int_to_minimal_unsigned(msg.identifier),),
        payload=b"",
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[B2S_DisableZstdCustom] = serialize_b2s_disable_zstd_custom
