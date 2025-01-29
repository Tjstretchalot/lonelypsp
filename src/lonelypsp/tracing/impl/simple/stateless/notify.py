import base64
import io
import json
import secrets
import struct
import time
import warnings
from types import TracebackType
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from lonelypsp.auth.config import BadAuthResult
from lonelypsp.compat import fast_dataclass
from lonelypsp.tracing.impl.simple.config import SimpleTracingConfig
from lonelypsp.tracing.impl.simple.db import SimpleTracingDBSidecar
from lonelypsp.tracing.impl.simple.shared import cristians
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
from lonelypsp.tracing.stateless.notify import (
    StatelessTracingNotifyOnAuthResult,
    StatelessTracingNotifyOnAuthVerified,
    StatelessTracingNotifyOnHashed,
    StatelessTracingNotifyOnReceivedFirst,
    StatelessTracingNotifyOnResponseAuthResult,
    StatelessTracingNotifyOnResponseReceived,
    StatelessTracingNotifyOnRetryDetermined,
    StatelessTracingNotifyOnSending,
    StatelessTracingNotifyOnSendingResponse,
    StatelessTracingNotifyStart,
    StatelessTracingNotifyStartFirst,
)


@fast_dataclass
class RemoteTrace:
    name: str
    extra_json: str
    occurred_at_remote: float


