from typing import TYPE_CHECKING, List, Optional, Sequence, Type

from lonelypsp.sync_io import SyncReadableBytesIO
from lonelypsp.ws.constants import (
    BroadcasterToSubscriberWSMessageType,
    PubSubWSMessageFlags,
    SubscriberToBroadcasterWSMessageType,
)
from lonelypsp.ws.generic_parser import B2S_MessageParser, S2B_MessageParser
from lonelypsp.ws.message import S2B_Message, B2S_Message
from lonelypsp.ws.messages.configure import S2B_ConfigureParser
from lonelypsp.ws.messages.confirm_configure import B2S_ConfirmConfigureParser
from lonelypsp.ws.messages.confirm_notify import B2S_ConfirmNotifyParser
from lonelypsp.ws.messages.confirm_receive import S2B_ConfirmRecieveParser
from lonelypsp.ws.messages.confirm_subscribe import (
    B2S_ConfirmSubscribeExactParser,
    B2S_ConfirmSubscribeGlobParser,
)
from lonelypsp.ws.messages.confirm_unsubscribe import (
    B2S_ConfirmUnsubscribeExactParser,
    B2S_ConfirmUnsubscribeGlobParser,
)
from lonelypsp.ws.messages.continue_notify import B2S_ContinueNotifyParser
from lonelypsp.ws.messages.continue_receive import S2B_ContinueReceiveParser
from lonelypsp.ws.messages.enable_zstd_custom import B2S_EnableZstdCustomParser
from lonelypsp.ws.messages.enable_zstd_preset import B2S_EnableZstdPresetParser
from lonelypsp.ws.messages.notify import S2B_NotifyParser
from lonelypsp.ws.messages.notify_stream import S2B_NotifyStreamParser
from lonelypsp.ws.messages.receive_stream import B2S_ReceiveStreamParser
from lonelypsp.ws.messages.subscribe import (
    S2B_SubscribeExactParser,
    S2B_SubscribeGlobParser,
)
from lonelypsp.ws.messages.unsubscribe import (
    S2B_UnsubscribeExactParser,
    S2B_UnsubscribeGlobParser,
)


S2B_MESSAGE_PARSERS: List[Type[S2B_MessageParser[S2B_Message]]] = [
    S2B_ConfigureParser,
    S2B_ConfirmRecieveParser,
    S2B_ContinueReceiveParser,
    S2B_NotifyStreamParser,
    S2B_NotifyParser,
    S2B_SubscribeExactParser,
    S2B_SubscribeGlobParser,
    S2B_UnsubscribeExactParser,
    S2B_UnsubscribeGlobParser,
]
"""All of the message parsers for subscriber -> broadcaster messages. Generally,
easier to use via S2B_AnyMessageParser
"""

B2S_MESSAGE_PARSERS: List[Type[B2S_MessageParser[B2S_Message]]] = [
    B2S_ConfirmConfigureParser,
    B2S_ConfirmNotifyParser,
    B2S_ConfirmSubscribeExactParser,
    B2S_ConfirmSubscribeGlobParser,
    B2S_ConfirmUnsubscribeExactParser,
    B2S_ConfirmUnsubscribeGlobParser,
    B2S_ContinueNotifyParser,
    B2S_EnableZstdCustomParser,
    B2S_EnableZstdPresetParser,
    B2S_ReceiveStreamParser,
]
"""All of the message parsers for broadcaster -> subscriber messages. Generally,
easier to use via B2S_AnyMessageParser
"""


def _make_s2b_parser_lookup() -> (
    Sequence[Optional[Type[S2B_MessageParser[S2B_Message]]]]
):

    largest_type: int = 0
    total_types: int = 0
    for parser in S2B_MESSAGE_PARSERS:
        for typ in parser.relevant_types():
            if typ < 0:
                raise ValueError(f"Message type {typ} is negative")
            if typ > largest_type:
                largest_type = typ
            total_types += 1

    assert largest_type < 2 * total_types, "need to swap this implementation"

    lookup: List[Optional[Type[S2B_MessageParser[S2B_Message]]]] = [
        None for _ in range(largest_type + 1)
    ]
    for parser in S2B_MESSAGE_PARSERS:
        for message_type in parser.relevant_types():
            assert (
                lookup[message_type] is None
            ), f"{message_type} has duplicate parser (first: {lookup[message_type]}, second: {parser})"
            lookup[message_type] = parser
    return tuple(lookup)


_s2b_parser_lookup = _make_s2b_parser_lookup()


class S2B_AnyMessageParser:
    """Satisfies S2B_MessageParser[S2B_Message]"""

    @classmethod
    def relevant_types(cls) -> List[SubscriberToBroadcasterWSMessageType]:
        result = []
        for parser in S2B_MESSAGE_PARSERS:
            result.extend(parser.relevant_types())
        return result

    @classmethod
    def parse(
        cls,
        flags: PubSubWSMessageFlags,
        type: SubscriberToBroadcasterWSMessageType,
        payload: SyncReadableBytesIO,
    ) -> S2B_Message:
        if type < 0:
            raise ValueError(f"Message type {type} is negative")
        if type >= len(_s2b_parser_lookup):
            raise ValueError(f"Message type {type} is too large")
        parser = _s2b_parser_lookup[type]
        if parser is None:
            raise ValueError(f"Message type {type} is not supported")
        return parser.parse(flags, type, payload)


if TYPE_CHECKING:
    _: Type[S2B_MessageParser[S2B_Message]] = S2B_AnyMessageParser


def _make_b2s_parser_lookup() -> (
    Sequence[Optional[Type[B2S_MessageParser[B2S_Message]]]]
):
    largest_type: int = 0
    total_types: int = 0
    for parser in B2S_MESSAGE_PARSERS:
        for typ in parser.relevant_types():
            if typ < 0:
                raise ValueError(f"Message type {typ} is negative")
            if typ > largest_type:
                largest_type = typ
            total_types += 1

    assert largest_type < 2 * total_types, "need to swap this implementation"

    lookup: List[Optional[Type[B2S_MessageParser[B2S_Message]]]] = [
        None for _ in range(largest_type + 1)
    ]
    for parser in B2S_MESSAGE_PARSERS:
        for message_type in parser.relevant_types():
            assert (
                lookup[message_type] is None
            ), f"{message_type} has duplicate parser (first: {lookup[message_type]}, second: {parser})"
            lookup[message_type] = parser
    return tuple(lookup)


_b2s_parser_lookup = _make_b2s_parser_lookup()


class B2S_AnyMessageParser:
    """Satisfies B2S_MessageParser[B2S_Message]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberWSMessageType]:
        result = []
        for parser in B2S_MESSAGE_PARSERS:
            result.extend(parser.relevant_types())
        return result

    @classmethod
    def parse(
        cls,
        flags: PubSubWSMessageFlags,
        type: BroadcasterToSubscriberWSMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_Message:
        if type < 0:
            raise ValueError(f"Message type {type} is negative")
        if type >= len(_b2s_parser_lookup):
            raise ValueError(f"Message type {type} is too large")
        parser = _b2s_parser_lookup[type]
        if parser is None:
            raise ValueError(f"Message type {type} is not supported")
        return parser.parse(flags, type, payload)


if TYPE_CHECKING:
    __: Type[B2S_MessageParser[B2S_Message]] = B2S_AnyMessageParser
