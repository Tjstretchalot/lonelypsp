from dataclasses import dataclass
from typing import Literal, Optional

from httppubsubprotocol.ws.constants import SubscriberToBroadcasterWSMessageType
from httppubsubprotocol.compat import fast_dataclass


@fast_dataclass
class S2B_NotifyUncompressed:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.NOTIFY]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    identifier: bytes
    """an arbitrary identifier for this notification assigned by the subscriber; max 64 bytes
    """

    compressor_id: Literal[None]
    """discriminator value. We reinterpret a compressor id of 0 to None as we cannot
    type "strictly positive integers" in python for the counterpart to `Literal[0]`
    """

    topic: bytes
    """the topic of the message"""

    verified_uncompressed_sha512: bytes
    """The sha512 hash of the uncompressed message, 64 bytes, verified"""

    uncompressed_message: bytes
    """The message in uncompressed form"""


@fast_dataclass
class S2B_NotifyCompressed:
    """
    S2B = Subscriber to Broadcaster
    See the type enum documentation for more information on the fields
    """

    type: Literal[SubscriberToBroadcasterWSMessageType.NOTIFY]
    """discriminator value"""

    authorization: Optional[str]
    """url: websocket:<nonce>:<ctr>
    
    an empty string is reinterpreted as None for consistency between
    minimal headers mode and expanded headers mode
    """

    identifier: bytes
    """an arbitrary identifier for this notification assigned by the subscriber; max 64 bytes
    """

    compressor_id: int
    """the id of the compressor used to compress the message"""

    topic: bytes
    """the topic of the message"""

    verified_compressed_sha512: bytes
    """The sha512 hash of the compressed message, 64 bytes, verified"""

    compressed_message: bytes
    """The message in compressed form"""

    decompressed_length: int
    """The expected, but unverified, length of the message after decompression"""
