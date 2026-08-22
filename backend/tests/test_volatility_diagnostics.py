import pytest

from app.models.black_scholes import (
    OptionInputs,
    european_call,
    european_put,
)

from app.services.volatility_surface import (
    OptionQuote,
    calibrate_option_chain,
)

from app.services.volatility_diagnostics import (
    calculate_volatility_diagnostics,
)


def build_calibrated_quotes():
    spot = 100.0
    rate = 0.05
    dividend_yield = 0.0
    volatility = 0.20

    quotes = []

    for maturity in [
        0.5,
        1.0,
    ]:
        for strike in [
            90.0,
            100.0,
            110.0,
        ]:
            inputs = OptionInputs(
                spot=spot,
                strike=strike,
                rate=rate,
                volatility=
                    volatility,
                maturity=
                    maturity,
                dividend_yield=
                    dividend_yield,
            )

            call_price = (
                european_call(
                    inputs
                )
            )

            put_price = (
                european_put(
                    inputs
                )
            )

            quotes.append(
                OptionQuote(
                    strike=
                        strike,

                    maturity=
                        maturity,

                    market_price=
                        call_price,

                    option_type=
                        "call",
                )
            )

            quotes.append(
                OptionQuote(
                    strike=
                        strike,

                    maturity=
                        maturity,

                    market_price=
                        put_price,

                    option_type=
                        "put",
                )
            )

    result = calibrate_option_chain(
        spot=spot,
        rate=rate,
        dividend_yield=
            dividend_yield,
        quotes=quotes,
    )

    return (
        spot,
        rate,
        dividend_yield,
        result.calibrated,
    )


def test_moneyness_diagnostics():
    (
        spot,
        rate,
        dividend_yield,
        quotes,
    ) = (
        build_calibrated_quotes()
    )

    diagnostics = (
        calculate_volatility_diagnostics(
            quotes=
                quotes,

            spot=
                spot,

            rate=
                rate,

            dividend_yield=
                dividend_yield,
        )
    )

    assert len(
        diagnostics.moneyness
    ) == len(
        quotes
    )

    atm_points = [
        item
        for item
        in diagnostics.moneyness
        if item.strike
        == 100.0
    ]

    assert atm_points

    for item in atm_points:
        assert (
            item.moneyness
            == pytest.approx(
                1.0
            )
        )

        assert (
            item.log_moneyness
            == pytest.approx(
                0.0
            )
        )


def test_constant_volatility_has_near_zero_skew():
    (
        spot,
        rate,
        dividend_yield,
        quotes,
    ) = (
        build_calibrated_quotes()
    )

    diagnostics = (
        calculate_volatility_diagnostics(
            quotes=
                quotes,

            spot=
                spot,

            rate=
                rate,

            dividend_yield=
                dividend_yield,
        )
    )

    assert len(
        diagnostics.skew
    ) == 2

    for item in (
        diagnostics.skew
    ):
        assert (
            item.skew_slope
            is not None
        )

        assert abs(
            item.skew_slope
        ) < 1e-5


def test_atm_term_structure():
    (
        spot,
        rate,
        dividend_yield,
        quotes,
    ) = (
        build_calibrated_quotes()
    )

    diagnostics = (
        calculate_volatility_diagnostics(
            quotes=
                quotes,

            spot=
                spot,

            rate=
                rate,

            dividend_yield=
                dividend_yield,
        )
    )

    assert len(
        diagnostics
        .atm_term_structure
    ) == 2

    for item in (
        diagnostics
        .atm_term_structure
    ):
        assert (
            item.atm_strike
            == 100.0
        )

        assert (
            item
            .atm_implied_volatility
            == pytest.approx(
                0.20,
                abs=1e-6,
            )
        )


def test_black_scholes_prices_satisfy_put_call_parity():
    (
        spot,
        rate,
        dividend_yield,
        quotes,
    ) = (
        build_calibrated_quotes()
    )

    diagnostics = (
        calculate_volatility_diagnostics(
            quotes=
                quotes,

            spot=
                spot,

            rate=
                rate,

            dividend_yield=
                dividend_yield,
        )
    )

    assert len(
        diagnostics
        .put_call_parity
    ) == 6

    assert (
        diagnostics
        .mean_absolute_parity_error
        is not None
    )

    assert (
        diagnostics
        .max_absolute_parity_error
        is not None
    )

    assert (
        diagnostics
        .mean_absolute_parity_error
        < 1e-8
    )

    assert (
        diagnostics
        .max_absolute_parity_error
        < 1e-8
    )