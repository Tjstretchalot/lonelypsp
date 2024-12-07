from dataclasses import dataclass
from typing import Literal, Union

from httppubsubprotocol.ws.constants import BroadcasterToSubscriberWSMessageType


@dataclass(frozen=True, slots=True)
class B2S_ConfirmUnsubscribeExact:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONFIRM_UNSUBSCRIBE_EXACT]
    """discriminator value"""

    topic: bytes
    """the topic the subscriber is no longer subscribed to"""


@dataclass(frozen=True, slots=True)
class B2S_ConfirmUnsubscribeGlob:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONFIRM_UNSUBSCRIBE_GLOB]
    """discriminator value"""

    glob: str
    """the glob pattern the subscriber is no longer subscribed to"""


B2S_ConfirmUnsubscribe = Union[B2S_ConfirmUnsubscribeExact, B2S_ConfirmUnsubscribeGlob]
