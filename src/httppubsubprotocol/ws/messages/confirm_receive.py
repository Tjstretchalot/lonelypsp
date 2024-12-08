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
    serialize_simple_message,
)


@fast_dataclass
class S2B_ConfirmReceive:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.CONFIRM_RECEIVE]
    """discriminator value"""

    identifier: bytes
    """an arbitrary identifier for the notification assigned by the broadcaster; max 64 bytes
    """


_headers: Collection[str] = ("x-identifier",)


class S2B_ConfirmRecieveParser:
    """Satisfies S2B_MessageParser[S2B_ConfirmReceive]"""

    @classmethod
    def relevant_types(cls) -> List[SubscriberToBroadcasterWSMessageType]:
        return [SubscriberToBroadcasterWSMessageType.CONFIRM_RECEIVE]

    @classmethod
    def parse(
        cls,
        flags: PubSubWSMessageFlags,
        type: SubscriberToBroadcasterWSMessageType,
        payload: SyncReadableBytesIO,
    ) -> S2B_ConfirmReceive:
        assert type == SubscriberToBroadcasterWSMessageType.CONFIRM_RECEIVE

        headers = parse_simple_headers(flags, payload, _headers)
        identifier = headers["x-identifier"]
        if len(identifier) > 64:
            raise ValueError("x-identifier must be at most 64 bytes")

        return S2B_ConfirmReceive(
            type=type,
            identifier=identifier,
        )


if TYPE_CHECKING:
    _: Type[S2B_MessageParser[S2B_ConfirmReceive]] = S2B_ConfirmRecieveParser


def serialize_s2b_confirm_receive(
    msg: S2B_ConfirmReceive, /, *, minimal_headers: bool
) -> Union[bytes, bytearray, memoryview]:
    """Satisfies MessageSerializer[S2B_ConfirmReceive]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_headers,
        header_values=(msg.identifier,),
        payload=b"",
        minimal_headers=minimal_headers,
    )


if TYPE_CHECKING:
    __: MessageSerializer[S2B_ConfirmReceive] = serialize_s2b_confirm_receive
