import pytest

from app.models.black_scholes import (
    OptionInputs,
    european_call,
    european_put,
)

from app.models.implied_volatility import (
    implied_volatility,
)


def test_call_implied_volatility():
    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    market_price = european_call(
        inputs
    )

    recovered = implied_volatility(
        inputs,
        market_price,
        option_type="call",
    )

    assert recovered == pytest.approx(
        0.20,
        abs=1e-6,
    )


def test_put_implied_volatility():
    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.30,
        maturity=1.0,
        dividend_yield=0.0,
    )

    market_price = european_put(
        inputs
    )

    recovered = implied_volatility(
        inputs,
        market_price,
        option_type="put",
    )

    assert recovered == pytest.approx(
        0.30,
        abs=1e-6,
    )


def test_invalid_market_price():
    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    with pytest.raises(
        ValueError
    ):
        implied_volatility(
            inputs,
            market_price=-1.0,
        )