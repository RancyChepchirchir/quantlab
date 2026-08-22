from dataclasses import dataclass
from dataclasses import replace
from time import time
from typing import Dict, Optional, Tuple

from app.services.market_data.cache import (
    OptionChainCache,
)

from app.services.market_data.errors import (
    MarketDataProviderError,
)

from app.services.market_data.provider import (
    OptionChainProvider,
)

from app.services.market_data.providers.alpha_vantage import (
    AlphaVantageOptionChainProvider,
)

from app.services.market_data.providers.massive import (
    MassiveOptionChainProvider,
)

from app.services.market_data.providers.mock import (
    MockOptionChainProvider,
)

from app.services.market_data.types import (
    OptionChainSnapshot,
)


OPTION_CHAIN_CACHE_TTL_SECONDS = 300

# If an upstream provider says we are rate
# limited or temporarily unavailable, avoid
# immediately hitting it again.
PROVIDER_FAILURE_COOLDOWN_SECONDS = 60


_option_chain_cache = OptionChainCache(
    ttl_seconds=OPTION_CHAIN_CACHE_TTL_SECONDS
)


@dataclass(frozen=True)
class CachedProviderFailure:
    error: MarketDataProviderError
    stored_at: float


_provider_failure_cache: Dict[
    Tuple[str, str],
    CachedProviderFailure,
] = {}


def _cache_key(
    provider: str,
    symbol: str,
) -> Tuple[str, str]:
    return (
        provider
        .strip()
        .lower(),

        symbol
        .strip()
        .upper(),
    )


def get_provider(
    provider: str,
) -> OptionChainProvider:
    """
    Return a configured market-data provider.
    """

    normalized = (
        provider
        .strip()
        .lower()
    )

    if normalized == "mock":
        return (
            MockOptionChainProvider()
        )

    if normalized in {
        "alpha_vantage",
        "alphavantage",
        "alpha-vantage",
    }:
        return (
            AlphaVantageOptionChainProvider()
        )

    if normalized == "massive":
        return (
            MassiveOptionChainProvider()
        )

    raise ValueError(
        "Unknown market-data "
        f"provider: {provider}"
    )


def get_market_data_provider(
    provider: str,
) -> OptionChainProvider:
    """
    Descriptive alias retained alongside
    the original get_provider API.
    """

    return get_provider(
        provider
    )


def _get_cached_provider_failure(
    provider: str,
    symbol: str,
) -> Optional[
    MarketDataProviderError
]:
    key = _cache_key(
        provider,
        symbol,
    )

    cached = (
        _provider_failure_cache.get(
            key
        )
    )

    if cached is None:
        return None

    age = (
        time()
        - cached.stored_at
    )

    if (
        age
        >= PROVIDER_FAILURE_COOLDOWN_SECONDS
    ):
        _provider_failure_cache.pop(
            key,
            None,
        )

        return None

    remaining = max(
        PROVIDER_FAILURE_COOLDOWN_SECONDS
        - age,
        0.0,
    )

    original = (
        cached.error
    )

    return MarketDataProviderError(
        message=(
            original.message
        ),
        status_code=(
            original.status_code
        ),
        provider=(
            original.provider
        ),
        upstream_status=(
            original.upstream_status
        ),
        retryable=(
            original.retryable
        ),
        cached=True,
        retry_after_seconds=(
            remaining
        ),
    )


def _store_provider_failure(
    provider: str,
    symbol: str,
    error: MarketDataProviderError,
) -> None:
    """
    Cache only retryable provider failures.

    Configuration and entitlement failures
    should not become transient cooldown
    entries because the user may fix them
    immediately.
    """

    if not error.retryable:
        return

    key = _cache_key(
        provider,
        symbol,
    )

    _provider_failure_cache[
        key
    ] = CachedProviderFailure(
        error=error,
        stored_at=time(),
    )


def _clear_provider_failure(
    provider: str,
    symbol: str,
) -> None:
    key = _cache_key(
        provider,
        symbol,
    )

    _provider_failure_cache.pop(
        key,
        None,
    )


