from dataclasses import dataclass
from typing import Literal, Optional, Union

from httppubsubprotocol.ws.constants import SubscriberToBroadcasterWSMessageType


@dataclass(frozen=True, slots=True)
class S2B_UnsubscribeExact:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.UNSUBSCRIBE_EXACT]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    topic: bytes
    """the topic to unsubscribe from"""


@dataclass(frozen=True, slots=True)
class S2B_UnsubscribeGlob:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.UNSUBSCRIBE_GLOB]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    glob: str
    """the glob pattern to unsubscribe from"""


S2B_Unsubscribe = Union[S2B_UnsubscribeExact, S2B_UnsubscribeGlob]
