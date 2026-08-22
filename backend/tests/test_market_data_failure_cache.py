import pytest

from app.services.market_data.errors import (
    MarketDataProviderError,
    MarketDataRateLimitError,
)

import app.services.market_data.service as service

from app.services.market_data.service import (
    clear_option_chain_cache,
    clear_provider_failure_cache,
    get_option_chain,
    provider_failure_cache_size,
)


class RateLimitedProvider:
    def __init__(
        self,
    ):
        self.call_count = 0

    def get_option_chain(
        self,
        symbol: str,
    ):
        self.call_count += 1

        raise MarketDataRateLimitError(
            message=(
                "Provider rate limit reached."
            ),
            provider="massive",
            upstream_status=429,
        )


def test_retryable_failure_is_cached(
    monkeypatch,
):
    clear_option_chain_cache()
    clear_provider_failure_cache()

    provider = (
        RateLimitedProvider()
    )

    monkeypatch.setattr(
        service,
        "get_provider",
        lambda provider_name:
            provider,
    )

    with pytest.raises(
        MarketDataRateLimitError
    ) as first:
        get_option_chain(
            symbol="SPY",
            provider="massive",
        )

    assert (
        first.value.cached
        is False
    )

    assert (
        provider.call_count
        == 1
    )

    assert (
        provider_failure_cache_size()
        == 1
    )

    with pytest.raises(
        MarketDataProviderError
    ) as second:
        get_option_chain(
            symbol="SPY",
            provider="massive",
        )

    assert (
        second.value.cached
        is True
    )

    assert (
        second.value.status_code
        == 429
    )

    assert (
        second.value.retry_after_seconds
        is not None
    )

    # Most important assertion:
    #
    # the second request does NOT contact
    # Massive again.
    assert (
        provider.call_count
        == 1
    )


def test_refresh_bypasses_failure_cache(
    monkeypatch,
):
    clear_option_chain_cache()
    clear_provider_failure_cache()

    provider = (
        RateLimitedProvider()
    )

    monkeypatch.setattr(
        service,
        "get_provider",
        lambda provider_name:
            provider,
    )

    with pytest.raises(
        MarketDataRateLimitError
    ):
        get_option_chain(
            symbol="SPY",
            provider="massive",
        )

    assert (
        provider.call_count
        == 1
    )

    with pytest.raises(
        MarketDataRateLimitError
    ):
        get_option_chain(
            symbol="SPY",
            provider="massive",
            use_cache=False,
        )

    # refresh/live mode really contacted
    # the provider again.
    assert (
        provider.call_count
        == 2
    )


def test_failure_cache_can_be_cleared(
    monkeypatch,
):
    clear_option_chain_cache()
    clear_provider_failure_cache()

    provider = (
        RateLimitedProvider()
    )

    monkeypatch.setattr(
        service,
        "get_provider",
        lambda provider_name:
            provider,
    )

    with pytest.raises(
        MarketDataRateLimitError
    ):
        get_option_chain(
            symbol="SPY",
            provider="massive",
        )

    assert (
        provider_failure_cache_size()
        == 1
    )

    clear_provider_failure_cache(
        provider="massive",
        symbol="SPY",
    )

    assert (
        provider_failure_cache_size()
        == 0
    )