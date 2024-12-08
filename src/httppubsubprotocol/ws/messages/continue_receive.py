from dataclasses import dataclass
from typing import TYPE_CHECKING, Collection, List, Literal, Type, Union

from httppubsubprotocol.sync_io import SyncReadableBytesIO
from httppubsubprotocol.ws.constants import (
    PubSubWSMessageFlags,
    SubscriberToBroadcasterWSMessageType,
)
from httppubsubprotocol.compat import fast_dataclass
from httppubsubprotocol.ws.generic_parser import S2B_MessageParser
from httppubsubprotocol.ws.parser_helpers import parse_simple_headers
from httppubsubprotocol.ws.serializer_helpers import (
    MessageSerializer,
    int_to_minimal_unsigned,
    serialize_simple_message,
)


@fast_dataclass
class S2B_ContinueReceive:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.CONTINUE_RECEIVE]
    """discriminator value"""

    identifier: bytes
    """an arbitrary identifier for the notification assigned by the broadcaster; max 64 bytes
    """

    part_id: int
    """which part the subscriber received; acknowledgments must always be in order"""


_headers: Collection[str] = ("x-identifier", "x-part-id")


class S2B_ContinueReceiveParser:
    """Satisfies S2B_MessageParser[S2B_ContinueReceive]"""

    @classmethod
    def relevant_types(cls) -> List[SubscriberToBroadcasterWSMessageType]:
        return [SubscriberToBroadcasterWSMessageType.CONTINUE_RECEIVE]

    @classmethod
    def parse(
        cls,
        flags: PubSubWSMessageFlags,
        type: SubscriberToBroadcasterWSMessageType,
        payload: SyncReadableBytesIO,
    ) -> S2B_ContinueReceive:
        assert type == SubscriberToBroadcasterWSMessageType.CONTINUE_RECEIVE

        headers = parse_simple_headers(flags, payload, _headers)
        identifier = headers["x-identifier"]
        if len(identifier) > 64:
            raise ValueError("x-identifier must be at most 64 bytes")

        part_id_bytes = headers["x-part-id"]
        if len(part_id_bytes) > 8:
            raise ValueError("x-part-id must be at most 8 bytes")

        part_id = int.from_bytes(part_id_bytes)

        return S2B_ContinueReceive(
            type=type,
            identifier=identifier,
            part_id=part_id,
        )


if TYPE_CHECKING:
    _: Type[S2B_MessageParser[S2B_ContinueReceive]] = S2B_ContinueReceiveParser


def serialize_s2b_continue_receive(
    msg: S2B_ContinueReceive, /, *, minimal_headers: bool
) -> Union[bytes, bytearray, memoryview]:
    """Satisfies MessageSerializer[B2S_ContinueNotify]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_headers,
        header_values=(msg.identifier, int_to_minimal_unsigned(msg.part_id)),
        payload=b"",
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[S2B_ContinueReceive] = serialize_s2b_continue_receive
