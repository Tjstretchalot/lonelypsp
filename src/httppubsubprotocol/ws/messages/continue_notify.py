from dataclasses import dataclass
from typing import Literal

from httppubsubprotocol.ws.constants import BroadcasterToSubscriberWSMessageType


@dataclass
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
