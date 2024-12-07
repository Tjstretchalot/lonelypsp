from dataclasses import dataclass
from typing import Literal

from httppubsubprotocol.ws.constants import BroadcasterToSubscriberWSMessageType
from httppubsubprotocol.compat import fast_dataclass


@fast_dataclass
class B2S_EnableZstdCustom:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.ENABLE_ZSTD_CUSTOM]
    """discriminator value"""

    identifier: int
    """the identifier the broadcaster has assigned to compressing with this
    dictionary
    """

    compression_level: int
    """the compression level (any negative integer up to and including positive 22)
    that the broadcaster recommends for this dictionary; the subscriber is free to
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

    dictionary: bytes
    """the compression dictionary, in bytes, that is referenced when compressing
    with this identifier
    """
