from typing import TYPE_CHECKING, Literal, Optional, Type

from lonelypsp.auth.config import BadAuthResult
from lonelypsp.tracing.shared.handle_trusted_notify import (
    HandledTrustedNotify,
    HandledTrustedNotifyHandleMissedStart,
    HandledTrustedNotifyReceivedResponse,
    HandledTrustedNotifySendingReceive,
    HandleTrustedNotifyHandleMissedDone,
    HandleTrustedNotifyResponseAuthResultReady,
    HandleTrustedNotifyUnsubscribeImmediateDone,
)
from lonelypsp.tracing.shared.tracing_and_followup import TracingAndFollowup


class NoopHandleTrustedNotify:
    """No-op implementation for tracing a `handle_trusted_notify` call"""

    def on_unavailable(self) -> None: ...
    def on_exact_subscriber_found(
        self, /, *, url: str
    ) -> HandledTrustedNotifySendingReceive[HandledTrustedNotify[Literal[None]]]:
        return self

    def on_glob_subscriber_found(
        self, /, *, glob: str, url: str
    ) -> HandledTrustedNotifySendingReceive[HandledTrustedNotify[Literal[None]]]:
        return self

    def on_no_more_subscribers(self) -> None: ...

    def on_sending_receive(
        self, /, *, identifier: bytes
    ) -> TracingAndFollowup[
        HandledTrustedNotifyReceivedResponse[HandledTrustedNotify[Literal[None]]]
    ]:
        return TracingAndFollowup(tracing=b"", followup=self)

    def on_network_error(
        self,
    ) -> HandledTrustedNotifyHandleMissedStart[HandledTrustedNotify[None]]:
        return self

    def on_response_received(
        self, /, *, status_code: int
    ) -> HandleTrustedNotifyResponseAuthResultReady[HandledTrustedNotify[None]]:
        return self

    def on_bad_receive_response(
        self,
    ) -> HandledTrustedNotifyHandleMissedStart[HandledTrustedNotify[None]]:
        return self

    def on_unsubscribe_immediate_requested(
        self,
    ) -> HandleTrustedNotifyUnsubscribeImmediateDone[HandledTrustedNotify[None]]:
        return self

    def on_bad_receive_auth_result(
        self, /, *, result: BadAuthResult
    ) -> HandledTrustedNotifyHandleMissedStart[HandledTrustedNotify[None]]:
        return self

    def on_receive_confirmed(
        self, /, *, tracing: bytes, num_subscribers: int
    ) -> HandledTrustedNotify[None]:
        return self

    def on_unsubscribe_immediate_success(self) -> HandledTrustedNotify[None]:
        return self

    def on_unsubscribe_immediate_not_found(self) -> HandledTrustedNotify[None]:
        return self

    def on_unsubscribe_immediate_unavailable(self) -> None: ...

    def on_handle_missed_start(
        self,
    ) -> HandleTrustedNotifyHandleMissedDone[HandledTrustedNotify[None]]:
        return self

    def on_handle_missed_skipped(
        self, /, *, recovery: Optional[str], next_retry_at: Optional[float]
    ) -> HandledTrustedNotify[None]:
        return self

    def on_handle_missed_success(
        self, recovery: str, next_retry_at: float
    ) -> HandledTrustedNotify[None]:
        return self

    def on_handle_missed_unavailable(
        self, recovery: str, next_retry_at: float
    ) -> HandledTrustedNotify[None]:
        return self


if TYPE_CHECKING:
    _: Type[HandledTrustedNotify[Literal[None]]] = NoopHandleTrustedNotify
