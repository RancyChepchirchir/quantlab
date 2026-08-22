import pytest

from app.services.volatility_surface import (
    CalibratedQuote,
)

from app.services.volatility_interpolation import (
    interpolate_volatility_surface,
)


def make_quote(
    strike: float,
    maturity: float,
    iv: float,
) -> CalibratedQuote:
    return CalibratedQuote(
        strike=
            strike,

        maturity=
            maturity,

        market_price=
            10.0,

        option_type=
            "call",

        implied_volatility=
            iv,

        american_implied_volatility=
            iv,

        american_iv_difference=
            0.0,

        american_iv_converged=
            True,
    )


def test_surface_grid_shape():
    quotes = [
        make_quote(
            90.0,
            0.5,
            0.25,
        ),
        make_quote(
            100.0,
            0.5,
            0.20,
        ),
        make_quote(
            110.0,
            0.5,
            0.23,
        ),
        make_quote(
            90.0,
            1.0,
            0.24,
        ),
        make_quote(
            100.0,
            1.0,
            0.21,
        ),
        make_quote(
            110.0,
            1.0,
            0.22,
        ),
    ]

    surface = (
        interpolate_volatility_surface(
            quotes,
            strike_points=5,
            maturity_points=4,
        )
    )

    assert len(
        surface.strikes
    ) == 5

    assert len(
        surface.maturities
    ) == 4

    assert len(
        surface.points
    ) == 20


def test_surface_preserves_exact_observation():
    quotes = [
        make_quote(
            90.0,
            0.5,
            0.25,
        ),
        make_quote(
            100.0,
            0.5,
            0.20,
        ),
        make_quote(
            110.0,
            0.5,
            0.23,
        ),
    ]

    surface = (
        interpolate_volatility_surface(
            quotes,
            strike_points=3,
            maturity_points=2,
        )
    )

    matching = [
        point
        for point
        in surface.points
        if (
            point.strike
            == pytest.approx(
                100.0
            )
            and point.maturity
            == pytest.approx(
                0.5
            )
        )
    ]

    assert matching

    assert (
        matching[0]
        .implied_volatility
        == pytest.approx(
            0.20
        )
    )


def test_interpolated_volatility_is_positive():
    quotes = [
        make_quote(
            90.0,
            0.5,
            0.30,
        ),
        make_quote(
            110.0,
            1.0,
            0.20,
        ),
    ]

    surface = (
        interpolate_volatility_surface(
            quotes,
            strike_points=8,
            maturity_points=6,
        )
    )

    for point in (
        surface.points
    ):
        assert (
            point
            .implied_volatility
            > 0
        )


def test_empty_surface_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "At least one "
            "calibrated quote"
        ),
    ):
        interpolate_volatility_surface(
            []
        )