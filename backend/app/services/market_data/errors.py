from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketDataProviderError(Exception):
    message: str
    status_code: int = 502
    provider: Optional[str] = None
    upstream_status: Optional[int] = None
    retryable: bool = False

    cached: bool = False
    retry_after_seconds: Optional[float] = None

    def __str__(
        self,
    ) -> str:
        return self.message


class MarketDataConfigurationError(
    MarketDataProviderError
):
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            provider=provider,
            upstream_status=None,
            retryable=False,
            cached=False,
            retry_after_seconds=None,
        )


class MarketDataAuthorizationError(
    MarketDataProviderError
):
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        upstream_status: Optional[int] = None,
        cached: bool = False,
        retry_after_seconds: Optional[float] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            provider=provider,
            upstream_status=upstream_status,
            retryable=False,
            cached=cached,
            retry_after_seconds=retry_after_seconds,
        )


class MarketDataRateLimitError(
    MarketDataProviderError
):
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        upstream_status: Optional[int] = None,
        cached: bool = False,
        retry_after_seconds: Optional[float] = None,
    ):
        super().__init__(
            message=message,
            status_code=429,
            provider=provider,
            upstream_status=upstream_status,
            retryable=True,
            cached=cached,
            retry_after_seconds=retry_after_seconds,
        )


class MarketDataUpstreamError(
    MarketDataProviderError
):
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        upstream_status: Optional[int] = None,
        retryable: bool = True,
        cached: bool = False,
        retry_after_seconds: Optional[float] = None,
    ):
        super().__init__(
            message=message,
            status_code=502,
            provider=provider,
            upstream_status=upstream_status,
            retryable=retryable,
            cached=cached,
            retry_after_seconds=retry_after_seconds,
        )