from types import TracebackType
from typing import Optional, Protocol, Type

from lonelypsp.auth.config import BadAuthResult
from lonelypsp.tracing.shared.handle_trusted_notify import HandledTrustedNotify
from lonelypsp.tracing.shared.tracing_and_followup import TracingAndFollowup


class StatelessTracingNotifyStart(Protocol):
    """Entry context manager for the subscriber side of a NOTIFY"""

    def __enter__(self) -> "StatelessTracingNotifyStartFirst":
        """Called to initialize the trace on the subscriber side for a NOTIFY"""

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Called when the subscriber side of this trace is completely done, which
        may be due to cancellation, on a best-effort basis (i.e., as good as
        `with` could do but not better)
        """


class StatelessTracingNotifyStartFirst(Protocol):
    """First object run on the subscriber (and overall)"""

    def on_start_without_hash(
        self, /, *, topic: bytes, length: int, filelike: bool
    ) -> "StatelessTracingNotifyOnHashed":
        """Called immediately after the `lonelypsc` library is told to make
        a NOTIFY call, given that the client did not provide the sha512 hash (so
        lonelypsc needs to compute it)

        Args:
            topic (bytes): the topic to write to
            length (int): the length of the data to write
            filelike (bool): whether the data is provided as a file-like object (True)
                or as a bytes object (False). When given a bytes object all operations
                are performed in memory regardless of the length

        Returns:
            StatelessTracingNotifyOnHashed: the next object to use
        """

    def on_start_with_hash(
        self, /, *, topic: bytes, length: int, filelike: bool
    ) -> "StatelessTracingNotifyOnSending":
        """Called immediately after the `lonelypsc` library is told to make
        a NOTIFY call, given that the client provided the sha512 hash (so
        lonelypsc does not need to compute it)

        Args:
            topic (bytes): the topic to write to
            length (int): the length of the data to write
            filelike (bool): whether the data is provided as a file-like object (True)
                or as a bytes object (False). When given a bytes object all operations
                are performed in memory regardless of the length

        Returns:
            StatelessTracingNotifyOnSending: the next object to use
        """


class StatelessTracingNotifyOnHashed(Protocol):
    """Run on the subscriber, omitted if the hash was provided to lonelypsc"""

    def on_hashed(self) -> "StatelessTracingNotifyOnSending":
        """Called after the lonelypsc library has finished computing the hash
        of the message and is moving to getting ready to send the message to
        the server
        """


class StatelessTracingNotifyOnSending(Protocol):
    """Run on the subscriber immediately prior to transferring to the broadcaster"""

    def on_sending_request(
        self, /, *, broadcaster: str, identifier: bytes
    ) -> TracingAndFollowup["StatelessTracingNotifyOnResponseReceived"]:
        """Called immediately prior to the subscriber sending the request to
        the broadcaster. Must return the tracing data to send to the broadcaster
        to pick up

        Args:
            broadcaster (str): the broadcaster to send the request to
            identifier (bytes): the arbitrary identifier the subscriber assigned
                to this request; this will be passed to the broadcaster without
                having to store it in the tracing data, and can be assumed to
                be globally unique

        Returns:
            tracing: the tracing data to send, max 2^16-1 bytes, may be empty
            followup: the next object on the subscriber side
        """


class StatelessTracingNotifyOnReceived(Protocol):
    """Entry context manager for the broadcaster side of a NOTIFY"""

    def __enter__(self) -> "StatelessTracingNotifyOnReceivedFirst":
        """Called to initialize the trace on the broadcaster side for a NOTIFY"""

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Called when the broadcaster side of this trace is done, which may be due
        to cancellation, on a best-effort basis (i.e., as good as `with` could
        do but not better)
        """


class StatelessTracingNotifyOnReceivedFirst(Protocol):
    """First object run on the broadcaster (but not overall)"""

    def on_received(self) -> "StatelessTracingNotifyOnAuthResult":
        """Called immedaitely upon detecting a NOTIFY over the stateless
        protocol, before the body has been parsed or authorization has been
        checked. Generally only useful for collecting timing data if the
        request is accepted
        """


class StatelessTracingNotifyOnAuthResult(Protocol):
    """Run on the broadcaster"""

    def on_bad_request(self) -> None:
        """Called if the request is malformed or otherwise invalid, terminating
        the chain without a useful response to the subscriber
        """

    def on_bad_auth_result(self, /, *, result: BadAuthResult) -> None:
        """Called if the authorization check failed, terminating the chain
        without a useful response to the subscriber
        """

    def on_auth_tentatively_accepted(self) -> "StatelessTracingNotifyOnAuthVerified":
        """Called if the authorization check passed, meaning that if the hashes
        all actually match what was sent, then the request was sent by the subscriber
        """


