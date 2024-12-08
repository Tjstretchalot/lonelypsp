from typing import Union

from httppubsubprotocol.ws.messages.configure import S2B_Configure
from httppubsubprotocol.ws.messages.confirm_configure import B2S_ConfirmConfigure
from httppubsubprotocol.ws.messages.confirm_notify import B2S_ConfirmNotify
from httppubsubprotocol.ws.messages.confirm_receive import S2B_ConfirmReceive
from httppubsubprotocol.ws.messages.confirm_subscribe import (
    B2S_ConfirmSubscribeExact,
    B2S_ConfirmSubscribeGlob,
)
from httppubsubprotocol.ws.messages.confirm_unsubscribe import (
    B2S_ConfirmUnsubscribeExact,
    B2S_ConfirmUnsubscribeGlob,
)
from httppubsubprotocol.ws.messages.continue_notify import B2S_ContinueNotify
from httppubsubprotocol.ws.messages.continue_receive import S2B_ContinueReceive
from httppubsubprotocol.ws.messages.enable_zstd_custom import B2S_EnableZstdCustom
from httppubsubprotocol.ws.messages.enable_zstd_preset import B2S_EnableZstdPreset
from httppubsubprotocol.ws.messages.notify_stream import S2B_NotifyStream
from httppubsubprotocol.ws.messages.notify import S2B_Notify
from httppubsubprotocol.ws.messages.receive_stream import B2S_ReceiveStream
from httppubsubprotocol.ws.messages.subscribe import (
    S2B_SubscribeExact,
    S2B_SubscribeGlob,
)
from httppubsubprotocol.ws.messages.unsubscribe import (
    S2B_UnsubscribeExact,
    S2B_UnsubscribeGlob,
)


S2B_Message = Union[
    S2B_Configure,
    S2B_ConfirmReceive,
    S2B_ContinueReceive,
    S2B_NotifyStream,
    S2B_Notify,
    S2B_SubscribeExact,
    S2B_SubscribeGlob,
    S2B_UnsubscribeExact,
    S2B_UnsubscribeGlob,
]
"""Type alias for any message from a subscriber to a broadcaster"""

B2S_Message = Union[
    B2S_ConfirmConfigure,
    B2S_ConfirmNotify,
    B2S_ConfirmSubscribeExact,
    B2S_ConfirmSubscribeGlob,
    B2S_ConfirmUnsubscribeExact,
    B2S_ConfirmUnsubscribeGlob,
    B2S_ContinueNotify,
    B2S_EnableZstdCustom,
    B2S_EnableZstdPreset,
    B2S_ReceiveStream,
]
"""Type alias for any message from a broadcaster to a subscriber"""
