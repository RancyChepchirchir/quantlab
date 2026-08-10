from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.monte_carlo import (
    monte_carlo_price,
)


def test_monte_carlo_call_positive():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    result = monte_carlo_price(
        inputs,
        option_type="call",
        simulations=100_000,
        seed=42,
    )

    assert result.price > 0


def test_black_scholes_inside_mc_confidence_interval():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    bs_price = european_call(inputs)

    result = monte_carlo_price(
        inputs,
        option_type="call",
        simulations=500_000,
        seed=42,
    )

    assert (
        result.confidence_low
        <= bs_price
        <= result.confidence_high
    )


def test_standard_error_positive():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    result = monte_carlo_price(
        inputs,
        simulations=10_000,
        seed=42,
    )

    assert result.standard_error > 0