def get_option_chain(
    symbol: str,
    provider: str = "mock",
    use_cache: bool = True,
) -> OptionChainSnapshot:
    """
    Load an option-chain snapshot.

    Order of operations:

        successful snapshot cache
                ↓
        provider-failure cooldown
                ↓
        live provider request
                ↓
        cache successful response
    """

    normalized_symbol = (
        symbol
        .strip()
        .upper()
    )

    normalized_provider = (
        provider
        .strip()
        .lower()
    )

    if not normalized_symbol:
        raise ValueError(
            "Symbol must not be empty."
        )

    # -----------------------------------------------------
    # 1. Successful-chain cache
    # -----------------------------------------------------

    if use_cache:
        cached = (
            _option_chain_cache.get(
                provider=(
                    normalized_provider
                ),
                symbol=(
                    normalized_symbol
                ),
            )
        )

        if cached is not None:
            (
                snapshot,
                age_seconds,
            ) = cached

            return replace(
                snapshot,
                cache_hit=True,
                cache_age_seconds=float(
                    age_seconds
                ),
                cache_ttl_seconds=(
                    OPTION_CHAIN_CACHE_TTL_SECONDS
                ),
            )

    # -----------------------------------------------------
    # 2. Provider-failure cooldown
    #
    # refresh=true bypasses both successful
    # cache and failure cooldown.
    # -----------------------------------------------------

    if use_cache:
        cached_failure = (
            _get_cached_provider_failure(
                provider=(
                    normalized_provider
                ),
                symbol=(
                    normalized_symbol
                ),
            )
        )

        if (
            cached_failure
            is not None
        ):
            raise cached_failure

    # -----------------------------------------------------
    # 3. Live provider request
    # -----------------------------------------------------

    client = get_provider(
        normalized_provider
    )

    try:
        snapshot = (
            client.get_option_chain(
                normalized_symbol
            )
        )

    except MarketDataProviderError as error:
        if use_cache:
            _store_provider_failure(
                provider=(
                    normalized_provider
                ),
                symbol=(
                    normalized_symbol
                ),
                error=error,
            )

        raise

    # -----------------------------------------------------
    # 4. Successful response clears any old
    #    provider failure for this symbol.
    # -----------------------------------------------------

    _clear_provider_failure(
        provider=(
            normalized_provider
        ),
        symbol=(
            normalized_symbol
        ),
    )

    fresh_snapshot = replace(
        snapshot,
        cache_hit=False,
        cache_age_seconds=0.0,
        cache_ttl_seconds=(
            OPTION_CHAIN_CACHE_TTL_SECONDS
        ),
    )

    # -----------------------------------------------------
    # 5. Cache successful chain
    # -----------------------------------------------------

    if use_cache:
        _option_chain_cache.set(
            provider=(
                normalized_provider
            ),
            symbol=(
                normalized_symbol
            ),
            snapshot=(
                fresh_snapshot
            ),
        )

    return fresh_snapshot


def clear_option_chain_cache(
    provider: Optional[str] = None,
    symbol: Optional[str] = None,
) -> None:
    """
    Clear successful-chain cache entries.
    """

    if (
        provider is None
        and symbol is None
    ):
        _option_chain_cache.clear()
        return

    if (
        provider is None
        or symbol is None
    ):
        raise ValueError(
            "provider and symbol must "
            "both be supplied when "
            "invalidating one cache entry."
        )

    _option_chain_cache.invalidate(
        provider=provider,
        symbol=symbol,
    )


def clear_provider_failure_cache(
    provider: Optional[str] = None,
    symbol: Optional[str] = None,
) -> None:
    """
    Clear provider cooldown state.
    """

    if (
        provider is None
        and symbol is None
    ):
        _provider_failure_cache.clear()
        return

    if (
        provider is None
        or symbol is None
    ):
        raise ValueError(
            "provider and symbol must "
            "both be supplied when "
            "invalidating one failure entry."
        )

    _clear_provider_failure(
        provider=provider,
        symbol=symbol,
    )


def option_chain_cache_size() -> int:
    return (
        _option_chain_cache.size()
    )


def provider_failure_cache_size() -> int:
    return len(
        _provider_failure_cache
    )