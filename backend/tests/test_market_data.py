import pytest

from app.services.market_data.service import (
    get_option_chain,
    get_provider,
)

from datetime import date

from app.services.market_data.providers.massive import (
    MassiveOptionChainProvider,
)

def test_mock_option_chain():
    snapshot = get_option_chain(
        "SPY",
        provider="mock",
    )

    assert snapshot.symbol == "SPY"
    assert snapshot.spot > 0
    assert len(
        snapshot.expiries
    ) == 2
    assert len(
        snapshot.quotes
    ) > 0


def test_mock_quotes_have_spreads():
    snapshot = get_option_chain(
        "AAPL",
        provider="mock",
    )

    for quote in snapshot.quotes:
        assert quote.bid is not None
        assert quote.ask is not None
        assert (
            quote.ask
            >= quote.bid
        )


def test_unknown_provider_rejected():
    with pytest.raises(
        ValueError
    ):
        get_provider(
            "does_not_exist"
        )


def test_alpha_vantage_requires_key(
    monkeypatch,
):
    monkeypatch.delenv(
        "ALPHA_VANTAGE_API_KEY",
        raising=False,
    )

    with pytest.raises(
        ValueError
    ):
        get_provider(
            "alpha_vantage"
        )

def test_massive_requires_key(
    monkeypatch,
):
    monkeypatch.delenv(
        "MASSIVE_API_KEY",
        raising=False,
    )

    with pytest.raises(
        ValueError
    ):
        get_provider(
            "massive"
        )

def test_representative_expiry_selection():
    provider = MassiveOptionChainProvider(
        api_key="test"
    )

    today = date(
        2026,
        8,
        22,
    )

    expiries = [
        "2026-08-29",
        "2026-09-05",
        "2026-09-19",
        "2026-10-03",
        "2026-11-21",
    ]

    selected = (
        provider
        ._select_representative_expiries(
            expiries,
            today,
        )
    )

    assert len(selected) == 2

    assert selected[0] != selected[1]

    # TARGET_EXPIRY_DAYS = (14, 45)
    #
    # 2026-09-05 = 14 days
    # 2026-10-03 = 42 days
    #
    # These should therefore be the
    # representative expiries selected.
    assert selected == [
        "2026-09-05",
        "2026-10-03",
    ]

def test_select_matched_pairs_prefers_near_atm_strikes():
        provider = MassiveOptionChainProvider(
            api_key="test"
        )

        spot = 100.0

        contracts = [
            {
                "ticker":
                    "CALL_90",
                "strike_price":
                    90.0,
                "contract_type":
                    "call",
            },
            {
                "ticker":
                    "PUT_90",
                "strike_price":
                    90.0,
                "contract_type":
                    "put",
            },
            {
                "ticker":
                    "CALL_95",
                "strike_price":
                    95.0,
                "contract_type":
                    "call",
            },
            {
                "ticker":
                    "PUT_95",
                "strike_price":
                    95.0,
                "contract_type":
                    "put",
            },
            {
                "ticker":
                    "CALL_100",
                "strike_price":
                    100.0,
                "contract_type":
                    "call",
            },
            {
                "ticker":
                    "PUT_100",
                "strike_price":
                    100.0,
                "contract_type":
                    "put",
            },
            {
                "ticker":
                    "CALL_105",
                "strike_price":
                    105.0,
                "contract_type":
                    "call",
            },
            {
                "ticker":
                    "PUT_105",
                "strike_price":
                    105.0,
                "contract_type":
                    "put",
            },
            {
                "ticker":
                    "CALL_110",
                "strike_price":
                    110.0,
                "contract_type":
                    "call",
            },
            {
                "ticker":
                    "PUT_110",
                "strike_price":
                    110.0,
                "contract_type":
                    "put",
            },
        ]

        pairs = (
            provider
            ._select_matched_pairs(
                contracts,
                spot,
            )
        )

        assert len(
            pairs
        ) == 3

        selected_strikes = [
            float(
                call_contract[
                    "strike_price"
                ]
            )
            for (
                call_contract,
                _
            ) in pairs
        ]

        assert selected_strikes[0] == 100.0

        assert set(
            selected_strikes
        ) == {
            95.0,
            100.0,
            105.0,
        }

        for (
            call_contract,
            put_contract,
        ) in pairs:
            assert (
                call_contract[
                    "strike_price"
                ]
                == put_contract[
                    "strike_price"
                ]
            )

            assert (
                call_contract[
                    "contract_type"
                ]
                == "call"
            )

            assert (
                put_contract[
                    "contract_type"
                ]
                == "put"
            )

def test_service_option_chain_cache():
    from app.services.market_data.service import (
        clear_option_chain_cache,
        get_option_chain,
    )

    clear_option_chain_cache()

    first = (
        get_option_chain(
            symbol="SPY",
            provider="mock",
        )
    )

    second = (
        get_option_chain(
            symbol="SPY",
            provider="mock",
        )
    )

    assert (
        first.cache_hit
        is False
    )

    assert (
        second.cache_hit
        is True
    )

    assert (
        second
        .cache_age_seconds
        is not None
    )

    assert (
        second
        .cache_ttl_seconds
        == 300
    )


def test_refresh_bypasses_service_cache():
    from app.services.market_data.service import (
        clear_option_chain_cache,
        get_option_chain,
    )

    clear_option_chain_cache()

    _ = (
        get_option_chain(
            symbol="SPY",
            provider="mock",
        )
    )

    refreshed = (
        get_option_chain(
            symbol="SPY",
            provider="mock",
            use_cache=False,
        )
    )

    assert (
        refreshed.cache_hit
        is False
    )