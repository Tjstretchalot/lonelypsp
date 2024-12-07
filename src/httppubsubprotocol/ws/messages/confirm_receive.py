from dataclasses import dataclass
from typing import Literal

from httppubsubprotocol.ws.constants import SubscriberToBroadcasterWSMessageType


@dataclass(frozen=True, slots=True)
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
