import pytest

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.greeks import (
    black_scholes_greeks,
)


def test_call_greeks():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    greeks = black_scholes_greeks(
        inputs,
        option_type="call",
    )

    assert greeks.delta == pytest.approx(
        0.6368,
        abs=1e-3,
    )

    assert greeks.gamma == pytest.approx(
        0.01876,
        abs=1e-4,
    )

    assert greeks.vega == pytest.approx(
        37.524,
        abs=1e-2,
    )

    assert greeks.theta < 0

    assert greeks.rho > 0


def test_put_delta_negative():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    greeks = black_scholes_greeks(
        inputs,
        option_type="put",
    )

    assert greeks.delta < 0
    assert greeks.gamma > 0
    assert greeks.vega > 0
    assert greeks.rho < 0