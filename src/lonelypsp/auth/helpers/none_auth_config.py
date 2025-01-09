from typing import TYPE_CHECKING, Literal, Optional, Type

from lonelypsp.auth.set_subscriptions_info import SetSubscriptionsInfo
from lonelypsp.stateful.messages.configure import S2B_Configure
from lonelypsp.stateful.messages.confirm_configure import B2S_ConfirmConfigure
from lonelypsp.stateless.make_strong_etag import StrongEtag

if TYPE_CHECKING:
    from lonelypsp.auth.config import (
        ToBroadcasterAuthConfig,
        ToSubscriberAuthConfig,
    )


class ToBroadcasterNoneAuth:
    """Sets up and allows a broadcaster that does not block any incoming requests.

    In order for this to be secure it must only be possible for trusted clients
    to connect to the server (e.g., by setting up TLS mutual auth at the binding
    level)
    """

    async def setup_to_broadcaster_auth(self) -> None: ...
    async def teardown_to_broadcaster_auth(self) -> None: ...

    async def authorize_subscribe_exact(
        self, /, *, url: str, recovery: Optional[str], exact: bytes, now: float
    ) -> Optional[str]:
        return None

    async def is_subscribe_exact_allowed(
        self,
        /,
        *,
        url: str,
        recovery: Optional[str],
        exact: bytes,
        now: float,
        authorization: Optional[str],
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"

    async def authorize_subscribe_glob(
        self, /, *, url: str, recovery: Optional[str], glob: str, now: float
    ) -> Optional[str]:
        return None

    async def is_subscribe_glob_allowed(
        self,
        /,
        *,
        url: str,
        recovery: Optional[str],
        glob: str,
        now: float,
        authorization: Optional[str],
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"

    async def authorize_notify(
        self, /, *, topic: bytes, message_sha512: bytes, now: float
    ) -> Optional[str]:
        return None

    async def is_notify_allowed(
        self,
        /,
        *,
        topic: bytes,
        message_sha512: bytes,
        now: float,
        authorization: Optional[str],
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"

    async def authorize_stateful_configure(
        self,
        /,
        *,
        subscriber_nonce: bytes,
        enable_zstd: bool,
        enable_training: bool,
        initial_dict: int,
    ) -> Optional[str]:
        return None

    async def is_stateful_configure_allowed(
        self, /, *, message: S2B_Configure, now: float
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"

    async def authorize_check_subscriptions(
        self, /, *, url: str, now: float
    ) -> Optional[str]:
        return None

    async def is_check_subscriptions_allowed(
        self, /, *, url: str, now: float, authorization: Optional[str]
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"

    async def authorize_set_subscriptions(
        self, /, *, url: str, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        return None

    async def is_set_subscriptions_allowed(
        self,
        /,
        *,
        url: str,
        strong_etag: StrongEtag,
        subscriptions: SetSubscriptionsInfo,
        now: float,
        authorization: Optional[str],
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"


class ToSubscriberNoneAuth:
    """Sets up and allows a subscriber that does not block any incoming requests.

    In order for this to be secure, the subscribers must only be able to receive
    messages from trusted clients.
    """

    async def setup_to_subscriber_auth(self) -> None: ...
    async def teardown_to_subscriber_auth(self) -> None: ...

    async def authorize_receive(
        self, /, *, url: str, topic: bytes, message_sha512: bytes, now: float
    ) -> Optional[str]:
        return None

    async def is_receive_allowed(
        self,
        /,
        *,
        url: str,
        topic: bytes,
        message_sha512: bytes,
        now: float,
        authorization: Optional[str],
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"

    async def authorize_missed(
        self, /, *, recovery: str, topic: bytes, now: float
    ) -> Optional[str]:
        return None

    async def is_missed_allowed(
        self,
        /,
        *,
        recovery: str,
        topic: bytes,
        now: float,
        authorization: Optional[str],
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"

    async def authorize_stateful_confirm_configure(
        self, /, *, broadcaster_nonce: bytes, now: float
    ) -> Optional[str]:
        return None

    async def is_stateful_confirm_configure_allowed(
        self, /, *, message: B2S_ConfirmConfigure, now: float
    ) -> Literal["ok", "unauthorized", "forbidden", "unavailable"]:
        return "ok"


if TYPE_CHECKING:
    _: Type[ToBroadcasterAuthConfig] = ToBroadcasterNoneAuth
    __: Type[ToSubscriberAuthConfig] = ToSubscriberNoneAuth
