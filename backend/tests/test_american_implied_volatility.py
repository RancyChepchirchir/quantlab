import pytest

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.binomial import (
    binomial_price,
)

from app.models.american_implied_volatility import (
    american_implied_volatility,
)


def test_recovers_american_put_volatility():
    true_volatility = 0.25

    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=
            true_volatility,
        maturity=1.0,
        dividend_yield=0.0,
    )

    market_price = (
        binomial_price(
            inputs,
            option_type="put",
            steps=500,
            american=True,
        )
        .price
    )

    result = (
        american_implied_volatility(
            inputs,
            market_price=
                market_price,
            option_type="put",
            steps=500,
        )
    )

    assert result.converged

    assert (
        result.implied_volatility
        == pytest.approx(
            true_volatility,
            abs=1e-4,
        )
    )

    assert (
        result.absolute_pricing_error
        < 1e-5
    )


def test_recovers_american_call_volatility():
    true_volatility = 0.30

    inputs = OptionInputs(
        spot=100.0,
        strike=105.0,
        rate=0.03,
        volatility=
            true_volatility,
        maturity=0.75,
        dividend_yield=0.02,
    )

    market_price = (
        binomial_price(
            inputs,
            option_type="call",
            steps=500,
            american=True,
        )
        .price
    )

    result = (
        american_implied_volatility(
            inputs,
            market_price=
                market_price,
            option_type="call",
            steps=500,
        )
    )

    assert result.converged

    assert (
        result.implied_volatility
        == pytest.approx(
            true_volatility,
            abs=1e-4,
        )
    )


def test_american_put_iv_for_itm_contract():
    true_volatility = 0.20

    inputs = OptionInputs(
        spot=90.0,
        strike=100.0,
        rate=0.05,
        volatility=
            true_volatility,
        maturity=0.5,
        dividend_yield=0.0,
    )

    market_price = (
        binomial_price(
            inputs,
            option_type="put",
            steps=500,
            american=True,
        )
        .price
    )

    result = (
        american_implied_volatility(
            inputs,
            market_price=
                market_price,
            option_type="put",
            steps=500,
        )
    )

    assert result.converged

    assert (
        result.implied_volatility
        == pytest.approx(
            true_volatility,
            abs=1e-4,
        )
    )


def test_invalid_market_price_rejected():
    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    with pytest.raises(
        ValueError,
        match=(
            "market_price "
            "must be positive"
        ),
    ):
        american_implied_volatility(
            inputs,
            market_price=0.0,
            option_type="put",
        )


def test_invalid_option_type_rejected():
    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    with pytest.raises(
        ValueError,
        match="option_type",
    ):
        american_implied_volatility(
            inputs,
            market_price=10.0,
            option_type="banana",
        )


def test_unattainable_market_price_rejected():
    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    with pytest.raises(
        ValueError,
        match=(
            "above the American "
            "model price"
        ),
    ):
        american_implied_volatility(
            inputs,
            market_price=1000.0,
            option_type="put",
            steps=250,
        )