from dataclasses import dataclass
from typing import Literal, Union

from httppubsubprotocol.ws.constants import BroadcasterToSubscriberWSMessageType


@dataclass(frozen=True, slots=True)
class B2S_ConfirmSubscribeExact:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONFIRM_SUBSCRIBE_EXACT]
    """discriminator value"""

    topic: bytes
    """the topic the subscriber is now subscribed to"""


@dataclass(frozen=True, slots=True)
class B2S_ConfirmSubscribeGlob:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONFIRM_SUBSCRIBE_GLOB]
    """discriminator value"""

    glob: str
    """the glob pattern whose matching topics the subscriber is now subscribed to"""


B2S_ConfirmSubscribe = Union[B2S_ConfirmSubscribeExact, B2S_ConfirmSubscribeGlob]
