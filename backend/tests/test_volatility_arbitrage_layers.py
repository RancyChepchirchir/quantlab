from types import SimpleNamespace

from app.services.svi import (
    fit_svi_surface,
)

from app.services.ssvi import (
    fit_ssvi_surface,
)

from app.services.volatility_arbitrage_layers import (
    compare_arbitrage_layers,
)


def make_quote(
    strike: float,
    maturity: float,
    iv: float,
    market_price: float,
    option_type="call",
):
    return SimpleNamespace(
        strike=
            strike,

        maturity=
            maturity,

        implied_volatility=
            iv,

        market_price=
            market_price,

        option_type=option_type,
    )


def synthetic_quotes():
    quotes = []

    for (
        maturity,
        base_iv,
        prices,
    ) in [
        (
            0.5,
            0.20,
            [
                21.0,
                12.0,
                6.0,
                2.5,
                0.9,
            ],
        ),
        (
            1.0,
            0.22,
            [
                23.0,
                14.0,
                9.0,
                5.0,
                2.5,
            ],
        ),
        (
            2.0,
            0.24,
            [
                27.0,
                19.0,
                13.5,
                9.0,
                5.8,
            ],
        ),
    ]:

        for (
            index,
            strike,
        ) in enumerate(
            [
                80.0,
                90.0,
                100.0,
                110.0,
                120.0,
            ]
        ):

            adjustment = (
                abs(
                    strike
                    - 100.0
                )
                / 1000.0
            )

            quotes.append(
                make_quote(
                    strike=
                        strike,

                    maturity=
                        maturity,

                    iv=
                        base_iv
                        + adjustment,

                    market_price=
                        prices[
                            index
                        ],
                )
            )

    return quotes


def test_three_layer_arbitrage_comparison():

    quotes = (
        synthetic_quotes()
    )

    svi = (
        fit_svi_surface(
            quotes=
                quotes,

            spot=
                100.0,

            minimum_strikes=
                3,

            grid_points=
                31,

            calendar_grid_points=
                51,
        )
    )

    ssvi = (
        fit_ssvi_surface(
            quotes=
                quotes,

            spot=
                100.0,

            rate=
                0.0,

            dividend_yield=
                0.0,

            minimum_strikes=
                3,

            grid_points_per_maturity=
                31,

            calendar_grid_points=
                51,
        )
    )

    result = (
        compare_arbitrage_layers(
            quotes=
                quotes,

            svi_surface=
                svi,

            ssvi_surface=
                ssvi,

            spot=
                100.0,

            rate=
                0.0,

            dividend_yield=
                0.0,
        )
    )

    assert (
        result.market.name
        == "market"
    )

    assert (
        result.svi.name
        == "svi"
    )

    assert (
        result.ssvi.name
        == "ssvi"
    )

    for layer in [
        result.market,
        result.svi,
        result.ssvi,
    ]:

        diagnostics = (
            layer.diagnostics
        )

        assert isinstance(
            diagnostics
            .calendar_arbitrage_free,
            bool,
        )

        assert isinstance(
            diagnostics
            .butterfly_arbitrage_free,
            bool,
        )

        assert isinstance(
            diagnostics
            .arbitrage_free,
            bool,
        )

        assert (
            diagnostics
            .calendar_violation_count
            >= 0
        )

        assert (
            diagnostics
            .butterfly_violation_count
            >= 0
        )

        assert (
            diagnostics
            .total_violation_count
            ==
            (
                diagnostics
                .calendar_violation_count

                + diagnostics
                .butterfly_violation_count
            )
        )


def test_market_layer_preserves_violation_signal():

    quotes = (
        synthetic_quotes()
    )

    # Force a clearly concave market slice
    # at T=0.5 around K=100.
    quotes[0] = make_quote(
        strike=80.0,
        maturity=0.5,
        iv=0.24,
        market_price=20.0,
    )

    quotes[1] = make_quote(
        strike=90.0,
        maturity=0.5,
        iv=0.22,
        market_price=15.0,
    )

    quotes[2] = make_quote(
        strike=100.0,
        maturity=0.5,
        iv=0.20,
        market_price=11.0,
    )

    quotes[3] = make_quote(
        strike=110.0,
        maturity=0.5,
        iv=0.21,
        market_price=5.0,
    )

    quotes[4] = make_quote(
        strike=120.0,
        maturity=0.5,
        iv=0.22,
        market_price=2.0,
    )

    svi = (
        fit_svi_surface(
            quotes=
                quotes,

            spot=
                100.0,

            minimum_strikes=
                3,

            grid_points=
                31,

            calendar_grid_points=
                51,
        )
    )

    ssvi = (
        fit_ssvi_surface(
            quotes=
                quotes,

            spot=
                100.0,

            rate=
                0.0,

            dividend_yield=
                0.0,

            minimum_strikes=
                3,

            grid_points_per_maturity=
                31,

            calendar_grid_points=
                51,
        )
    )

    result = (
        compare_arbitrage_layers(
            quotes=
                quotes,

            svi_surface=
                svi,

            ssvi_surface=
                ssvi,

            spot=
                100.0,

            rate=
                0.0,

            dividend_yield=
                0.0,
        )
    )

    assert (
        result
        .market
        .diagnostics
        .butterfly_violation_count
        >= 1
    )