from typing import TYPE_CHECKING, Optional, Type

from lonelypsp.auth.config import (
    AuthResult,
    ToBroadcasterAuthConfig,
    ToSubscriberAuthConfig,
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


class ToBroadcasterNoneAuth:
    """Sets up and allows a broadcaster that does not block any incoming requests.

    In order for this to be secure it must only be possible for trusted clients
    to connect to the server (e.g., by setting up TLS mutual auth at the binding
    level)
    """

    async def setup_to_broadcaster_auth(self) -> None: ...
    async def teardown_to_broadcaster_auth(self) -> None: ...

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
        return None

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
        return AuthResult.OK

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
        return None

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
        return AuthResult.OK

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
        return None

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
        return AuthResult.OK

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
        return None

    async def is_stateful_configure_allowed(
        self, /, *, message: S2B_Configure, now: float
    ) -> AuthResult:
        return AuthResult.OK

    async def authorize_check_subscriptions(
        self, /, *, tracing: bytes, url: str, now: float
    ) -> Optional[str]:
        return None

    async def is_check_subscriptions_allowed(
        self, /, *, tracing: bytes, url: str, now: float, authorization: Optional[str]
    ) -> AuthResult:
        return AuthResult.OK

    async def authorize_set_subscriptions(
        self, /, *, tracing: bytes, url: str, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        return None

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
        return AuthResult.OK

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
        return None

    async def is_stateful_continue_receive_allowed(
        self, /, *, url: str, message: S2B_ContinueReceive, now: float
    ) -> AuthResult:
        return AuthResult.OK

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
        return None

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
        return AuthResult.OK

    async def authorize_confirm_missed(
        self, /, *, tracing: bytes, topic: bytes, url: str, now: float
    ) -> Optional[str]:
        return None

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
        return AuthResult.OK


class ToSubscriberNoneAuth:
    """Sets up and allows a subscriber that does not block any incoming requests.

    In order for this to be secure, the subscribers must only be able to receive
    messages from trusted clients.
    """

    async def setup_to_subscriber_auth(self) -> None: ...
    async def teardown_to_subscriber_auth(self) -> None: ...

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
        return None

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
        return AuthResult.OK

    async def authorize_missed(
        self, /, *, tracing: bytes, recovery: str, topic: bytes, now: float
    ) -> Optional[str]:
        return None

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
        return AuthResult.OK

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
        return None

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
        return AuthResult.OK

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
        return None

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
        return AuthResult.OK

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
        return None

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
        return AuthResult.OK

    async def authorize_check_subscriptions_response(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        now: float,
    ) -> Optional[str]:
        return None

    async def is_check_subscription_response_allowed(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        return AuthResult.OK

    async def authorize_set_subscriptions_response(
        self, /, *, tracing: bytes, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        return None

    async def is_set_subscription_response_allowed(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        return AuthResult.OK

    async def authorize_stateful_confirm_configure(
        self, /, *, broadcaster_nonce: bytes, tracing: bytes, now: float
    ) -> Optional[str]:
        return None

    async def is_stateful_confirm_configure_allowed(
        self, /, *, message: B2S_ConfirmConfigure, now: float
    ) -> AuthResult:
        return AuthResult.OK

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
        return None

    async def is_stateful_enable_zstd_preset_allowed(
        self, /, *, url: str, message: B2S_EnableZstdPreset, now: float
    ) -> AuthResult:
        return AuthResult.OK

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
        return None

    async def is_stateful_enable_zstd_custom_allowed(
        self, /, *, url: str, message: B2S_EnableZstdCustom, now: float
    ) -> AuthResult:
        return AuthResult.OK

    async def authorize_stateful_disable_zstd_custom(
        self, /, *, tracing: bytes, compressor_identifier: int, url: str, now: float
    ) -> Optional[str]:
        return None

    async def is_stateful_disable_zstd_custom_allowed(
        self, /, *, url: str, message: B2S_DisableZstdCustom, now: float
    ) -> AuthResult:
        return AuthResult.OK

    async def authorize_stateful_continue_notify(
        self, /, *, tracing: bytes, identifier: bytes, part_id: int, now: float
    ) -> Optional[str]:
        return None

    async def is_stateful_continue_notify_allowed(
        self, /, *, message: B2S_ContinueNotify, now: float
    ) -> AuthResult:
        return AuthResult.OK


if TYPE_CHECKING:
    _: Type[ToBroadcasterAuthConfig] = ToBroadcasterNoneAuth
    __: Type[ToSubscriberAuthConfig] = ToSubscriberNoneAuth
