import pytest

from app.models.black_scholes import (
    OptionInputs,
    european_call,
    european_put,
)

from app.models.binomial import (
    binomial_price,
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


def test_binomial_call_positive(inputs):
    result = binomial_price(
        inputs,
        option_type="call",
        steps=100,
    )

    assert result.price > 0


def test_binomial_put_positive(inputs):
    result = binomial_price(
        inputs,
        option_type="put",
        steps=100,
    )

    assert result.price > 0


def test_binomial_converges_to_black_scholes_call(
    inputs,
):
    bs_price = european_call(inputs)

    tree_price = binomial_price(
        inputs,
        option_type="call",
        steps=1000,
    ).price

    assert tree_price == pytest.approx(
        bs_price,
        abs=0.01,
    )


def test_binomial_converges_to_black_scholes_put(
    inputs,
):
    bs_price = european_put(inputs)

    tree_price = binomial_price(
        inputs,
        option_type="put",
        steps=1000,
    ).price

    assert tree_price == pytest.approx(
        bs_price,
        abs=0.01,
    )


def test_american_put_not_less_than_european_put(
    inputs,
):
    european = binomial_price(
        inputs,
        option_type="put",
        steps=500,
        american=False,
    ).price

    american = binomial_price(
        inputs,
        option_type="put",
        steps=500,
        american=True,
    ).price

    assert american >= european