class SimpleStatelessTracingNotifyStart:
    """Subscriber side"""

    def __init__(self, db: SimpleTracingDBSidecar, config: SimpleTracingConfig) -> None:
        self.db: SimpleTracingDBSidecar = db
        """the database to use for the tracing data, assumed to already be entered"""

        self.config: SimpleTracingConfig = config
        """the configuration for the tracing data"""

        self.uid: bytes = int(time.time()).to_bytes(8, "big") + secrets.token_bytes(4)
        """the unique identifier we assigned without having to contact the db"""

        self.next_ord: int = 0
        """the order value for the next piece of timing information"""

        self.request_sent_at_local_nano: Optional[int] = None
        """when the request was sent in local nanotime"""

        self.response_received_at_local_nano: Optional[int] = None
        """when the response was received in local nanotime"""

        self._entered = False
        self._exited = False

    def __enter__(self) -> StatelessTracingNotifyStartFirst:
        assert not self._entered, "Cannot re-enter a tracing event"
        self._entered = True
        self.db.enqueue(
            [
                ("BEGIN IMMEDIATE TRANSACTION", []),
                (
                    "INSERT INTO stateless_notifies(uid, created_at) VALUES (?, ?)",
                    [self.uid, time.time()],
                ),
                ("COMMIT TRANSACTION", []),
            ]
        )
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        assert self._entered, "Cannot exit a tracing event that was never entered"
        if self._exited:
            return

        self._exited = True
        self.db.enqueue(
            [
                (
                    "BEGIN IMMEDIATE TRANSACTION",
                    [],
                ),
                (
                    "UPDATE stateless_notifies SET finished_at = ? WHERE uid = ?",
                    [time.time(), self.uid],
                ),
                (
                    "COMMIT TRANSACTION",
                    [],
                ),
            ]
        )

    def _reserve_ord(self, /) -> int:
        ord = self.next_ord
        self.next_ord += 1
        return ord

    def _trace(
        self,
        /,
        *,
        name: str,
        extra: Dict[str, Any],
        occurred_at: float,
        raw_occurred_at: Optional[float] = None,
    ) -> None:
        assert self._entered, "not entered"
        assert not self._exited, "already exited"
        extra_json = json.dumps(extra)
        if raw_occurred_at is None:
            raw_occurred_at = occurred_at
        self.db.enqueue(
            [
                (
                    "BEGIN IMMEDIATE TRANSACTION",
                    [],
                ),
                (
                    "INSERT INTO stateless_notify_timings "
                    "(notify_id, ord, name, extra, occurred_at, raw_occurred_at) "
                    "SELECT"
                    " stateless_notifies.id, ?, ?, ?, ?, ? "
                    "FROM stateless_notifies "
                    "WHERE stateless_notifies.uid = ?",
                    [
                        self._reserve_ord(),
                        name,
                        extra_json,
                        occurred_at,
                        raw_occurred_at,
                        self.uid,
                    ],
                ),
                (
                    "COMMIT TRANSACTION",
                    [],
                ),
            ]
        )

    # StartFirst
    def _on_start(
        self, /, *, name: str, topic: bytes, length: int, filelike: bool
    ) -> None:
        assert self._entered, "not entered"
        assert not self._exited, "already exited"
        occurred_at = time.time()
        self.db.enqueue(
            [
                ("BEGIN IMMEDIATE TRANSACTION", []),
                (
                    "UPDATE stateless_notifies SET topic = ?, length = ? WHERE uid = ?",
                    [topic, length, self.uid],
                ),
                (
                    "INSERT INTO stateless_notify_timings "
                    "(notify_id, ord, name, extra, occurred_at, raw_occurred_at) "
                    "SELECT"
                    " stateless_notifies.id, ?, ?, ?, ?, ? "
                    "FROM stateless_notifies "
                    "WHERE stateless_notifies.uid = ?",
                    [
                        self._reserve_ord(),
                        name,
                        b'{"filelike": ' + (b"true}" if filelike else b"false}"),
                        occurred_at,
                        occurred_at,
                        self.uid,
                    ],
                ),
                ("COMMIT TRANSACTION", []),
            ]
        )

    def on_start_without_hash(
        self, /, *, topic: bytes, length: int, filelike: bool
    ) -> StatelessTracingNotifyOnHashed:
        self._on_start(
            name="start_without_hash",
            topic=topic,
            length=length,
            filelike=filelike,
        )
        return self

    def on_start_with_hash(
        self, /, *, topic: bytes, length: int, filelike: bool
    ) -> StatelessTracingNotifyOnSending:
        self._on_start(
            name="start_with_hash",
            topic=topic,
            length=length,
            filelike=filelike,
        )
        return self

    # OnHashed
    def on_hashed(self) -> StatelessTracingNotifyOnSending:
        self._trace(name="hashed", extra={}, occurred_at=time.time())
        return self

    # OnSending
    def on_sending_request(
        self, /, *, broadcaster: str, identifier: bytes
    ) -> TracingAndFollowup[StatelessTracingNotifyOnResponseReceived]:
        self._trace(
            name="sending_request",
            extra={"broadcaster": broadcaster},
            occurred_at=time.time(),
        )
        self.request_sent_at_local_nano = time.time_ns()
        return TracingAndFollowup(tracing=b"", followup=self)

    def on_network_error(self) -> StatelessTracingNotifyOnRetryDetermined:
        self._trace(name="network_error", extra={}, occurred_at=time.time())
        return self

    def on_response_received(
        self, /, *, status_code: int
    ) -> StatelessTracingNotifyOnResponseAuthResult:
        self.response_received_at_local_nano = time.time_ns()
        self._trace(
            name="response_received",
            extra={"status_code": status_code},
            occurred_at=time.time(),
        )
        return self

    # StatelessTracingNotifyOnRetryDetermined
    def on_retry_prevented(self) -> None:
        self._trace(name="retry_prevented", extra={}, occurred_at=time.time())

    def on_retries_exhausted(self) -> None:
        self._trace(name="retries_exhausted", extra={}, occurred_at=time.time())

    def on_waiting_to_retry(self) -> StatelessTracingNotifyOnRetryDetermined:
        self._trace(name="waiting_to_retry", extra={}, occurred_at=time.time())
        return self

    def on_retrying(self) -> StatelessTracingNotifyOnSending:
        self._trace(name="retrying", extra={}, occurred_at=time.time())
        return self

    # StatelessTracingNotifyOnResponseAuthResult
    def on_bad_response(self) -> StatelessTracingNotifyOnRetryDetermined:
        self._trace(name="bad_response", extra={}, occurred_at=time.time())
        return self

    def on_bad_auth_result(
        self, /, *, result: BadAuthResult
    ) -> StatelessTracingNotifyOnRetryDetermined:
        self._trace(
            name="bad_auth_result",
            extra={"result": result.name},
            occurred_at=time.time(),
        )
        return self

    def on_response_notify_accepted(
        self, /, *, tracing: bytes, num_subscribers: int
    ) -> None:
        assert self._entered, "not entered"
        assert not self._exited, "already exited"
        assert self.request_sent_at_local_nano is not None, "no request sent"
        assert self.response_received_at_local_nano is not None, "no response received"
        occurred_at = time.time()

        rdr = io.BytesIO(tracing)
        truncated = rdr.read(1) != b"\0"
        num_traces = int.from_bytes(rdr.read(2), "big")
        traces: List[RemoteTrace] = []
        for _ in range(num_traces):
            name_len = int.from_bytes(rdr.read(2), "big")
            name = rdr.read(name_len).decode("utf-8")
            extra_len = int.from_bytes(rdr.read(2), "big")
            extra = rdr.read(extra_len).decode("utf-8")
            occurred_at_remote = struct.unpack(">d", rdr.read(8))[0]
            traces.append(
                RemoteTrace(
                    name=name,
                    extra_json=extra,
                    occurred_at_remote=occurred_at_remote,
                )
            )

        request_received_at_nano_remote = int.from_bytes(rdr.read(8), "big")
        response_sent_at_nano_remote = int.from_bytes(rdr.read(8), "big")
        offset = cristians.compute_offset(
            cristians.CristiansEnd(
                request_sent_at_local_nano=self.request_sent_at_local_nano,
                request_received_at_remote_nano=request_received_at_nano_remote,
                response_sent_at_remote_nano=response_sent_at_nano_remote,
                response_received_at_local_nano=self.response_received_at_local_nano,
            )
        )

        if truncated:
            warnings.warn("tracing data was truncated")

        to_enqueue: List[Tuple[str, List[Any]]] = [
            ("BEGIN IMMEDIATE TRANSACTION", []),
            (
                "INSERT INTO stateless_notify_timings "
                "(notify_id, ord, name, extra, occurred_at, raw_occurred_at) "
                "SELECT"
                " stateless_notifies.id, ?, ?, ?, ?, ? "
                "FROM stateless_notifies "
                "WHERE stateless_notifies.uid = ?",
                [
                    self._reserve_ord(),
                    name,
                    json.dumps(
                        {
                            "num_subscribers": num_subscribers,
                            "cristians": {
                                "request_sent_at_local_nano": self.request_sent_at_local_nano,
                                "request_received_at_remote_nano": request_received_at_nano_remote,
                                "response_sent_at_remote_nano": response_sent_at_nano_remote,
                                "response_received_at_local_nano": self.response_received_at_local_nano,
                                "latency_ms": offset.latency,
                                "offset_ms": offset.offset,
                            },
                            "truncated": truncated,
                        }
                    ),
                    occurred_at,
                    occurred_at,
                    self.uid,
                ],
            ),
        ]

        for remote_trace in traces:
            to_enqueue.append(
                (
                    "INSERT INTO stateless_notify_timings "
                    "(notify_id, ord, name, extra, occurred_at, raw_occurred_at) "
                    "SELECT"
                    " stateless_notifies.id, ?, ?, ?, ?, ? "
                    "FROM stateless_notifies "
                    "WHERE stateless_notifies.uid = ?",
                    [
                        self._reserve_ord(),
                        f"remote_{remote_trace.name}",
                        remote_trace.extra_json,
                        remote_trace.occurred_at_remote - offset.offset,
                        remote_trace.occurred_at_remote,
                        self.uid,
                    ],
                )
            )

        to_enqueue.append(("COMMIT TRANSACTION", []))
        self.db.enqueue(to_enqueue)


