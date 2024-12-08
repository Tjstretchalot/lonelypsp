from typing import TYPE_CHECKING, Collection, List, Literal, Type, Union

from httppubsubprotocol.sync_io import SyncReadableBytesIO
from httppubsubprotocol.ws.constants import (
    BroadcasterToSubscriberWSMessageType,
    PubSubWSMessageFlags,
)
from httppubsubprotocol.compat import fast_dataclass
from httppubsubprotocol.ws.generic_parser import B2S_MessageParser
from httppubsubprotocol.ws.parser_helpers import parse_simple_headers
from httppubsubprotocol.ws.serializer_helpers import (
    MessageSerializer,
    int_to_minimal_unsigned,
    serialize_simple_message,
)


@fast_dataclass
class B2S_ContinueNotify:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONTINUE_NOTIFY]
    """discriminator value"""

    identifier: bytes
    """an arbitrary identifier for the notification assigned by the subscriber; max 64 bytes
    """

    part_id: int
    """the part id the broadcaster received; they are expecting the next part after this"""


_headers: Collection[str] = ("x-identifier", "x-part-id")


class B2S_ContinueNotifyParser:
    """Satisfies B2S_MessageParser[B2S_ContinueNotify]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberWSMessageType]:
        return [BroadcasterToSubscriberWSMessageType.CONTINUE_NOTIFY]

    @classmethod
    def parse(
        cls,
        flags: PubSubWSMessageFlags,
        type: BroadcasterToSubscriberWSMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_ContinueNotify:
        assert type == BroadcasterToSubscriberWSMessageType.CONTINUE_NOTIFY

        headers = parse_simple_headers(flags, payload, _headers)
        identifier = headers["x-identifier"]
        if len(identifier) > 64:
            raise ValueError("x-identifier must be at most 64 bytes")

        part_id_bytes = headers["x-part-id"]
        if len(part_id_bytes) > 8:
            raise ValueError("x-part-id must be at most 8 bytes")

        part_id = int.from_bytes(part_id_bytes, "big")

        return B2S_ContinueNotify(
            type=type,
            identifier=identifier,
            part_id=part_id,
        )


if TYPE_CHECKING:
    _: Type[B2S_MessageParser[B2S_ContinueNotify]] = B2S_ContinueNotifyParser


def serialize_b2s_continue_notify(
    msg: B2S_ContinueNotify, /, *, minimal_headers: bool
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
    __: MessageSerializer[B2S_ContinueNotify] = serialize_b2s_continue_notify
