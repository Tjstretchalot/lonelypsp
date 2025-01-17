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
    int_to_minimal_unsigned,
    serialize_simple_message,
)
from lonelypsp.sync_io import SyncReadableBytesIO


@fast_dataclass
class S2B_ContinueReceive:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterStatefulMessageType.CONTINUE_RECEIVE]
    """discriminator value"""

    identifier: bytes
    """an arbitrary identifier for the notification assigned by the broadcaster; max 64 bytes
    """

    part_id: int
    """which part the subscriber received; acknowledgments must always be in order"""

    authorization: Optional[str]
    """the authorization header that shows the confirmation was sent by the subscriber

    empty strings are converted to None for consistency with http endpoints
    """

    tracing: bytes


_headers: Collection[str] = ("x-identifier", "x-part-id", "authorization", "x-tracing")


class S2B_ContinueReceiveParser:
    """Satisfies S2B_MessageParser[S2B_ContinueReceive]"""

    @classmethod
    def relevant_types(cls) -> List[SubscriberToBroadcasterStatefulMessageType]:
        return [SubscriberToBroadcasterStatefulMessageType.CONTINUE_RECEIVE]

    @classmethod
    def parse(
        cls,
        flags: PubSubStatefulMessageFlags,
        type: SubscriberToBroadcasterStatefulMessageType,
        payload: SyncReadableBytesIO,
    ) -> S2B_ContinueReceive:
        assert type == SubscriberToBroadcasterStatefulMessageType.CONTINUE_RECEIVE

        headers = parse_simple_headers(flags, payload, _headers)
        identifier = headers["x-identifier"]
        if len(identifier) > 64:
            raise ValueError("x-identifier must be at most 64 bytes")

        part_id_bytes = headers["x-part-id"]
        if len(part_id_bytes) > 8:
            raise ValueError("x-part-id must be at most 8 bytes")

        part_id = int.from_bytes(part_id_bytes, "big")

        authorization_bytes = headers["authorization"]
        authorization: Optional[str] = None
        if authorization_bytes != b"":
            try:
                authorization = authorization_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("authorization must be a utf-8 string")

        tracing = headers["x-tracing"]

        return S2B_ContinueReceive(
            type=type,
            identifier=identifier,
            part_id=part_id,
            authorization=authorization,
            tracing=tracing,
        )


if TYPE_CHECKING:
    _: Type[S2B_MessageParser[S2B_ContinueReceive]] = S2B_ContinueReceiveParser


def serialize_s2b_continue_receive(
    msg: S2B_ContinueReceive, /, *, minimal_headers: bool
) -> Union[bytes, bytearray]:
    """Satisfies MessageSerializer[B2S_ContinueNotify]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_headers,
        header_values=(
            msg.identifier,
            int_to_minimal_unsigned(msg.part_id),
            msg.authorization.encode("utf-8") if msg.authorization is not None else b"",
            msg.tracing,
        ),
        payload=b"",
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[S2B_ContinueReceive] = serialize_s2b_continue_receive
