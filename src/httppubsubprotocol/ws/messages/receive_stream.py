from dataclasses import dataclass
from typing import Literal, Optional, Union

from httppubsubprotocol.ws.constants import BroadcasterToSubscriberWSMessageType


@dataclass
class B2S_ReceiveStreamStartUncompressed:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields

    This type is for when x-part-id is 0 and x-compressor is 0
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.RECEIVE_STREAM]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    identifier: bytes
    """an arbitrary identifier for this notification assigned by the broadcaster; max 64 bytes
    """

    part_id: Literal[None]
    """discriminator value. We reinterpret a part id of 0 to None as we cannot
    type "strictly positive integers" in python for the counterpart to `Literal[0]`
    """

    compressor_id: Literal[None]
    """discriminator value. We reinterpret a compressor id of 0 to None as we cannot
    type "strictly positive integers" in python for the counterpart to `Literal[0]`
    """

    uncompressed_length: int
    """the number of bytes that comprise the notification body"""

    unverified_uncompressed_sha512: bytes
    """The unverified sha512 hash of the entire uncompressed notification body, 64 bytes"""

    payload: bytes
    """The first part of the notification in uncompressed form"""


@dataclass
class B2S_ReceiveStreamStartCompressed:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields

    This type is for when x-part-id is 0 and x-compressor is not 0
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.RECEIVE_STREAM]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    identifier: bytes
    """an arbitrary identifier for this notification assigned by the broadcaster; max 64 bytes
    """

    part_id: Literal[None]
    """discriminator value. We reinterpret a part id of 0 to None as we cannot
    type "strictly positive integers" in python for the counterpart to `Literal[0]`
    """

    compressor_id: int
    """a positive value indicating which compressor was used to compress the message"""

    compressed_length: int
    """the number of bytes that comprise the compressed notification body"""

    decompressed_length: int
    """when decompressing the compressed data, the number of bytes that should be produced"""

    unverified_compressed_sha512: bytes
    """the unverified sha512 hash of the entire compressed notification body, 64 bytes"""

    payload: bytes
    """the first part of the notification in compressed form; the compression is over the
    entire notification body, so this is probably not decompressible by itself
    """


@dataclass
class B2S_ReceiveStreamContinuation:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields

    This type is for when x-part-id is not 0
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.RECEIVE_STREAM]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    identifier: bytes
    """an arbitrary identifier for this notification assigned by the broadcaster; max 64 bytes
    """

    part_id: int
    """a positive value indicating the part number of the message. never sent out of order"""

    payload: bytes
    """the additional payload data for the notification"""


B2S_ReceiveStream = Union[
    B2S_ReceiveStreamStartUncompressed,
    B2S_ReceiveStreamStartCompressed,
    B2S_ReceiveStreamContinuation,
]
