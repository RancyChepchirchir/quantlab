from types import SimpleNamespace

import numpy as np
import pytest

from app.services.ssvi import (
    build_atm_slices,
    build_ssvi_arbitrage_diagnostics,
    build_ssvi_calendar_diagnostics,
    fit_ssvi_surface,
    forward_log_moneyness,
    forward_price,
    ssvi_phi,
    ssvi_total_variance,
)


def make_quote(
    strike: float,
    maturity: float,
    iv: float,
):
    return SimpleNamespace(
        strike=
            strike,

        maturity=
            maturity,

        implied_volatility=
            iv,
    )


def synthetic_quotes():
    quotes = []

    for (
        maturity,
        atm_iv,
    ) in [
        (
            0.5,
            0.20,
        ),
        (
            1.0,
            0.22,
        ),
        (
            2.0,
            0.24,
        ),
    ]:
        for (
            strike,
            adjustment,
        ) in [
            (
                80.0,
                0.05,
            ),
            (
                90.0,
                0.025,
            ),
            (
                100.0,
                0.0,
            ),
            (
                110.0,
                0.015,
            ),
            (
                120.0,
                0.035,
            ),
        ]:
            quotes.append(
                make_quote(
                    strike=
                        strike,

                    maturity=
                        maturity,

                    iv=
                        atm_iv
                        + adjustment,
                )
            )

    return quotes


def test_forward_price():
    result = forward_price(
        spot=
            100.0,

        rate=
            0.05,

        dividend_yield=
            0.02,

        maturity=
            1.0,
    )

    assert result == pytest.approx(
        100.0
        * np.exp(
            0.03
        )
    )


def test_forward_log_moneyness_is_zero_at_forward():
    forward = 105.0

    result = (
        forward_log_moneyness(
            strike=
                forward,

            forward=
                forward,
        )
    )

    assert result == pytest.approx(
        0.0
    )


def test_ssvi_phi_positive():
    theta = np.asarray(
        [
            0.02,
            0.04,
            0.08,
        ]
    )

    phi = ssvi_phi(
        theta=
            theta,

        eta=
            0.5,

        gamma=
            0.5,
    )

    assert np.all(
        phi > 0.0
    )


def test_ssvi_total_variance_positive():
    k = np.linspace(
        -0.3,
        0.3,
        21,
    )

    theta = np.full_like(
        k,
        0.04,
    )

    variance = (
        ssvi_total_variance(
            log_moneyness=
                k,

            theta=
                theta,

            eta=
                0.5,

            rho=
                -0.30,

            gamma=
                0.5,
        )
    )

    assert np.all(
        variance > 0.0
    )


def test_ssvi_atm_returns_theta():
    theta_value = 0.04

    result = (
        ssvi_total_variance(
            log_moneyness=
                np.asarray(
                    [
                        0.0
                    ]
                ),

            theta=
                np.asarray(
                    [
                        theta_value
                    ]
                ),

            eta=
                0.5,

            rho=
                -0.30,

            gamma=
                0.5,
        )
    )

    assert result[0] == pytest.approx(
        theta_value
    )


def test_build_atm_slices():
    slices = build_atm_slices(
        quotes=
            synthetic_quotes(),

        spot=
            100.0,

        rate=
            0.0,

        dividend_yield=
            0.0,

        minimum_strikes=
            3,
    )

    assert len(
        slices
    ) == 3

    assert [
        item.maturity
        for item
        in slices
    ] == [
        0.5,
        1.0,
        2.0,
    ]

    for item in slices:
        assert item.theta > 0.0
        assert item.forward > 0.0


def test_arbitrage_diagnostic_structure():
    slices = build_atm_slices(
        quotes=
            synthetic_quotes(),

        spot=
            100.0,

        rate=
            0.0,

        dividend_yield=
            0.0,
    )

    diagnostics = (
        build_ssvi_arbitrage_diagnostics(
            slices=
                slices,

            eta=
                0.5,

            rho=
                -0.25,

            gamma=
                0.5,
        )
    )

    assert len(
        diagnostics
    ) == 3

    for item in diagnostics:
        assert item.theta > 0.0
        assert item.phi > 0.0

        assert (
            item
            .first_butterfly_bound
            >= 0.0
        )

        assert (
            item
            .second_butterfly_bound
            >= 0.0
        )


def test_calendar_diagnostics():
    slices = build_atm_slices(
        quotes=
            synthetic_quotes(),

        spot=
            100.0,

        rate=
            0.0,

        dividend_yield=
            0.0,
    )

    diagnostics = (
        build_ssvi_calendar_diagnostics(
            slices=
                slices,

            eta=
                0.5,

            rho=
                -0.25,

            gamma=
                0.5,

            grid_points=
                51,
        )
    )

    assert len(
        diagnostics
    ) == 2

    for item in diagnostics:
        assert (
            item
            .comparison_point_count
            == 51
        )


def test_fit_ssvi_surface():
    result = fit_ssvi_surface(
        quotes=
            synthetic_quotes(),

        spot=
            100.0,

        rate=
            0.0,

        dividend_yield=
            0.0,

        grid_points_per_maturity=
            31,

        calendar_grid_points=
            51,
    )

    assert (
        result
        .parameters
        .maturity_count
        == 3
    )

    assert (
        result
        .parameters
        .observation_count
        == 15
    )

    assert (
        result.parameters.eta
        > 0.0
    )

    assert (
        -1.0
        < result.parameters.rho
        < 1.0
    )

    assert (
        0.0
        < result.parameters.gamma
        < 1.0
    )

    assert (
        result.parameters.rmse
        >= 0.0
    )

    assert len(
        result.atm_slices
    ) == 3

    assert len(
        result.points
    ) == (
        3
        * 31
    )

    assert len(
        result
        .calendar_diagnostics
    ) == 2

    assert len(
        result
        .arbitrage_diagnostics
    ) == 3


def test_ssvi_requires_two_maturities():
    quotes = [
        make_quote(
            90.0,
            1.0,
            0.22,
        ),

        make_quote(
            100.0,
            1.0,
            0.20,
        ),

        make_quote(
            110.0,
            1.0,
            0.21,
        ),
    ]

    with pytest.raises(
        ValueError,
        match=(
            "at least two maturities"
        ),
    ):
        fit_ssvi_surface(
            quotes=
                quotes,

            spot=
                100.0,

            rate=
                0.0,

            dividend_yield=
                0.0,
        )


def test_invalid_ssvi_parameters_rejected():
    with pytest.raises(
        ValueError,
        match="rho",
    ):
        ssvi_total_variance(
            log_moneyness=
                np.asarray(
                    [
                        0.0
                    ]
                ),

            theta=
                np.asarray(
                    [
                        0.04
                    ]
                ),

            eta=
                0.5,

            rho=
                1.0,

            gamma=
                0.5,
        )

    with pytest.raises(
        ValueError,
        match="gamma",
    ):
        ssvi_phi(
            theta=
                np.asarray(
                    [
                        0.04
                    ]
                ),

            eta=
                0.5,

            gamma=
                1.2,
        )