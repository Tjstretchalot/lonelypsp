from dataclasses import dataclass
from typing import Literal, Optional, Union

from httppubsubprotocol.ws.constants import SubscriberToBroadcasterWSMessageType
from httppubsubprotocol.compat import fast_dataclass


@fast_dataclass
class S2B_SubscribeExact:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.SUBSCRIBE_EXACT]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    topic: bytes
    """the topic to subscribe to"""


@fast_dataclass
class S2B_SubscribeGlob:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.SUBSCRIBE_GLOB]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    glob: str
    """the glob pattern to subscribe to"""


S2B_Subscribe = Union[S2B_SubscribeExact, S2B_SubscribeGlob]
