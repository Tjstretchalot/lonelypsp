import time

from lonelypsp.compat import fast_dataclass


@fast_dataclass
class CristiansStart:
    """The data stored by the initiator"""

    request_sent_at_nano: int


@fast_dataclass
class CristiansResponse:
    """The data sent by the receiver"""

    request_received_at_nano: int
    response_sent_at_nano: int


@fast_dataclass
class CristiansEnd:
    """The data stored by the initiator"""

    request_sent_at_local_nano: int
    request_received_at_remote_nano: int
    response_sent_at_remote_nano: int
    response_received_at_local_nano: int


@fast_dataclass
class CristiansOffset:
    """The offset calculated from the Cristian's algorithm"""

    latency: float
    """estimated one-way latency in milliseconds"""

    offset: float
    """estimated offset of the remote clock compared to the local clock, in milliseconds
    ```
    remote_time - local_time = offset
    local_time = remote_time - offset
    ```
    """


def finish_cristians(
    start: CristiansStart, response: CristiansResponse
) -> CristiansEnd:
    """Finishes the Cristian's algorithm"""
    return CristiansEnd(
        request_sent_at_local_nano=start.request_sent_at_nano,
        request_received_at_remote_nano=response.request_received_at_nano,
        response_sent_at_remote_nano=response.response_sent_at_nano,
        response_received_at_local_nano=time.time_ns(),
    )


def compute_offset(cristians_end: CristiansEnd) -> CristiansOffset:
    """Computes the offset from the Cristian's algorithm"""
    time_processing_nano = (
        cristians_end.response_received_at_local_nano
        - cristians_end.request_sent_at_local_nano
    )
    round_trip_time_nano = (
        cristians_end.response_received_at_local_nano
        - cristians_end.request_sent_at_local_nano
        - time_processing_nano
    )
    latency_nano = round_trip_time_nano / 2
    request_received_at_local_nano = (
        cristians_end.request_sent_at_local_nano + latency_nano
    )
    offset_nano = (
        cristians_end.request_received_at_remote_nano - request_received_at_local_nano
    )
    return CristiansOffset(
        latency=latency_nano / 1_000_000, offset=offset_nano / 1_000_000
    )
