from typing import Collection, Union
from httppubsubprotocol.sync_io import PreallocatedBytesIO, SyncWritableBytesIO
from httppubsubprotocol.ws.constants import (
    BroadcasterToSubscriberWSMessageType,
    PubSubWSMessageFlags,
    SubscriberToBroadcasterWSMessageType,
)


def serialize_prefix(
    out: SyncWritableBytesIO,
    type: Union[
        SubscriberToBroadcasterWSMessageType, BroadcasterToSubscriberWSMessageType
    ],
    /,
    *,
    minimal_headers: bool,
) -> None:
    """Writes the message flags and the type of message to the output stream."""
    out.write(
        int.to_bytes(
            PubSubWSMessageFlags.MINIMAL_HEADERS if minimal_headers else 0, 2, "big"
        )
    )
    out.write(int.to_bytes(type, 2, "big"))


def serialize_minimal_headers(
    out: SyncWritableBytesIO, values: Collection[bytes]
) -> None:
    """Writes the header values to the output stream, in minimal headers mode.

    Minimal headers does not get prefixed with the number of headers and the
    name of the headers is implicit from their order, thus this can be called
    multiple times to write multiple headers.
    """
    for value in values:
        out.write(int.to_bytes(len(value), 2, "big"))
        out.write(value)


def serialize_expanded_headers(
    out: SyncWritableBytesIO,
    header_names: Collection[str],
    header_values: Collection[bytes],
    /,
) -> None:
    """Writes the header values to the output stream, in expanded headers mode.

    Expanded headers get prefixed with the number of headers and the name of
    the headers, thus this can be called only once to write all headers.
    """
    assert len(header_names) == len(header_values)
    out.write(int.to_bytes(len(header_names), 2, "big"))
    for name, value in zip(header_names, header_values):
        out.write(int.to_bytes(len(name), 2, "big"))
        out.write(name.encode("ascii"))
        out.write(int.to_bytes(len(value), 2, "big"))
        out.write(value)


def serialize_simple_headers(
    out: SyncWritableBytesIO,
    header_names: Collection[str],
    header_values: Collection[bytes],
    /,
    *,
    minimal: bool,
) -> None:
    """Writes the given headers for the contents of a websocket message
    to the output stream in the appropriate mode.
    """

    if minimal:
        serialize_minimal_headers(out, header_values)
    else:
        serialize_expanded_headers(out, header_names, header_values)


def serialize_simple_message(
    *,
    type: Union[
        SubscriberToBroadcasterWSMessageType, BroadcasterToSubscriberWSMessageType
    ],
    header_names: Collection[str],
    header_values: Collection[bytes],
    payload: bytes,
    minimal_headers: bool,
) -> Union[bytes, bytearray, memoryview]:
    """Serializes the entire contents of a websocket message with the given
    type, headers, and payload, returning the bytes contents to send along
    the websocket
    """
    assert len(header_names) == len(header_values)
    total_size = (
        2  # flags
        + 2  # type
        + (  # headers
            2 * len(header_values) + sum(len(value) for value in header_values)
            if minimal_headers
            else 2
            + 4 * len(header_values)
            + sum(len(name.encode("ascii")) for name in header_names)
            + sum(len(value) for value in header_values)
        )
        + len(payload)
    )

    out = PreallocatedBytesIO(total_size)
    serialize_prefix(out, type, minimal_headers=minimal_headers)
    serialize_simple_headers(out, header_names, header_values, minimal=minimal_headers)
    out.write(payload)
    assert out.tell() == total_size
    return out.buffer
