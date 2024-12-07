from dataclasses import dataclass
from typing import Literal

from httppubsubprotocol.ws.constants import BroadcasterToSubscriberWSMessageType


@dataclass(frozen=True, slots=True)
class B2S_EnableZstdPreset:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.ENABLE_ZSTD_PRESET]
    """discriminator value"""

    identifier: int
    """the agreed upon identifier for this preset; 1 always means compression
    without a custom dictionary (i.e., the dictionary is sent alongside the
    compressed data)
    """

    compression_level: int
    """the compression level (any negative integer up to and including positive 22)
    that the broadcaster recommends for this preset; the subscriber is free to
    ignore this recommendation
    """

    min_size: int
    """the minimum in size in bytes that the broadcaster recommends for using
    this preset; the subscriber is free to ignore this recommendation
    """

    max_size: int
    """the maximum in size in bytes that the broadcaster recommends for using
    this preset; the subscriber is free to ignore this recommendation. 2**64-1
    for no limit
    """
