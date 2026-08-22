from app.services.market_data.filtering import (
    filter_option_quotes,
)

from app.services.market_data.types import (
    OptionChainQuote,
)


def make_quote(
    strike: float,
    last: float,
):
    return OptionChainQuote(
        symbol="SPY",
        expiry="2026-09-18",
        option_type="call",
        strike=strike,
        bid=None,
        ask=None,
        last=last,
        volume=None,
        open_interest=None,
        implied_volatility=None,
        source="test",
    )


def test_filter_keeps_near_money_quotes():
    quotes = [
        make_quote(
            80,
            5.0,
        ),
        make_quote(
            100,
            10.0,
        ),
        make_quote(
            120,
            2.0,
        ),
    ]

    result = filter_option_quotes(
        quotes,
        spot=100,
    )

    assert len(result) == 3


def test_filter_rejects_far_otm_quotes():
    quotes = [
        make_quote(
            50,
            0.10,
        ),
        make_quote(
            100,
            10.0,
        ),
        make_quote(
            160,
            0.05,
        ),
    ]

    result = filter_option_quotes(
        quotes,
        spot=100,
    )

    assert len(result) == 1
    assert result[0].strike == 100


def test_filter_rejects_zero_price():
    quotes = [
        make_quote(
            100,
            0.0,
        ),
    ]

    result = filter_option_quotes(
        quotes,
        spot=100,
    )

    assert result == []