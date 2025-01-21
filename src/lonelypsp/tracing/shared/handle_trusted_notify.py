from typing import Generic, Optional, Protocol, TypeVar

from lonelypsp.auth.config import BadAuthResult
from lonelypsp.tracing.shared.tracing_and_followup import TracingAndFollowup

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class HandledTrustedNotify(Generic[T], Protocol):
    """Runs on the broadcaster as part of various other sequences, notifying
    subscribers in turn until the final subscriber is reached. Assumes that
    from context the topic that is being notified is known

    T is the next object to use if this ends normally
    """

    def on_unavailable(self) -> None:
        """Called if the subscriber database could not be reached (DBConfig
        returned UNAVAILABLE). Terminates this loop
        """

    def on_exact_subscriber_found(
        self, /, *, url: str
    ) -> "HandledTrustedNotifySendingReceive[HandledTrustedNotify[T]]":
        """Called if the subscriber database found another subscriber that
        is subscribed to this exact topic

        Args:
            url (str): the URL of the exact subscriber
        """

    def on_glob_subscriber_found(
        self, /, *, glob: str, url: str
    ) -> "HandledTrustedNotifySendingReceive[HandledTrustedNotify[T]]":
        """Called if the subscriber database found another subscriber that
        is subscribed to the topic via a glob pattern

        Args:
            glob (str): the glob pattern that the topic matched
            url (str): the URL of the subscriber
        """

    def on_no_more_subscribers(self) -> T:
        """Called if there are no more subscribers to notify, which is the normal
        end to the loop
        """


class HandledTrustedNotifySendingReceive(Generic[T], Protocol):
    """Runs on the broadcaster"""

    def on_sending_receive(
        self, /, *, identifier: bytes
    ) -> TracingAndFollowup["HandledTrustedNotifyReceivedResponse[T]"]:
        """Produces the tracing data to send to the subscriber for processing
        the `RECEIVE`, plus the object on the broadcaster side to track the
        response from the RECEIVE

        Args:
            identifier (bytes): a new identifier for the RECEIVE that was assigned
                by the broadcaster. This will be passed to the subscriber without
                needing to include it in the tracing data. This can be assumed to
                be globally unique

        Returns:
            tracing: the tracing data to send to the subscriber
            followup: the object on the broadcaster side to track the response
        """


class HandledTrustedNotifyReceivedResponse(Generic[T_co], Protocol):
    """Runs on the broadcaster"""

    def on_network_error(self) -> "HandledTrustedNotifyHandleMissedStart[T_co]":
        """Called if no response was received from the subscriber, meaning either
        they could not be reached, didn't understand the protocol used, they
        experienced an error that prevented them from producing a sensible
        response, or the response never reached us due to network-level issues.

        A `MISSED` message will be scheduled if possible and then will move onto
        the next subscriber
        """

    def on_response_received(
        self, /, *, status_code: int
    ) -> "HandleTrustedNotifyResponseAuthResultReady[T_co]":
        """Called if a response was received from the subscriber but before the
        body has been parsed and before the authorization check on that response
        has been performed

        Args:
            status_code (int): the HTTP status code of the response, which isn't
                used for anything but logging
        """


class HandleTrustedNotifyResponseAuthResultReady(Generic[T_co], Protocol):
    def on_bad_receive_response(self) -> "HandledTrustedNotifyHandleMissedStart[T_co]":
        """Called if the response was malformed or otherwise invalid, which
        will schedule a `MISSED` message if possible and then move onto the
        next subscriber
        """

    def on_unsubscribe_immediate_requested(
        self,
    ) -> "HandleTrustedNotifyUnsubscribeImmediateDone[T_co]":
        """Called if the subscriber returned the unsubscribe immediate response,
        which does not require authorization and thus cannot/does not include
        tracing data. The unsubscribe will be processed and then the broadcaster
        will move onto the next subscriber
        """

    def on_bad_receive_auth_result(
        self, /, *, result: BadAuthResult
    ) -> "HandledTrustedNotifyHandleMissedStart[T_co]":
        """Called if the message was correctly formed but the authorization header
        was invalid, which will schedule a `MISSED` message if possible and then
        move onto the next subscriber
        """

    def on_receive_confirmed(self, /, *, tracing: bytes, num_subscribers: int) -> T_co:
        """Called if the response was correctly formed and the auth result succeeded.
        This is done in a single pass, so the tracing data is ready to be deserialized.

        Args:
            tracing (bytes): the tracing data from the subscriber
            num_subscribers (int): the number of subscribers that were notified
                by this RECEIVE, usually 1, but if the subscriber is also itself
                a broadcaster, may be 0 or more.
        """


class HandleTrustedNotifyUnsubscribeImmediateDone(Generic[T_co], Protocol):
    def on_unsubscribe_immediate_success(self) -> T_co:
        """Called when the subscriber has been successfully unsubscribed and
        the broadcaster is ready to move onto the next subscriber
        """

    def on_unsubscribe_immediate_not_found(self) -> T_co:
        """Called if the subscriber had already been removed from the database,
        and the broadcaster is ready to move onto the next subscriber
        """

    def on_unsubscribe_immediate_unavailable(self) -> None:
        """Called when the subscriber could not be unsubscribed because of a
        database issue, which ends the loop
        """


class HandledTrustedNotifyHandleMissedStart(Generic[T_co], Protocol):
    """Runs on the broadcaster"""

    def on_handle_missed_start(self) -> "HandleTrustedNotifyHandleMissedDone[T_co]":
        """Called when about to try scheduling a `MISSED` message before
        proceeding onto something else
        """


class HandleTrustedNotifyHandleMissedDone(Generic[T_co], Protocol):
    """Runs on the broadcaster"""

    def on_handle_missed_skipped(
        self, /, *, recovery: Optional[str], next_retry_at: Optional[float]
    ) -> T_co:
        """Did not schedule a `MISSED` message because either the subscriber did
        not have a recovery url set or the configuration of the broadcaster indicated
        one should not be sent

        Args:
            recovery (str, None): if the subscriber had a place to send MISSED messages,
                that url, otherwise None
            next_retry_at (float, None): if the broadcaster is configured to send missed
                messages, the time at which it was scheduled for, otherwise None
        """

    def on_handle_missed_success(self, recovery: str, next_retry_at: float) -> T_co:
        """Scheduled a `MISSED` message normally

        Args:
            recovery (str): the URL to send the `MISSED` message to
            next_retry_at (float): the time at which the `MISSED` message was scheduled
        """

    def on_handle_missed_unavailable(self, recovery: str, next_retry_at: float) -> T_co:
        """Failed to schedule a `MISSED` message due to an internal issue (the
        database was unavailable). Will still proceed as normal as MISSED messages
        are on a best-effort basis and the core database may still be functioning

        Args:
            recovery (str): the URL to send the `MISSED` message to
            next_retry_at (float): the time at which the `MISSED` message was supposed
                to be scheduled for
        """
