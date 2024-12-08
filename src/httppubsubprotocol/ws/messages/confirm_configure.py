from typing import TYPE_CHECKING, Collection, List, Literal, Type, Union

from httppubsubprotocol.sync_io import SyncReadableBytesIO
from httppubsubprotocol.ws.constants import (
    BroadcasterToSubscriberWSMessageType,
    PubSubWSMessageFlags,
)
from httppubsubprotocol.compat import fast_dataclass
from httppubsubprotocol.ws.generic_parser import B2S_MessageParser
from httppubsubprotocol.ws.parser_helpers import parse_simple_headers
from httppubsubprotocol.ws.serializer_helpers import serialize_simple_message


@fast_dataclass
class B2S_ConfirmConfigure:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONFIRM_CONFIGURE]
    """discriminator value"""

    broadcaster_nonce: bytes
    """32 random bytes representing the broadcasters contribution to the connection nonce"""


_headers: Collection[str] = ("x-broadcaster-nonce",)


class B2S_ConfirmConfigureParser:
    """Satisfies B2S_MessageParser[B2S_ConfirmConfigure]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberWSMessageType]:
        return [BroadcasterToSubscriberWSMessageType.CONFIRM_CONFIGURE]

    @classmethod
    def parse(
        cls,
        flags: PubSubWSMessageFlags,
        type: BroadcasterToSubscriberWSMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_ConfirmConfigure:
        assert type == BroadcasterToSubscriberWSMessageType.CONFIRM_CONFIGURE

        headers = parse_simple_headers(flags, payload, _headers)
        broadcaster_nonce = headers["x-broadcaster-nonce"]
        if len(broadcaster_nonce) != 32:
            raise ValueError("x-broadcaster-nonce must be 32 bytes")

        return B2S_ConfirmConfigure(
            type=type,
            broadcaster_nonce=broadcaster_nonce,
        )


if TYPE_CHECKING:
    _: Type[B2S_MessageParser[B2S_ConfirmConfigure]] = B2S_ConfirmConfigureParser


def serialize_b2s_confirm_configure(
    confirm_configure: B2S_ConfirmConfigure, /, *, minimal_headers: bool
) -> Union[bytes, bytearray, memoryview]:
    return serialize_simple_message(
        type=confirm_configure.type,
        header_names=_headers,
        header_values=(confirm_configure.broadcaster_nonce,),
        payload=b"",
        minimal_headers=minimal_headers,
    )
