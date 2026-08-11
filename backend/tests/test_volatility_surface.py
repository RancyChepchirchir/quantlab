import pytest

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.services.volatility_surface import (
    OptionQuote,
    calibrate_option_chain,
)


def test_option_chain_recovers_volatility():
    spot = 100.0
    rate = 0.05
    dividend_yield = 0.0
    true_volatility = 0.25

    quotes = []

    for strike in [
        80.0,
        90.0,
        100.0,
        110.0,
        120.0,
    ]:
        inputs = OptionInputs(
            spot=spot,
            strike=strike,
            rate=rate,
            volatility=true_volatility,
            maturity=1.0,
            dividend_yield=dividend_yield,
        )

        market_price = european_call(
            inputs
        )

        quotes.append(
            OptionQuote(
                strike=strike,
                maturity=1.0,
                market_price=market_price,
                option_type="call",
            )
        )

    calibrated = calibrate_option_chain(
        spot=spot,
        rate=rate,
        dividend_yield=dividend_yield,
        quotes=quotes,
    )

    assert len(calibrated) == 5

    for quote in calibrated:
        assert (
            quote.implied_volatility
            == pytest.approx(
                true_volatility,
                abs=1e-6,
            )
        )


def test_chain_preserves_quote_metadata():
    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=0.5,
        dividend_yield=0.0,
    )

    price = european_call(inputs)

    result = calibrate_option_chain(
        spot=100.0,
        rate=0.05,
        dividend_yield=0.0,
        quotes=[
            OptionQuote(
                strike=100.0,
                maturity=0.5,
                market_price=price,
                option_type="call",
            )
        ],
    )

    assert result[0].strike == 100.0
    assert result[0].maturity == 0.5
    assert result[0].market_price == price
    assert result[0].option_type == "call"