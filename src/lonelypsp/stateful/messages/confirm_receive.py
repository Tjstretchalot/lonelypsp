from typing import TYPE_CHECKING, Collection, List, Literal, Optional, Type, Union

from lonelypsp.compat import fast_dataclass
from lonelypsp.stateful.constants import (
    PubSubStatefulMessageFlags,
    SubscriberToBroadcasterStatefulMessageType,
)
from lonelypsp.stateful.generic_parser import S2B_MessageParser
from lonelypsp.stateful.parser_helpers import parse_simple_headers
from lonelypsp.stateful.serializer_helpers import (
    MessageSerializer,
    serialize_simple_message,
)
from lonelypsp.sync_io import SyncReadableBytesIO


@fast_dataclass
class S2B_ConfirmReceive:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterStatefulMessageType.CONFIRM_RECEIVE]
    """discriminator value"""

    identifier: bytes
    """an arbitrary identifier for the notification assigned by the broadcaster; max 64 bytes
    """

    authorization: Optional[str]
    """the authorization header that shows the confirmation was sent by the subscriber
    that was contacted
    
    empty strings are converted to None for consistency with http endpoints
    """

    tracing: bytes
    """the tracing data, which may be empty"""

    num_subscribers: int
    """the number of subscribers that received the message; usually 1, but can be more
    when this subscriber is acting as a relay
    """


_headers: Collection[str] = (
    "x-identifier",
    "authorization",
    "x-tracing",
    "x-num-subscribers",
)


class S2B_ConfirmRecieveParser:
    """Satisfies S2B_MessageParser[S2B_ConfirmReceive]"""

    @classmethod
    def relevant_types(cls) -> List[SubscriberToBroadcasterStatefulMessageType]:
        return [SubscriberToBroadcasterStatefulMessageType.CONFIRM_RECEIVE]

    @classmethod
    def parse(
        cls,
        flags: PubSubStatefulMessageFlags,
        type: SubscriberToBroadcasterStatefulMessageType,
        payload: SyncReadableBytesIO,
    ) -> S2B_ConfirmReceive:
        assert type == SubscriberToBroadcasterStatefulMessageType.CONFIRM_RECEIVE

        headers = parse_simple_headers(flags, payload, _headers)
        identifier = headers["x-identifier"]
        if len(identifier) > 64:
            raise ValueError("x-identifier must be at most 64 bytes")

        authorization_bytes = headers["authorization"]
        authorization: Optional[str] = None
        if authorization_bytes != b"":
            try:
                authorization = authorization_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("authorization must be a utf-8 string")

        tracing = headers["x-tracing"]
        num_subscribers_bytes = headers["x-num-subscribers"]
        if len(num_subscribers_bytes) > 4:
            raise ValueError("x-num-subscribers must be at most 4 bytes")
        num_subscribers = int.from_bytes(num_subscribers_bytes, "big")

        return S2B_ConfirmReceive(
            type=type,
            identifier=identifier,
            authorization=authorization,
            tracing=tracing,
            num_subscribers=num_subscribers,
        )


if TYPE_CHECKING:
    _: Type[S2B_MessageParser[S2B_ConfirmReceive]] = S2B_ConfirmRecieveParser


def serialize_s2b_confirm_receive(
    msg: S2B_ConfirmReceive, /, *, minimal_headers: bool
) -> Union[bytes, bytearray]:
    """Satisfies MessageSerializer[S2B_ConfirmReceive]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_headers,
        header_values=(
            msg.identifier,
            msg.authorization.encode("utf-8") if msg.authorization is not None else b"",
            msg.tracing,
            msg.num_subscribers.to_bytes(4, "big"),
        ),
        payload=b"",
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[S2B_ConfirmReceive] = serialize_s2b_confirm_receive
