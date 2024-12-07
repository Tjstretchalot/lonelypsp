from dataclasses import dataclass
from typing import Literal

from httppubsubprotocol.ws.constants import BroadcasterToSubscriberWSMessageType
from httppubsubprotocol.compat import fast_dataclass


@fast_dataclass
class B2S_ConfirmNotify:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONFIRM_NOTIFY]
    """discriminator value"""

    identifier: bytes
    """an arbitrary identifier for the notification assigned by the subscriber; max 64 bytes
    """

    subscribers: int
    """how many subscribers were successfully notified"""