class StatelessTracingNotifyOnAuthVerified(Protocol):
    """Run on the broadcaster"""

    def on_auth_mismatch(self) -> None:
        """Called if the authorization provided doesn't actually match what was
        sent. This will terminate the chain without a useful response to the
        subscriber
        """

    def on_auth_accepted(
        self, topic: bytes, length: int, identifier: bytes, tracing: bytes
    ) -> "HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]":
        """Called if the authorization header matches what was sent, so
        the broadcaster is moving onto actually processing the notification.

        Args:
            topic (bytes): the topic to find subscribers of
            length (int): the length of the message to send
            identifier (bytes): the arbitrary identifier the subscriber assigned
                to this request, can be assumed to be globally unique if authorized
                subscribers can be trusted, otherwise a new identifier needs to be
                generated if uniqueness is required. In other words, this is globally
                unique iff only trusted internal services can pass authorization
            tracing (bytes): the tracing data sent by the subscriber
        """


class StatelessTracingNotifyOnSendingResponse(Protocol):
    """Runs on the broadcaster"""

    def on_sending_response(self) -> bytes:
        """Called as close as possible to actually sending the `RESPONSE_NOTIFY`
        message to the subscriber. This is necessarily before producing the
        authorization header, which will sign the tracing data, and actually
        formatting the response body, which will include the tracing data.

        Returns:
            bytes: the tracing data to send to the subscriber
        """


class StatelessTracingNotifyOnResponseReceived(Protocol):
    """Runs on the subscriber after receiving the response from the broadcaster
    but before reading the body or verifying the authorization
    """

    def on_network_error(self) -> "StatelessTracingNotifyOnRetryDetermined":
        """Called if the subscriber did not receive a response from the broadcaster
        because either subscriber could not reach the broadcaster, the broadcaster
        did not understand the request or experienced an error that prevented it
        from forming a sensible response, or the broadcasters response could not
        reach the subscriber
        """
        ...

    def on_response_received(
        self, /, *, status_code: int
    ) -> "StatelessTracingNotifyOnResponseAuthResult":
        """Called when the subscriber has received what should be a `RESPONSE_NOTIFY`
        from the broadcaster, but before the body has been read or the authorization
        has been checked

        Args:
            status_code (int): the HTTP status code of the response, which isn't
                used for anything but logging
        """


class StatelessTracingNotifyOnRetryDetermined(Protocol):
    """Called on the subscriber"""

    def on_retry_prevented(self) -> None:
        """Called if the subscriber does not want to attempt to retry this
        type of error
        """

    def on_retries_exhausted(self) -> None:
        """Called if the subscriber wants to retry this request but has exhausted
        its retry limit
        """

    def on_waiting_to_retry(self) -> "StatelessTracingNotifyOnRetryDetermined":
        """Called if the subscriber will wait a bit before trying the next
        broadcaster, immediately before sleeping
        """

    def on_retrying(self) -> StatelessTracingNotifyOnSending:
        """Called if the subscriber will try to notify this or a different
        broadcaster with the same message. A new authorization header will
        be created and there is an opportunity to change the tracing data.
        """


class StatelessTracingNotifyOnResponseAuthResult(Protocol):
    """Runs on the subscriber"""

    def on_bad_response(self) -> StatelessTracingNotifyOnRetryDetermined:
        """Called if the response was malformed or otherwise invalid, so the
        subscriber didn't get any useful tracing data. Will determine if
        retrying is appropriate and provide that info to the next object.
        """

    def on_bad_auth_result(
        self, /, *, result: BadAuthResult
    ) -> StatelessTracingNotifyOnRetryDetermined:
        """Called if the response authorization failed, meaning it may not have
        come from the broadcaster and there is no useful tracing data.
        Will determine if retrying is appropriate and provide that info to the
        next object.
        """

    def on_response_notify_accepted(
        self, /, *, tracing: bytes, num_subscribers: int
    ) -> None:
        """Called if the response was correctly formed and passed authorization,
        meaning the subscriber has received the final tracing data from the
        broadcaster and is about to return from the lonelypsc library

        Args:
            tracing (bytes): the tracing data sent by the broadcaster
            num_subscribers (int): the number of subscribers that received the
                notification, which is often useful for the caller when they know
                how many they were expecting
        """
