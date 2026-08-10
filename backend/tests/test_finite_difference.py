import pytest

from app.models.black_scholes import (
    OptionInputs,
    european_call,
    european_put,
)

from app.models.finite_difference import (
    crank_nicolson_price,
)


@pytest.fixture
def inputs():
    return OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )


def test_crank_nicolson_call_positive(
    inputs,
):
    result = crank_nicolson_price(
        inputs,
        option_type="call",
        space_steps=200,
        time_steps=200,
    )

    assert result.price > 0


def test_crank_nicolson_put_positive(
    inputs,
):
    result = crank_nicolson_price(
        inputs,
        option_type="put",
        space_steps=200,
        time_steps=200,
    )

    assert result.price > 0


def test_crank_nicolson_call_close_to_black_scholes(
    inputs,
):
    bs_price = european_call(
        inputs
    )

    result = crank_nicolson_price(
        inputs,
        option_type="call",
        space_steps=250,
        time_steps=250,
    )

    assert result.price == pytest.approx(
        bs_price,
        abs=0.05,
    )


def test_crank_nicolson_put_close_to_black_scholes(
    inputs,
):
    bs_price = european_put(
        inputs
    )

    result = crank_nicolson_price(
        inputs,
        option_type="put",
        space_steps=250,
        time_steps=250,
    )

    assert result.price == pytest.approx(
        bs_price,
        abs=0.05,
    )