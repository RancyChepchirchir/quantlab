import pytest

from app.models.black_scholes import (
    OptionInputs,
    european_put,
)

from app.models.binomial import (
    binomial_price,
)

from app.models.american_finite_difference import (
    projected_crank_nicolson_put,
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


def test_american_fd_positive(inputs):
    result = (
        projected_crank_nicolson_put(
            inputs,
            space_steps=150,
            time_steps=150,
        )
    )

    assert result.price > 0


def test_american_put_at_least_european_put(
    inputs,
):
    european = european_put(
        inputs
    )

    american = (
        projected_crank_nicolson_put(
            inputs,
            space_steps=200,
            time_steps=200,
        ).price
    )

    assert american >= european


def test_american_fd_close_to_crr(
    inputs,
):
    fd = (
        projected_crank_nicolson_put(
            inputs,
            space_steps=250,
            time_steps=250,
        ).price
    )

    crr = binomial_price(
        inputs,
        option_type="put",
        steps=2000,
        american=True,
    ).price

    assert fd == pytest.approx(
        crr,
        abs=0.10,
    )