from enum import IntEnum, auto
from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    Protocol,
    Type,
)

from lonelypsp.auth.set_subscriptions_info import SetSubscriptionsInfo
from lonelypsp.stateful.messages.configure import S2B_Configure
from lonelypsp.stateful.messages.confirm_configure import B2S_ConfirmConfigure
from lonelypsp.stateful.messages.continue_notify import B2S_ContinueNotify
from lonelypsp.stateful.messages.continue_receive import S2B_ContinueReceive
from lonelypsp.stateful.messages.disable_zstd_custom import B2S_DisableZstdCustom
from lonelypsp.stateful.messages.enable_zstd_custom import B2S_EnableZstdCustom
from lonelypsp.stateful.messages.enable_zstd_preset import B2S_EnableZstdPreset
from lonelypsp.stateless.make_strong_etag import StrongEtag


class AuthResult(IntEnum):
    """Distinguishes the different possible results of an authorization check"""

    OK = auto()
    """the request is allowed"""

    UNAUTHORIZED = auto()
    """the authorization header is required but not provided"""

    FORBIDDEN = auto()
    """the authorization header is provided but invalid"""

    UNAVAILABLE = auto()
    """a service is required to check this isn't available"""


BadAuthResult = Literal[
    AuthResult.UNAUTHORIZED, AuthResult.FORBIDDEN, AuthResult.UNAVAILABLE
]


