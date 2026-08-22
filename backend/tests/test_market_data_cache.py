from time import sleep

import pytest

from app.services.market_data.cache import (
    OptionChainCache,
)

from app.services.market_data.types import (
    OptionChainQuote,
    OptionChainSnapshot,
)


def make_snapshot() -> OptionChainSnapshot:
    quote = (
        OptionChainQuote(
            symbol="SPY",
            expiry="2026-09-18",
            option_type="call",
            strike=100.0,
            bid=5.0,
            ask=5.2,
            last=5.1,
            volume=100,
            open_interest=200,
            implied_volatility=None,
            source="test",
        )
    )

    return (
        OptionChainSnapshot(
            symbol="SPY",
            spot=100.0,
            currency="USD",
            expiries=[
                "2026-09-18"
            ],
            quotes=[
                quote
            ],
            source="test",
            returned_quote_count=1,
        )
    )


def test_cache_miss():
    cache = (
        OptionChainCache(
            ttl_seconds=10
        )
    )

    result = (
        cache.get(
            provider="massive",
            symbol="SPY",
        )
    )

    assert result is None


def test_cache_hit():
    cache = (
        OptionChainCache(
            ttl_seconds=10
        )
    )

    snapshot = (
        make_snapshot()
    )

    cache.set(
        provider="massive",
        symbol="SPY",
        snapshot=snapshot,
    )

    result = (
        cache.get(
            provider="massive",
            symbol="SPY",
        )
    )

    assert result is not None

    cached_snapshot, age = (
        result
    )

    assert (
        cached_snapshot.symbol
        == "SPY"
    )

    assert age >= 0.0


def test_cache_normalizes_key():
    cache = (
        OptionChainCache(
            ttl_seconds=10
        )
    )

    cache.set(
        provider="Massive",
        symbol="spy",
        snapshot=(
            make_snapshot()
        ),
    )

    result = (
        cache.get(
            provider="massive",
            symbol="SPY",
        )
    )

    assert result is not None


def test_cache_expires():
    cache = (
        OptionChainCache(
            ttl_seconds=1
        )
    )

    cache.set(
        provider="massive",
        symbol="SPY",
        snapshot=(
            make_snapshot()
        ),
    )

    sleep(
        1.05
    )

    result = (
        cache.get(
            provider="massive",
            symbol="SPY",
        )
    )

    assert result is None


def test_cache_invalidate():
    cache = (
        OptionChainCache(
            ttl_seconds=10
        )
    )

    cache.set(
        provider="massive",
        symbol="SPY",
        snapshot=(
            make_snapshot()
        ),
    )

    cache.invalidate(
        provider="massive",
        symbol="SPY",
    )

    assert (
        cache.get(
            provider="massive",
            symbol="SPY",
        )
        is None
    )


def test_cache_clear():
    cache = (
        OptionChainCache(
            ttl_seconds=10
        )
    )

    snapshot = (
        make_snapshot()
    )

    cache.set(
        provider="massive",
        symbol="SPY",
        snapshot=snapshot,
    )

    cache.set(
        provider="mock",
        symbol="AAPL",
        snapshot=snapshot,
    )

    assert (
        cache.size()
        == 2
    )

    cache.clear()

    assert (
        cache.size()
        == 0
    )


def test_invalid_cache_ttl_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "ttl_seconds must "
            "be positive"
        ),
    ):
        OptionChainCache(
            ttl_seconds=0
        )