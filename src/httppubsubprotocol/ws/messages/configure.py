from dataclasses import dataclass
from typing import Literal

from httppubsubprotocol.ws.constants import SubscriberToBroadcasterWSMessageType


@dataclass
class S2B_Configure:
    """
    S2B = Subscriber to Broadcaster

    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.CONFIGURE]
    """discriminator value"""

    subscriber_nonce: bytes
    """32 random bytes representing the subscriber's contribution to the nonce"""

    enable_zstd: bool
    """if the client is willing to receive zstandard compressed messages"""

    enable_training: bool
    """if the client may accept custom compression dictionaries"""
