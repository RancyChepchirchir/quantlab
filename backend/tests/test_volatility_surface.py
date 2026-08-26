import pytest

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.services.volatility_surface import (
    OptionQuote,
    calibrate_option_chain,
)

from fastapi.testclient import (
    TestClient,
)

from app.main import app


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

    result = calibrate_option_chain(
        spot=spot,
        rate=rate,
        dividend_yield=dividend_yield,
        quotes=quotes,
    )

    assert result.input_count == 5
    assert result.calibrated_count == 5
    assert result.rejected_count == 0

    assert result.success_rate == pytest.approx(
        1.0
    )

    assert len(
        result.calibrated
    ) == 5

    assert len(
        result.rejected
    ) == 0

    for quote in result.calibrated:
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

    price = european_call(
        inputs
    )

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

    assert result.input_count == 1
    assert result.calibrated_count == 1
    assert result.rejected_count == 0

    assert len(
        result.calibrated
    ) == 1

    quote = result.calibrated[0]

    assert quote.strike == 100.0
    assert quote.maturity == 0.5
    assert quote.market_price == price
    assert quote.option_type == "call"

    assert (
        quote.implied_volatility
        == pytest.approx(
            0.20,
            abs=1e-6,
        )
    )


def test_bad_quote_does_not_break_chain():
    valid_inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    valid_price = european_call(
        valid_inputs
    )

    quotes = [
        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=valid_price,
            option_type="call",
        ),

        OptionQuote(
            strike=200.0,
            maturity=1.0,
            market_price=999.0,
            option_type="call",
        ),
    ]

    result = calibrate_option_chain(
        spot=100.0,
        rate=0.05,
        dividend_yield=0.0,
        quotes=quotes,
    )

    assert result.input_count == 2
    assert result.calibrated_count == 1
    assert result.rejected_count == 1

    assert result.success_rate == pytest.approx(
        0.5
    )

    assert len(
        result.calibrated
    ) == 1

    assert len(
        result.rejected
    ) == 1

    calibrated_quote = (
        result.calibrated[0]
    )

    assert (
        calibrated_quote.strike
        == 100.0
    )

    assert (
        calibrated_quote
        .implied_volatility
        == pytest.approx(
            0.20,
            abs=1e-6,
        )
    )

    rejected_quote = (
        result.rejected[0]
    )

    assert (
        rejected_quote.strike
        == 200.0
    )

    assert (
        rejected_quote.market_price
        == 999.0
    )

    assert (
        rejected_quote.option_type
        == "call"
    )

    assert (
        rejected_quote.reason
    )


def test_invalid_strike_is_rejected():
    valid_inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    valid_price = european_call(
        valid_inputs
    )

    quotes = [
        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=valid_price,
            option_type="call",
        ),

        OptionQuote(
            strike=-10.0,
            maturity=1.0,
            market_price=5.0,
            option_type="call",
        ),
    ]

    result = calibrate_option_chain(
        spot=100.0,
        rate=0.05,
        dividend_yield=0.0,
        quotes=quotes,
    )

    assert result.input_count == 2
    assert result.calibrated_count == 1
    assert result.rejected_count == 1

    assert (
        result.rejected[0].reason
        == "strike must be positive"
    )


def test_invalid_maturity_is_rejected():
    valid_inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    valid_price = european_call(
        valid_inputs
    )

    quotes = [
        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=valid_price,
            option_type="call",
        ),

        OptionQuote(
            strike=100.0,
            maturity=0.0,
            market_price=5.0,
            option_type="call",
        ),
    ]

    result = calibrate_option_chain(
        spot=100.0,
        rate=0.05,
        dividend_yield=0.0,
        quotes=quotes,
    )

    assert result.calibrated_count == 1
    assert result.rejected_count == 1

    assert (
        result.rejected[0].reason
        == "maturity must be positive"
    )


def test_invalid_market_price_is_rejected():
    valid_inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    valid_price = european_call(
        valid_inputs
    )

    quotes = [
        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=valid_price,
            option_type="call",
        ),

        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=0.0,
            option_type="call",
        ),
    ]

    result = calibrate_option_chain(
        spot=100.0,
        rate=0.05,
        dividend_yield=0.0,
        quotes=quotes,
    )

    assert result.calibrated_count == 1
    assert result.rejected_count == 1

    assert (
        result.rejected[0].reason
        == "market price must be positive"
    )


def test_invalid_option_type_is_rejected():
    valid_inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    valid_price = european_call(
        valid_inputs
    )

    quotes = [
        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=valid_price,
            option_type="call",
        ),

        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=5.0,
            option_type="banana",
        ),
    ]

    result = calibrate_option_chain(
        spot=100.0,
        rate=0.05,
        dividend_yield=0.0,
        quotes=quotes,
    )

    assert result.calibrated_count == 1
    assert result.rejected_count == 1

    assert (
        result.rejected[0].reason
        == "unsupported option type"
    )


def test_all_bad_quotes_raise_error():
    quotes = [
        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=999.0,
            option_type="call",
        ),

        OptionQuote(
            strike=100.0,
            maturity=1.0,
            market_price=-5.0,
            option_type="call",
        ),
    ]

    with pytest.raises(
        ValueError,
        match=(
            "No option quotes could "
            "be successfully calibrated."
        ),
    ):
        calibrate_option_chain(
            spot=100.0,
            rate=0.05,
            dividend_yield=0.0,
            quotes=quotes,
        )


def test_empty_chain_returns_empty_result():
    result = calibrate_option_chain(
        spot=100.0,
        rate=0.05,
        dividend_yield=0.0,
        quotes=[],
    )

    assert result.input_count == 0
    assert result.calibrated_count == 0
    assert result.rejected_count == 0

    assert result.success_rate == 0.0

    assert result.calibrated == []
    assert result.rejected == []

def test_american_iv_is_reported():
    inputs = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.25,
        maturity=1.0,
        dividend_yield=0.0,
    )

    from app.models.binomial import (
        binomial_price,
    )

    market_price = (
        binomial_price(
            inputs,
            option_type="put",
            steps=300,
            american=True,
        )
        .price
    )

    result = calibrate_option_chain(
        spot=100.0,
        rate=0.05,
        dividend_yield=0.0,
        quotes=[
            OptionQuote(
                strike=100.0,
                maturity=1.0,
                market_price=
                    market_price,
                option_type="put",
            )
        ],
        american_steps=300,
    )

    assert result.calibrated_count == 1

    quote = (
        result.calibrated[0]
    )

    assert (
        quote
        .american_implied_volatility
        is not None
    )

    assert (
        quote
        .american_implied_volatility
        == pytest.approx(
            0.25,
            abs=1e-4,
        )
    )

    assert (
        quote
        .american_iv_converged
        is True
    )