class SimpleStatelessTracingNotifyOnReceived:
    """Broadcaster side"""

    def __init__(self) -> None:
        self.request_received_at_nano: Optional[int] = None
        """when the request was received in nanoseconds"""

        self.traces: List[RemoteTrace] = []
        """the traces we will send back as a broadcaster"""

    def __enter__(self) -> StatelessTracingNotifyOnReceivedFirst:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None: ...

    # OnReceivedFirst
    def on_received(self) -> StatelessTracingNotifyOnAuthResult:
        self.request_received_at_nano = time.time_ns()
        return self

    # OnAuthResult
    def on_bad_request(self) -> None: ...

    def on_bad_auth_result(self, /, *, result: BadAuthResult) -> None: ...

    def on_auth_tentatively_accepted(self) -> StatelessTracingNotifyOnAuthVerified:
        self.traces.append(
            RemoteTrace(
                name="auth_tentatively_accepted",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    # OnAuthVerified
    def on_auth_mismatch(self) -> None: ...

    def on_auth_accepted(
        self, topic: bytes, length: int, identifier: bytes, tracing: bytes
    ) -> HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]:
        self.traces.append(
            RemoteTrace(
                name="auth_accepted",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    # HandledTrustedNotify
    def on_unavailable(self) -> None: ...

    def on_exact_subscriber_found(
        self, /, *, url: str
    ) -> HandledTrustedNotifySendingReceive[
        HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
    ]:
        self.traces.append(
            RemoteTrace(
                name="exact_subscriber_found",
                extra_json=json.dumps({"url": url}),
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_glob_subscriber_found(
        self, /, *, glob: str, url: str
    ) -> HandledTrustedNotifySendingReceive[
        HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
    ]:
        self.traces.append(
            RemoteTrace(
                name="glob_subscriber_found",
                extra_json=json.dumps({"glob": glob, "url": url}),
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_no_more_subscribers(self) -> StatelessTracingNotifyOnSendingResponse:
        self.traces.append(
            RemoteTrace(
                name="no_more_subscribers",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    # HandledTrustedNotifySendingReceive
    def on_sending_receive(
        self, /, *, identifier: bytes
    ) -> TracingAndFollowup[
        HandledTrustedNotifyReceivedResponse[
            HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
        ]
    ]:
        self.traces.append(
            RemoteTrace(
                name="sending_receive",
                extra_json=json.dumps(
                    {
                        "identifier_b64url": base64.urlsafe_b64encode(
                            identifier
                        ).decode("ascii")
                    }
                ),
                occurred_at_remote=time.time(),
            )
        )
        return TracingAndFollowup(tracing=b"", followup=self)

    # HandledTrustedNotifyReceivedResponse
    def on_network_error(
        self,
    ) -> HandledTrustedNotifyHandleMissedStart[
        HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
    ]:
        self.traces.append(
            RemoteTrace(
                name="network_error",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_response_received(
        self, /, *, status_code: int
    ) -> HandleTrustedNotifyResponseAuthResultReady[
        HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
    ]:
        self.traces.append(
            RemoteTrace(
                name="response_received",
                extra_json=json.dumps({"status_code": status_code}),
                occurred_at_remote=time.time(),
            )
        )
        return self

    # HandledTrustedNotifyHandleMissedStart
    def on_handle_missed_start(
        self,
    ) -> HandleTrustedNotifyHandleMissedDone[
        HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
    ]:
        self.traces.append(
            RemoteTrace(
                name="handle_missed_start",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    # HandleTrustedNotifyHandleMissedDone
    def on_handle_missed_skipped(
        self, /, *, recovery: Optional[str], next_retry_at: Optional[float]
    ) -> HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]:
        self.traces.append(
            RemoteTrace(
                name="handle_missed_skipped",
                extra_json=json.dumps(
                    {"recovery": recovery, "next_retry_at": next_retry_at}
                ),
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_handle_missed_success(
        self, recovery: str, next_retry_at: float
    ) -> HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]:
        self.traces.append(
            RemoteTrace(
                name="handle_missed_success",
                extra_json=json.dumps(
                    {"recovery": recovery, "next_retry_at": next_retry_at}
                ),
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_handle_missed_unavailable(
        self, recovery: str, next_retry_at: float
    ) -> HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]:
        self.traces.append(
            RemoteTrace(
                name="handle_missed_unavailable",
                extra_json=json.dumps(
                    {"recovery": recovery, "next_retry_at": next_retry_at}
                ),
                occurred_at_remote=time.time(),
            )
        )
        return self

    # HandleTrustedNotifyResponseAuthResultReady
    def on_bad_receive_response(
        self,
    ) -> HandledTrustedNotifyHandleMissedStart[
        HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
    ]:
        self.traces.append(
            RemoteTrace(
                name="bad_response",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_unsubscribe_immediate_requested(
        self,
    ) -> HandleTrustedNotifyUnsubscribeImmediateDone[
        HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
    ]:
        self.traces.append(
            RemoteTrace(
                name="unsubscribe_immediate_requested",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    # HandleTrustedNotifyResponseAuthResultReady
    def on_bad_receive_auth_result(
        self, /, *, result: BadAuthResult
    ) -> HandledTrustedNotifyHandleMissedStart[
        HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]
    ]:
        self.traces.append(
            RemoteTrace(
                name="bad_auth_result",
                extra_json=json.dumps({"result": result.name}),
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_receive_confirmed(
        self, /, *, tracing: bytes, num_subscribers: int
    ) -> HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]:
        self.traces.append(
            RemoteTrace(
                name="receive_confirmed",
                extra_json=json.dumps({"num_subscribers": num_subscribers}),
                occurred_at_remote=time.time(),
            )
        )
        return self

    # HandleTrustedNotifyUnsubscribeImmediateDone
    def on_unsubscribe_immediate_success(
        self,
    ) -> HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]:
        self.traces.append(
            RemoteTrace(
                name="unsubscribe_immediate_success",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_unsubscribe_immediate_not_found(
        self,
    ) -> HandledTrustedNotify[StatelessTracingNotifyOnSendingResponse]:
        self.traces.append(
            RemoteTrace(
                name="unsubscribe_immediate_not_found",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )
        return self

    def on_unsubscribe_immediate_unavailable(self) -> None:
        self.traces.append(
            RemoteTrace(
                name="unsubscribe_immediate_unavailable",
                extra_json="{}",
                occurred_at_remote=time.time(),
            )
        )

    # StatelessTracingNotifyOnSendingResponse
    def on_sending_response(self) -> bytes:
        assert self.request_received_at_nano is not None, "no request received"
        tracing = io.BytesIO()
        tracing.write(b"\0")  # truncated flag
        tracing.write(len(self.traces).to_bytes(2, "big"))

        for idx, trace in enumerate(self.traces):
            start_pos = tracing.tell()
            tracing.write(len(trace.name).to_bytes(2, "big"))
            tracing.write(trace.name.encode("utf-8"))
            tracing.write(len(trace.extra_json).to_bytes(2, "big"))
            tracing.write(trace.extra_json.encode("utf-8"))
            tracing.write(struct.pack(">d", trace.occurred_at_remote))
            if tracing.tell() >= (2**16) - 17:
                warnings.warn("tracing data too large, truncating")
                tracing.seek(0)
                tracing.write(b"\1")
                tracing.write(idx.to_bytes(2, "big"))
                tracing.seek(start_pos)
                break

        tracing.write(self.request_received_at_nano.to_bytes(8, "big"))
        response_sent_at_nano = time.time_ns()
        tracing.write(response_sent_at_nano.to_bytes(8, "big"))
        final_pos = tracing.tell()
        return tracing.getvalue()[:final_pos]


if TYPE_CHECKING:
    _: Type[StatelessTracingNotifyStart] = SimpleStatelessTracingNotifyStart
