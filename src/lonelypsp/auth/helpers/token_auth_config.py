import hmac
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


class ToBroadcasterTokenAuth:
    """Allows and produces the authorization header to the broadcaster in
    the consistent form `f"Bearer {token}"`

    In order for this to be secure, the headers must be encrypted, typically via
    HTTPS.
    """

    def __init__(self, /, *, token: str) -> None:
        self.expecting = f"Bearer {token}"
        """The exact authorization header the broadcaster receives"""

    async def setup_to_broadcaster_auth(self) -> None: ...
    async def teardown_to_broadcaster_auth(self) -> None: ...

    def _check_header(self, authorization: Optional[str]) -> AuthResult:
        if authorization is None:
            return AuthResult.UNAUTHORIZED
        if not hmac.compare_digest(authorization, self.expecting):
            return AuthResult.FORBIDDEN
        return AuthResult.OK

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
        return self.expecting

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
        return self._check_header(authorization)

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
        return self.expecting

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
        return self._check_header(authorization)

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
        return self.expecting

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
        return self._check_header(authorization)

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
        return self.expecting

    async def is_stateful_configure_allowed(
        self, /, *, message: S2B_Configure, now: float
    ) -> AuthResult:
        return self._check_header(message.authorization)

    async def authorize_check_subscriptions(
        self, /, *, tracing: bytes, url: str, now: float
    ) -> Optional[str]:
        return self.expecting

    async def is_check_subscriptions_allowed(
        self, /, *, tracing: bytes, url: str, now: float, authorization: Optional[str]
    ) -> AuthResult:
        return self._check_header(authorization)

    async def authorize_set_subscriptions(
        self, /, *, tracing: bytes, url: str, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        return self.expecting

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
        return self._check_header(authorization)

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
        return self.expecting

    async def is_stateful_continue_receive_allowed(
        self, /, *, url: str, message: S2B_ContinueReceive, now: float
    ) -> AuthResult:
        return self._check_header(message.authorization)

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
        return self.expecting

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
        return self._check_header(authorization)

    async def authorize_confirm_missed(
        self, /, *, tracing: bytes, topic: bytes, url: str, now: float
    ) -> Optional[str]:
        return self.expecting

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
        return self._check_header(authorization)


class ToSubscriberTokenAuth:
    """Allows and produces the authorization header to the subscriber in
    the consistent form `f"Bearer {token}"`

    In order for this to be secure, the clients must verify the header matches
    what they expect and the headers must be encrypted, typically via HTTPS.
    """

    def __init__(self, /, *, token: str) -> None:
        self.expecting = f"Bearer {token}"
        """The authorization header that the subscriber receives"""

    async def setup_to_subscriber_auth(self) -> None: ...
    async def teardown_to_subscriber_auth(self) -> None: ...

    def _check_header(self, authorization: Optional[str]) -> AuthResult:
        if authorization is None:
            return AuthResult.UNAUTHORIZED
        if not hmac.compare_digest(authorization, self.expecting):
            return AuthResult.FORBIDDEN
        return AuthResult.OK

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
        return self.expecting

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
        return self._check_header(authorization)

    async def authorize_missed(
        self, /, *, tracing: bytes, recovery: str, topic: bytes, now: float
    ) -> Optional[str]:
        return self.expecting

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
        return self._check_header(authorization)

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
        return self.expecting

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
        return self._check_header(authorization)

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
        return self.expecting

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
        return self._check_header(authorization)

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
        return self.expecting

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
        return self._check_header(authorization)

    async def authorize_check_subscriptions_response(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        now: float,
    ) -> Optional[str]:
        return self.expecting

    async def is_check_subscription_response_allowed(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        return self._check_header(authorization)

    async def authorize_set_subscriptions_response(
        self, /, *, tracing: bytes, strong_etag: StrongEtag, now: float
    ) -> Optional[str]:
        return self.expecting

    async def is_set_subscription_response_allowed(
        self,
        /,
        *,
        tracing: bytes,
        strong_etag: StrongEtag,
        authorization: Optional[str],
        now: float,
    ) -> AuthResult:
        return self._check_header(authorization)

    async def authorize_stateful_confirm_configure(
        self, /, *, broadcaster_nonce: bytes, tracing: bytes, now: float
    ) -> Optional[str]:
        return self.expecting

    async def is_stateful_confirm_configure_allowed(
        self, /, *, message: B2S_ConfirmConfigure, now: float
    ) -> AuthResult:
        return self._check_header(message.authorization)

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
        return self.expecting

    async def is_stateful_enable_zstd_preset_allowed(
        self, /, *, url: str, message: B2S_EnableZstdPreset, now: float
    ) -> AuthResult:
        return self._check_header(message.authorization)

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
        return self.expecting

    async def is_stateful_enable_zstd_custom_allowed(
        self, /, *, url: str, message: B2S_EnableZstdCustom, now: float
    ) -> AuthResult:
        return self._check_header(message.authorization)

    async def authorize_stateful_disable_zstd_custom(
        self, /, *, tracing: bytes, compressor_identifier: int, url: str, now: float
    ) -> Optional[str]:
        return self.expecting

    async def is_stateful_disable_zstd_custom_allowed(
        self, /, *, url: str, message: B2S_DisableZstdCustom, now: float
    ) -> AuthResult:
        return self._check_header(message.authorization)

    async def authorize_stateful_continue_notify(
        self, /, *, tracing: bytes, identifier: bytes, part_id: int, now: float
    ) -> Optional[str]:
        return self.expecting

    async def is_stateful_continue_notify_allowed(
        self, /, *, message: B2S_ContinueNotify, now: float
    ) -> AuthResult:
        return self._check_header(message.authorization)


if TYPE_CHECKING:
    _: Type[ToBroadcasterAuthConfig] = ToBroadcasterTokenAuth
    __: Type[ToSubscriberAuthConfig] = ToSubscriberTokenAuth
