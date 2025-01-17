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
class B2S_Missed:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberStatefulMessageType.MISSED]
    """discriminator value"""

    authorization: Optional[str]
    """recovery: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    tracing: bytes
    """the tracing data, which may be empty"""

    topic: bytes
    """the topic the possibly missed message was sent to"""


_headers: Collection[str] = (
    "authorization",
    "x-tracing",
    "x-topic",
)


class B2S_MissedParser:
    """Satisfies B2S_MessageParser[B2S_Missed]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberStatefulMessageType]:
        return [BroadcasterToSubscriberStatefulMessageType.MISSED]

    @classmethod
    def parse(
        cls,
        flags: PubSubStatefulMessageFlags,
        type: BroadcasterToSubscriberStatefulMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_Missed:
        assert type == BroadcasterToSubscriberStatefulMessageType.MISSED

        headers = parse_simple_headers(flags, payload, _headers)

        authorization_bytes = headers["authorization"]
        authorization: Optional[str] = None
        if authorization_bytes != b"":
            try:
                authorization = authorization_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("authorization must be a utf-8 string")

        tracing = headers["x-tracing"]
        topic = headers["x-topic"]

        return B2S_Missed(
            type=type,
            authorization=authorization,
            tracing=tracing,
            topic=topic,
        )


if TYPE_CHECKING:
    _: Type[B2S_MessageParser[B2S_Missed]] = B2S_MissedParser


def serialize_b2s_missed(
    msg: B2S_Missed, /, *, minimal_headers: bool
) -> Union[bytes, bytearray]:
    """Satisfies MessageSerializer[B2S_Missed]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_headers,
        header_values=(
            msg.authorization.encode("utf-8") if msg.authorization is not None else b"",
            msg.tracing,
            msg.topic,
        ),
        payload=b"",
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[B2S_Missed] = serialize_b2s_missed