class ToBroadcasterAuthConfig(Protocol):
    """Handles verifying requests from a subscriber to this broadcaster or
    producing the authorization header when contacting other broadcasters
    """

    async def setup_to_broadcaster_auth(self) -> None:
        """Prepares this authorization instance for use. If the
        to broadcaster auth config is not re-entrant (i.e., it cannot
        be used by two clients simultaneously), it must detect this and error
        out.
        """

    async def teardown_to_broadcaster_auth(self) -> None:
        """Cleans up this authorization instance after use. This is called when a
        client is done using the auth config, and should release any resources
        it acquired during `setup_to_broadcaster_auth`.
        """

    async def authorize_subscribe_exact(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the broadcaster to subscribe
        the given url to the given topic.

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            url (str): the url the subscriber is subscribing to
            recovery (str, None): the url that will receive MISSED messages for this
                subscription, if any
            exact (bytes): the exact topic they are subscribing to
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_subscribe_exact_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to
        (un)subscribe a specific url to a specific topic

        Args:
            tracing (bytes): the tracing data from the subscriber, may be empty
            url (str): the url that will receive notifications
            recovery (str, None): the url that will receive MISSED messages for this
                subscription, if any. Always None for unsubscribes
            exact (bytes): the exact topic they want to receive messages from
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_subscribe_glob(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the broadcaster to subscribe
        the given url to any message sent to a topic which matches the glob.

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            url (str): the url the subscriber is subscribing to
            recovery (str, None): the url that will receive MISSED messages for this
                subscription, if any
            glob (str): the glob pattern they are subscribing to
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_subscribe_glob_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to
        (un)subscribe a specific url to a specific glob of topics

        Args:
            tracing (bytes): the tracing data from the subscriber, may be empty
            url (str): the url that will receive notifications
            recovery (str, None): the url that will receive MISSED messages for this
                subscription, if any
            glob (str): a glob for the topics that they want to receive notifications from
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_notify(
        self,
        /,
        *,
        tracing: bytes,
        topic: bytes,
        identifier: bytes,
        message_sha512: bytes,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the broadcaster to fanout
        a notification on a specific topic. As the message may be very large, only
        the sha512 of the message is used for authorization.

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            topic (bytes): the topic that the message is being sent to
            identifier (bytes): an arbitrary identifier for this message assigned
                by the subscriber, max 255 bytes
            message_sha512 (bytes): the sha512 of the message being sent
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_notify_allowed(
        self,
        /,
        *,
        tracing: bytes,
        topic: bytes,
        identifier: bytes,
        message_sha512: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to fanout a
        notification on a specific topic.

        As we support very large messages, for authorization only the SHA-512 of
        the message should be used, which will be fully verified before any
        notifications go out.

        Note that in websockets where compression is enabled, the sha512 is
        of the compressed content, as we cannot safely decompress the data (and
        thus compute the decompressed sha512) unless we know it is safe, at which
        point a second check would be redundant.

        Args:
            tracing (bytes): the tracing data from the subscriber, may be empty
            topic (bytes): the topic that the message is being sent to
            identifier (bytes): an arbitrary identifier for this message assigned
                by the subscriber, max 255 bytes
            message_sha512 (bytes): the sha512 of the message being sent
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_stateful_configure(
        self,
        /,
        *,
        tracing: bytes,
        subscriber_nonce: bytes,
        enable_zstd: bool,
        enable_training: bool,
        initial_dict: int,
    ) -> Optional[str]:
        """Produces the authorization header to send to the broadcaster to configure
        a stateful connection. This is the first packet in the stateful protocol

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            subscriber_nonce (bytes): the 32 random bytes the subscriber is
                contributing toward the connection nonce
            enable_zstd (bool): whether to enable zstd compression
            enable_training (bool): whether to enable training mode
            initial_dict (int): the initial dictionary to use

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_stateful_configure_allowed(
        self, /, *, message: S2B_Configure, now: float
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to configure
        a stateful connection with a subscriber.

        Args:
            message (S2B_Configure): the configure message they sent
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """

    async def authorize_check_subscriptions(
        self, /, *, tracing: bytes, url: str, now: float
    ) -> Optional[str]:
        """Produces the authorization header sent to the broadcaster to check
        the subscriptions for a specific url.

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            url (str): the url the subscriber is checking
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_check_subscriptions_allowed(
        self, /, *, tracing: bytes, url: str, now: float, authorization: Optional[str]
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to check
        the subscriptions for a specific url.

        Args:
            tracing (bytes): the tracing data from the subscriber, may be empty
            url (str): the url whose subscriptions are being checked
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_set_subscriptions(
        self, /, *, tracing: bytes, url: str, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        """Produces the authorization header sent to the broadcaster to replace
        the subscriptions for a specific url.

        Unlike with the checking side which might compare the user being
        authenticated with vs the topics, there is generally no reason to need
        to view the specific globs/topics that are being subscribed to for
        generating the authorization token, as if they are not valid it will
        be caught by the broadcaster

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            url (str): the url the subscriber is setting
            strong_etag (StrongEtag): the strong etag of the subscriptions being set
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_set_subscriptions_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        strong_etag: StrongEtag,
        subscriptions: SetSubscriptionsInfo,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to replace
        the subscriptions for a specific url.

        Ideally the authorization would not need to actually iterate the topics
        and globs, but in practice that is too great a restriction, so instead
        the iterable is async, single-use, and can detect if it was unused, allowing
        the implementation the maximum flexibility to make performance optimizations
        while still allowing the obvious desired case of some users can only subscribe
        to certain prefixes

        WARN: when this function returns, `subscriptions` will no longer be usable

        Args:
            tracing (bytes): the tracing data from the subscriber, may be empty
            url (str): the url whose subscriptions are being set
            strong_etag (StrongEtag): the strong etag that will be verified before
                actually setting subscriptions, but may not have been verified yet.
            subscriptions (SetSubscriptionsInfo): the subscriptions to set
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_stateful_continue_receive(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        part_id: int,
        url: str,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the broadcaster to acknowledge
        that the subscriber has finished receiving the given part id of the given arbitrarily
        identified message and is ready to receive more. This is used on stateful connections
        which have simultaneous, continuous receive and send capabilities, and is used as a
        form of backpressure. Note that the broadcaster might send e.g. 3 messages before
        waiting for the ack on the first one, to keep the connection reasonably saturated

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            identifier (bytes): the arbitrary identifier of the message being received.
                this identifier was assigned by the broadcaster on the first `RECEIVE_STREAM`
            part_id (int): the part id of the message received
            url (str): websocket:<nonce>:<ctr> which helps detect desyncs
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_stateful_continue_receive_allowed(
        self, /, *, url: str, message: S2B_ContinueReceive, now: float
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to acknowledge
        that the subscriber has finished receiving the given part id of the given arbitrarily
        identified message and is ready to receive more.

        Args:
            url (str): websocket:<nonce>:<ctr> which helps detect desyncs
            message (S2B_ContinueReceive): the continue receive message from the subscriber
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """

    async def authorize_confirm_receive(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        num_subscribers: int,
        url: str,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the broadcaster to confirm
        that the subscriber has received the entire message with the given identifier.

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            identifier (bytes): the arbitrary identifier of the message being received.
                this identifier was assigned by the broadcaster
            num_subscribers (int): the number of subscribers that received the message
            url (str): the url the subscriber received the message on; for websockets, this
                is a unique identifier to this request
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_confirm_receive_allowed(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        num_subscribers: int,
        url: str,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to confirm
        that the subscriber has received the entire message with the given identifier.

        Args:
            tracing (bytes): the tracing data from the subscriber, may be empty
            identifier (bytes): the arbitrary identifier of the message being received.
                this identifier was assigned by the broadcaster
            num_subscribers (int): the number of subscribers that received the message
            url (str): the url the subscriber received the message on; for websockets, this
                is a unique identifier to this request
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_confirm_missed(
        self, /, *, tracing: bytes, topic: bytes, url: str, now: float
    ) -> Optional[str]:
        """Produces the authorization header to send to the broadcaster to confirm
        that the subscriber received that it may have missed a message on the given
        topic via the given url at approximately the given time.

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            topic (bytes): the topic that one or more messages may have been missed on
            url (str): the url the subscriber missed the message on
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_confirm_missed_allowed(
        self,
        /,
        *,
        tracing: bytes,
        topic: bytes,
        url: str,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to the broadcaster to confirm
        that the subscriber received that it may have missed a message on the given
        topic via the given url at approximately the given time.

        Args:
            tracing (bytes): the tracing data from the subscriber, may be empty
            topic (bytes): the topic that one or more messages may have been missed on
            url (str): the url the subscriber missed the message on
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """


class ToSubscriberAuthConfig(Protocol):
    """Handles verifying requests from a broadcaster to this subscriber or
    producing the authorization header when contacting subscribers
    """

    async def setup_to_subscriber_auth(self) -> None:
        """Prepares this authorization instance for use. If the to subscriber auth
        config is not re-entrant (i.e., it cannot be used by two clients
        simultaneously), it must detect this and error out.
        """

    async def teardown_to_subscriber_auth(self) -> None:
        """Cleans up this authorization instance after use. This is called when a
        client is done using the auth config, and should release any resources it
        acquired during `setup_to_subscriber_auth`.
        """

    async def authorize_receive(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        topic: bytes,
        message_sha512: bytes,
        identifier: bytes,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber a message
        with the given sha512 on the given topic at approximately the given
        time.

        When using websockets, the url is of the form "websocket:<nonce>:<ctr>",
        where more details are described in the websocket endpoints
        documentation. What's important is that the recipient can either verify
        the url is what they expect or the url is structured such that it is
        unique if _either_ party is acting correctly, meaning replay attacks are
        limited to a single target (i.e., we structurally disallow replaying a
        message sent from Bob to Alice via pretending to be Bob to Charlie, as
        Charlie will be able to tell that message was intended for not-Charlie).

        Note that the reverse is not promised (i.e., broadcasters do not know which
        broadcaster the subscriber meant to contact), but assuming the number of
        broadcasters is much smaller than the number of subscribers, this is less
        of an issue to coordinate.

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            url (str): the url that will receive the notification
            topic (bytes): the topic that the message is being sent to
            message_sha512 (bytes): the sha512 of the message being sent
            identifier (bytes): the arbitrary identifier of the message being received.
                this identifier was assigned by the broadcaster
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_receive_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        topic: bytes,
        message_sha512: bytes,
        identifier: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to a subscriber to receive a message
        from a broadcaster on a topic.

        As we support very large messages, for authorization only the SHA-512 of
        the message should be used, which will be fully verified.

        Broadcasters act as subscribers for receiving messages when a subscriber
        is connected via websocket, so it can forward messages sent to other
        broadcasters.

        Args:
            tracing (bytes): the tracing data the broadcaster provided, may be empty
            topic (bytes): the topic the message claims to be on
            message_sha512 (bytes): the sha512 of the message being received
            identifier (bytes): the arbitrary identifier of the message being received.
                this identifier was assigned by the broadcaster
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_missed(
        self, /, *, tracing: bytes, recovery: str, topic: bytes, now: float
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to indicate
        that it may have missed a message on the given topic. The message is being sent at
        approximately the given time, which is unrelated to when the message they
        missed was sent.

        The contents of the message are not sent nor necessarily available; this
        is just to inform the subscriber that they may have missed a message.
        They may have their own log that they can recovery the message with if
        necessary.

        When sending this over a websocket, the recovery url is of the form
        `websocket:<nonce>:<ctr>`, where more details can be found in the
        stateful documentation in lonelypsp

        Args:
            tracing (bytes): the tracing data to send to the broadcaster, may be empty
            recovery (str): the url that will receive the missed message
            topic (bytes): the topic that the message was on
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_missed_allowed(
        self,
        /,
        *,
        tracing: bytes,
        recovery: str,
        topic: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to a subscriber via the given
        recovery url to indicate it may have missed a message on the given topic

        Broadcasters act as subscribers for receiving messages when a subscriber
        is connected via websocket, so it can forward messages sent to other
        broadcasters.

        Args:
            tracing (bytes): the tracing data the broadcaster provided, may be empty
            recovery (str): the url the missed message was sent to
            topic (bytes): the topic the message was on
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_confirm_subscribe_exact(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to confirm
        the exact subscription they sent was accepted.

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            url (str): the url the subscriber is subscribing to
            recovery (str, None): the url that will receive MISSED messages for this
                subscription, if any
            exact (bytes): the exact topic they are subscribing to
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_confirm_subscribe_exact_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber to confirm
        the exact subscription they sent was accepted.

        Args:
            tracing (bytes): the tracing data from the broadcaster, may be empty
            url (str): the url that will receive notifications
            recovery (str, None): the url that will receive MISSED messages for this
                subscription, if any
            exact (bytes): the exact topic they want to receive messages from
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_confirm_subscribe_glob(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to confirm
        the glob subscription they sent was accepted.

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            url (str): the url the subscriber is subscribing to
            recovery (str, None): the url that will receive MISSED messages for this
                subscription, if any
            glob (str): the glob pattern they are subscribing to
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_confirm_subscribe_glob_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber to confirm
        the glob subscription they sent was accepted.

        Args:
            tracing (bytes): the tracing data from the broadcaster, may be empty
            url (str): the url that will receive notifications
            recovery (str, None): the url that will receive MISSED messages for this
                subscription, if any
            glob (str): a glob for the topics that they want to receive notifications from
            now (float): the current time in seconds since the epoch, as if from `time.time()`
            authorization (str, None): the authorization header they provided

        Returns: AuthResult
        """

    async def authorize_confirm_notify(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        subscribers: int,
        topic: bytes,
        message_sha512: bytes,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to confirm
        the notification they sent was accepted.

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            identifier (bytes): the arbitrary identifier of the message being received.
                this identifier was assigned by the subscriber
            subscribers (int): the number of subscribers that received the message
            topic (bytes): the topic that the message is being sent to
            message_sha512 (bytes): the sha512 of the message being sent
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_confirm_notify_allowed(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        subscribers: int,
        topic: bytes,
        message_sha512: bytes,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber to confirm
        the notification they sent was accepted.

        Args:
            tracing (bytes): the tracing data from the broadcaster, may be empty
            identifier (bytes): the arbitrary identifier of the message being received.
                this identifier was assigned by the subscriber
            subscribers (int): the number of subscribers that received the message
            topic (bytes): the topic that the message is being sent to
            message_sha512 (bytes): the sha512 of the message being sent
            authorization (str, None): the authorization header they provided
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """

    async def authorize_check_subscriptions_response(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber in response
        to a CHECK_SUBSCRIPTIONS request

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            strong_etag (StrongEtag): the strong etag to return
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_check_subscription_response_allowed(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber in response
        to a CHECK_SUBSCRIPTIONS request

        Args:
            tracing (bytes): the tracing data from the broadcaster, may be empty
            strong_etag (StrongEtag): the strong etag to return
            authorization (str, None): the authorization header they provided
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """

    async def authorize_set_subscriptions_response(
        self, /, *, tracing: bytes, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber in response
        to a SET_SUBSCRIPTIONS request

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            strong_etag (StrongEtag): the strong etag to return
            now (float): the current time in seconds since the epoch, as if from `time.time()`
        """

    async def is_set_subscription_response_allowed(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber in response
        to a SET_SUBSCRIPTIONS request

        Args:
            tracing (bytes): the tracing data from the broadcaster, may be empty
            strong_etag (StrongEtag): the strong etag to return
            authorization (str, None): the authorization header they provided
            now (float): the current time in seconds since the epoch, as if from `time.time()`
        """

    async def authorize_stateful_confirm_configure(
        self, /, *, broadcaster_nonce: bytes, tracing: bytes, now: float
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to confirm
        the stateful configure message they sent was accepted.

        Args:
            broadcaster_nonce (bytes): the nonce that the broadcaster will send in the
                confirm configure message
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_stateful_confirm_configure_allowed(
        self, /, *, message: B2S_ConfirmConfigure, now: float
    ) -> AuthResult:
        """Checks the authorization header posted to a subscriber to confirm the
        stateful configure message they sent was accepted.

        Args:
            message (B2S_ConfirmConfigure): the confirm configure message from the broadcaster
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """

    async def authorize_stateful_enable_zstd_preset(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        compressor_identifier: int,
        compression_level: int,
        min_size: int,
        max_size: int,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to enable
        zstd compression with the given parameters over a stateful connection.

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            url (str): the url the subscriber is subscribing to
            compressor_identifier (int): the identifier of the zstd compressor
            compression_level (int): the compression level to use
            min_size (int): the minimum size of messages to compress
            max_size (int): the maximum size of messages to compress, up to 2^64 - 1
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_stateful_enable_zstd_preset_allowed(
        self, /, *, url: str, message: B2S_EnableZstdPreset, now: float
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber to enable
        zstd compression with the given parameters over a stateful connection.

        Args:
            url (str): websocket:<nonce>:<ctr>, unique to this request
            message (B2S_EnableZstdPreset): the enable zstd preset message from the broadcaster
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """

    async def authorize_stateful_enable_zstd_custom(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        compressor_identifier: int,
        compression_level: int,
        min_size: int,
        max_size: int,
        sha512: bytes,
        now: float,
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to enable
        zstd compression with the given parameters over a stateful connection.

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            url (str): the url the subscriber is subscribing to
            compressor_identifier (bytes): the identifier of the zstd compressor
            compression_level (int): the compression level to use
            min_size (int): the minimum size of messages to compress
            max_size (int): the maximum size of messages to compress, up to 2^64 - 1
            sha512 (bytes): the sha512 of the compressor dictionary, which is used in
                place of the actual dictionary data for authorization (as the dictionary
                could be pretty large)
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_stateful_enable_zstd_custom_allowed(
        self, /, *, url: str, message: B2S_EnableZstdCustom, now: float
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber to enable
        zstd compression with the given parameters over a stateful connection.

        Args:
            url (str): websocket:<nonce>:<ctr>, unique to this request
            message (B2S_EnableZstdCustom): the enable zstd custom message from the broadcaster
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """

    async def authorize_stateful_disable_zstd_custom(
        self, /, *, tracing: bytes, compressor_identifier: int, url: str, now: float
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to disable
        zstd compression previously enabled with the given identifier

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            compressor_identifier (int): the identifier of the zstd compressor
            url (str): the url the subscriber is subscribing to
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_stateful_disable_zstd_custom_allowed(
        self, /, *, url: str, message: B2S_DisableZstdCustom, now: float
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber to disable
        zstd compression previously enabled with the given identifier

        Args:
            url (str): websocket:<nonce>:<ctr>, unique to this request
            message (B2S_DisableZstdCustom): the disable zstd custom message from the broadcaster
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """

    async def authorize_stateful_continue_notify(
        self, /, *, tracing: bytes, identifier: bytes, part_id: int, now: float
    ) -> Optional[str]:
        """Produces the authorization header to send to the subscriber to continue
        sending the message with the given identifier and part id over a stateful
        connection

        Args:
            tracing (bytes): the tracing data to send to the subscriber, may be empty
            identifier (bytes): the arbitrary identifier of the message being sent.
                this identifier was assigned by the subscriber
            part_id (bytes): the part id that was received by the broadcaster
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns:
            str, None: the authorization header to use, if any
        """

    async def is_stateful_continue_notify_allowed(
        self, /, *, message: B2S_ContinueNotify, now: float
    ) -> AuthResult:
        """Checks the authorization header posted to the subscriber to continue
        sending the message with the given identifier and part id

        Args:
            message (B2S_ContinueNotify): the continue notify message from the broadcaster
            now (float): the current time in seconds since the epoch, as if from `time.time()`

        Returns: AuthResult
        """


class AuthConfig(ToBroadcasterAuthConfig, ToSubscriberAuthConfig, Protocol): ...


class AuthConfigFromParts:
    """Convenience class to combine an incoming and outgoing auth config into an
    auth config
    """

    def __init__(
        self,
        to_broadcaster: ToBroadcasterAuthConfig,
        to_subscriber: ToSubscriberAuthConfig,
    ):
        self.to_broadcaster = to_broadcaster
        self.to_subscriber = to_subscriber

    async def setup_to_broadcaster_auth(self) -> None:
        await self.to_broadcaster.setup_to_broadcaster_auth()

    async def teardown_to_broadcaster_auth(self) -> None:
        await self.to_broadcaster.teardown_to_broadcaster_auth()

    async def authorize_subscribe_exact(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_subscribe_exact(
            tracing=tracing, url=url, recovery=recovery, exact=exact, now=now
        )

    async def is_subscribe_exact_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_broadcaster.is_subscribe_exact_allowed(
            tracing=tracing,
            url=url,
            recovery=recovery,
            exact=exact,
            now=now,
            authorization=authorization,
        )

    async def authorize_subscribe_glob(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_subscribe_glob(
            tracing=tracing, url=url, recovery=recovery, glob=glob, now=now
        )

    async def is_subscribe_glob_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_broadcaster.is_subscribe_glob_allowed(
            tracing=tracing,
            url=url,
            recovery=recovery,
            glob=glob,
            now=now,
            authorization=authorization,
        )

    async def authorize_notify(
        self,
        /,
        *,
        tracing: bytes,
        topic: bytes,
        identifier: bytes,
        message_sha512: bytes,
        now: float,
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_notify(
            tracing=tracing,
            topic=topic,
            identifier=identifier,
            message_sha512=message_sha512,
            now=now,
        )

    async def is_notify_allowed(
        self,
        /,
        *,
        tracing: bytes,
        topic: bytes,
        identifier: bytes,
        message_sha512: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_broadcaster.is_notify_allowed(
            tracing=tracing,
            topic=topic,
            identifier=identifier,
            message_sha512=message_sha512,
            now=now,
            authorization=authorization,
        )

    async def authorize_stateful_configure(
        self,
        /,
        *,
        tracing: bytes,
        subscriber_nonce: bytes,
        enable_zstd: bool,
        enable_training: bool,
        initial_dict: int,
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_stateful_configure(
            tracing=tracing,
            subscriber_nonce=subscriber_nonce,
            enable_zstd=enable_zstd,
            enable_training=enable_training,
            initial_dict=initial_dict,
        )

    async def is_stateful_configure_allowed(
        self, /, *, message: S2B_Configure, now: float
    ) -> AuthResult:
        return await self.to_broadcaster.is_stateful_configure_allowed(
            message=message, now=now
        )

    async def authorize_check_subscriptions(
        self, /, *, tracing: bytes, url: str, now: float
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_check_subscriptions(
            tracing=tracing, url=url, now=now
        )

    async def is_check_subscriptions_allowed(
        self, /, *, tracing: bytes, url: str, now: float, authorization: Optional[str]
    ) -> AuthResult:
        return await self.to_broadcaster.is_check_subscriptions_allowed(
            tracing=tracing, url=url, now=now, authorization=authorization
        )

    async def authorize_set_subscriptions(
        self, /, *, tracing: bytes, url: str, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_set_subscriptions(
            tracing=tracing, url=url, strong_etag=strong_etag, now=now
        )

    async def is_set_subscriptions_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        strong_etag: StrongEtag,
        subscriptions: SetSubscriptionsInfo,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_broadcaster.is_set_subscriptions_allowed(
            tracing=tracing,
            url=url,
            strong_etag=strong_etag,
            subscriptions=subscriptions,
            now=now,
            authorization=authorization,
        )

    async def authorize_stateful_continue_receive(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        part_id: int,
        url: str,
        now: float,
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_stateful_continue_receive(
            tracing=tracing, identifier=identifier, part_id=part_id, url=url, now=now
        )

    async def is_stateful_continue_receive_allowed(
        self, /, *, url: str, message: S2B_ContinueReceive, now: float
    ) -> AuthResult:
        return await self.to_broadcaster.is_stateful_continue_receive_allowed(
            url=url, message=message, now=now
        )

    async def authorize_confirm_receive(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        num_subscribers: int,
        url: str,
        now: float,
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_confirm_receive(
            tracing=tracing,
            identifier=identifier,
            num_subscribers=num_subscribers,
            url=url,
            now=now,
        )

    async def is_confirm_receive_allowed(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        num_subscribers: int,
        url: str,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_broadcaster.is_confirm_receive_allowed(
            tracing=tracing,
            identifier=identifier,
            num_subscribers=num_subscribers,
            url=url,
            now=now,
            authorization=authorization,
        )

    async def authorize_confirm_missed(
        self, /, *, tracing: bytes, topic: bytes, url: str, now: float
    ) -> Optional[str]:
        return await self.to_broadcaster.authorize_confirm_missed(
            tracing=tracing, topic=topic, url=url, now=now
        )

    async def is_confirm_missed_allowed(
        self,
        /,
        *,
        tracing: bytes,
        topic: bytes,
        url: str,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_broadcaster.is_confirm_missed_allowed(
            tracing=tracing,
            topic=topic,
            url=url,
            now=now,
            authorization=authorization,
        )

    async def setup_to_subscriber_auth(self) -> None:
        await self.to_subscriber.setup_to_subscriber_auth()

    async def teardown_to_subscriber_auth(self) -> None:
        await self.to_subscriber.teardown_to_subscriber_auth()

    async def authorize_receive(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        topic: bytes,
        message_sha512: bytes,
        identifier: bytes,
        now: float,
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_receive(
            tracing=tracing,
            url=url,
            topic=topic,
            message_sha512=message_sha512,
            identifier=identifier,
            now=now,
        )

    async def is_receive_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        topic: bytes,
        message_sha512: bytes,
        identifier: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_subscriber.is_receive_allowed(
            tracing=tracing,
            url=url,
            topic=topic,
            message_sha512=message_sha512,
            identifier=identifier,
            now=now,
            authorization=authorization,
        )

    async def authorize_missed(
        self, /, *, tracing: bytes, recovery: str, topic: bytes, now: float
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_missed(
            tracing=tracing, recovery=recovery, topic=topic, now=now
        )

    async def is_missed_allowed(
        self,
        /,
        *,
        tracing: bytes,
        recovery: str,
        topic: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_subscriber.is_missed_allowed(
            tracing=tracing,
            recovery=recovery,
            topic=topic,
            now=now,
            authorization=authorization,
        )

    async def authorize_confirm_subscribe_exact(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_confirm_subscribe_exact(
            tracing=tracing, url=url, recovery=recovery, exact=exact, now=now
        )

    async def is_confirm_subscribe_exact_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_subscriber.is_confirm_subscribe_exact_allowed(
            tracing=tracing,
            url=url,
            recovery=recovery,
            exact=exact,
            now=now,
            authorization=authorization,
        )

    async def authorize_confirm_subscribe_glob(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_confirm_subscribe_glob(
            tracing=tracing, url=url, recovery=recovery, glob=glob, now=now
        )

    async def is_confirm_subscribe_glob_allowed(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
        authorization: Optional[str],
    ) -> AuthResult:
        return await self.to_subscriber.is_confirm_subscribe_glob_allowed(
            tracing=tracing,
            url=url,
            recovery=recovery,
            glob=glob,
            now=now,
            authorization=authorization,
        )

    async def authorize_confirm_notify(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        subscribers: int,
        topic: bytes,
        message_sha512: bytes,
        now: float,
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_confirm_notify(
            tracing=tracing,
            identifier=identifier,
            subscribers=subscribers,
            topic=topic,
            message_sha512=message_sha512,
            now=now,
        )

    async def is_confirm_notify_allowed(
        self,
        /,
        *,
        tracing: bytes,
        identifier: bytes,
        subscribers: int,
        topic: bytes,
        message_sha512: bytes,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        return await self.to_subscriber.is_confirm_notify_allowed(
            tracing=tracing,
            identifier=identifier,
            subscribers=subscribers,
            topic=topic,
            message_sha512=message_sha512,
            authorization=authorization,
            now=now,
        )

    async def authorize_check_subscriptions_response(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        now: float,
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_check_subscriptions_response(
            tracing=tracing, strong_etag=strong_etag, now=now
        )

    async def is_check_subscription_response_allowed(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        return await self.to_subscriber.is_check_subscription_response_allowed(
            tracing=tracing,
            strong_etag=strong_etag,
            authorization=authorization,
            now=now,
        )

    async def authorize_set_subscriptions_response(
        self, /, *, tracing: bytes, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_set_subscriptions_response(
            tracing=tracing, strong_etag=strong_etag, now=now
        )

    async def is_set_subscription_response_allowed(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        return await self.to_subscriber.is_set_subscription_response_allowed(
            tracing=tracing,
            strong_etag=strong_etag,
            authorization=authorization,
            now=now,
        )

    async def authorize_stateful_confirm_configure(
        self, /, *, broadcaster_nonce: bytes, tracing: bytes, now: float
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_stateful_confirm_configure(
            broadcaster_nonce=broadcaster_nonce, tracing=tracing, now=now
        )

    async def is_stateful_confirm_configure_allowed(
        self, /, *, message: B2S_ConfirmConfigure, now: float
    ) -> AuthResult:
        return await self.to_subscriber.is_stateful_confirm_configure_allowed(
            message=message, now=now
        )

    async def authorize_stateful_enable_zstd_preset(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        compressor_identifier: int,
        compression_level: int,
        min_size: int,
        max_size: int,
        now: float,
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_stateful_enable_zstd_preset(
            tracing=tracing,
            url=url,
            compressor_identifier=compressor_identifier,
            compression_level=compression_level,
            min_size=min_size,
            max_size=max_size,
            now=now,
        )

    async def is_stateful_enable_zstd_preset_allowed(
        self, /, *, url: str, message: B2S_EnableZstdPreset, now: float
    ) -> AuthResult:
        return await self.to_subscriber.is_stateful_enable_zstd_preset_allowed(
            url=url, message=message, now=now
        )

    async def authorize_stateful_enable_zstd_custom(
        self,
        /,
        *,
        tracing: bytes,
        url: str,
        compressor_identifier: int,
        compression_level: int,
        min_size: int,
        max_size: int,
        sha512: bytes,
        now: float,
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_stateful_enable_zstd_custom(
            tracing=tracing,
            url=url,
            compressor_identifier=compressor_identifier,
            compression_level=compression_level,
            min_size=min_size,
            max_size=max_size,
            sha512=sha512,
            now=now,
        )

    async def is_stateful_enable_zstd_custom_allowed(
        self, /, *, url: str, message: B2S_EnableZstdCustom, now: float
    ) -> AuthResult:
        return await self.to_subscriber.is_stateful_enable_zstd_custom_allowed(
            url=url, message=message, now=now
        )

    async def authorize_stateful_disable_zstd_custom(
        self, /, *, tracing: bytes, compressor_identifier: int, url: str, now: float
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_stateful_disable_zstd_custom(
            tracing=tracing,
            compressor_identifier=compressor_identifier,
            url=url,
            now=now,
        )

    async def is_stateful_disable_zstd_custom_allowed(
        self, /, *, url: str, message: B2S_DisableZstdCustom, now: float
    ) -> AuthResult:
        return await self.to_subscriber.is_stateful_disable_zstd_custom_allowed(
            url=url, message=message, now=now
        )

    async def authorize_stateful_continue_notify(
        self, /, *, tracing: bytes, identifier: bytes, part_id: int, now: float
    ) -> Optional[str]:
        return await self.to_subscriber.authorize_stateful_continue_notify(
            tracing=tracing, identifier=identifier, part_id=part_id, now=now
        )

    async def is_stateful_continue_notify_allowed(
        self, /, *, message: B2S_ContinueNotify, now: float
    ) -> AuthResult:
        return await self.to_subscriber.is_stateful_continue_notify_allowed(
            message=message, now=now
        )


if TYPE_CHECKING:
    _: Type[AuthConfig] = AuthConfigFromParts
