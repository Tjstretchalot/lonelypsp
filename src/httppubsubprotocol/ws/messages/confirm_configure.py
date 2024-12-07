from dataclasses import dataclass
from typing import Literal

from httppubsubprotocol.ws.constants import BroadcasterToSubscriberWSMessageType
from httppubsubprotocol.compat import fast_dataclass


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
