from math import exp

import pytest

from app.models.black_scholes import (
    OptionInputs,
    european_call,
    european_put,
)


def test_put_call_parity():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    call = european_call(inputs)
    put = european_put(inputs)

    lhs = call - put

    rhs = (
        inputs.spot
        * exp(
            -inputs.dividend_yield
            * inputs.maturity
        )
        - inputs.strike
        * exp(
            -inputs.rate
            * inputs.maturity
        )
    )

    assert lhs == pytest.approx(
        rhs,
        rel=1e-10,
        abs=1e-10,
    )