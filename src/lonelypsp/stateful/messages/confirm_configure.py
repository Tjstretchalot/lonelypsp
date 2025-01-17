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
    serialize_simple_message,
)
from lonelypsp.sync_io import SyncReadableBytesIO


@fast_dataclass
class B2S_ConfirmConfigure:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberStatefulMessageType.CONFIRM_CONFIGURE]
    """discriminator value"""

    broadcaster_nonce: bytes
    """32 random bytes representing the broadcasters contribution to the connection nonce"""

    authorization: Optional[str]
    """variable length proof that the broadcaster is allowed to serve the subscriber
    
    empty strings are converted to None for consistency with http endpoints
    """

    tracing: bytes
    """the tracing data, which may be empty"""


_headers: Collection[str] = ("x-broadcaster-nonce", "authorization", "x-tracing")


class B2S_ConfirmConfigureParser:
    """Satisfies B2S_MessageParser[B2S_ConfirmConfigure]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberStatefulMessageType]:
        return [BroadcasterToSubscriberStatefulMessageType.CONFIRM_CONFIGURE]

    @classmethod
    def parse(
        cls,
        flags: PubSubStatefulMessageFlags,
        type: BroadcasterToSubscriberStatefulMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_ConfirmConfigure:
        assert type == BroadcasterToSubscriberStatefulMessageType.CONFIRM_CONFIGURE

        headers = parse_simple_headers(flags, payload, _headers)
        broadcaster_nonce = headers["x-broadcaster-nonce"]
        if len(broadcaster_nonce) != 32:
            raise ValueError("x-broadcaster-nonce must be 32 bytes")

        authorization_bytes = headers["authorization"]
        authorization: Optional[str] = None
        if authorization_bytes != b"":
            try:
                authorization = authorization_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("authorization must be a utf-8 string")

        tracing: bytes = headers["x-tracing"]

        return B2S_ConfirmConfigure(
            type=type,
            broadcaster_nonce=broadcaster_nonce,
            authorization=authorization,
            tracing=tracing,
        )


if TYPE_CHECKING:
    _: Type[B2S_MessageParser[B2S_ConfirmConfigure]] = B2S_ConfirmConfigureParser


def serialize_b2s_confirm_configure(
    msg: B2S_ConfirmConfigure, /, *, minimal_headers: bool
) -> Union[bytes, bytearray]:
    """Satisfies MessageSerializer[B2S_ConfirmConfigure]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_headers,
        header_values=(
            msg.broadcaster_nonce,
            msg.authorization.encode("utf-8") if msg.authorization is not None else b"",
            msg.tracing,
        ),
        payload=b"",
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[B2S_ConfirmConfigure] = serialize_b2s_confirm_configure
