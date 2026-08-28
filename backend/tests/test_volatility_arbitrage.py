import pytest

from app.services.volatility_arbitrage import (
    detect_butterfly_arbitrage,
    detect_calendar_arbitrage,
    diagnose_volatility_arbitrage,
    total_variance,
)


def test_total_variance():
    result = total_variance(
        volatility=0.20,
        maturity=2.0,
    )

    assert result == pytest.approx(
        0.08
    )


def test_total_variance_rejects_negative_volatility():
    with pytest.raises(
        ValueError,
        match="volatility",
    ):
        total_variance(
            volatility=-0.20,
            maturity=1.0,
        )


def test_total_variance_rejects_invalid_maturity():
    with pytest.raises(
        ValueError,
        match="maturity",
    ):
        total_variance(
            volatility=0.20,
            maturity=0.0,
        )


def test_calendar_arbitrage_free_surface():
    strikes = [
        90.0,
        90.0,
        100.0,
        100.0,
        110.0,
        110.0,
    ]

    maturities = [
        0.5,
        1.0,
        0.5,
        1.0,
        0.5,
        1.0,
    ]

    volatilities = [
        0.22,
        0.23,
        0.20,
        0.21,
        0.21,
        0.22,
    ]

    violations = (
        detect_calendar_arbitrage(
            strikes=strikes,
            maturities=maturities,
            volatilities=volatilities,
        )
    )

    assert violations == []


def test_calendar_arbitrage_violation_detected():
    strikes = [
        100.0,
        100.0,
    ]

    maturities = [
        0.5,
        1.0,
    ]

    # Total variance:
    #
    # T=0.5:
    # 0.40^2 * 0.5 = 0.08
    #
    # T=1.0:
    # 0.20^2 * 1.0 = 0.04
    #
    # Later total variance is smaller.
    volatilities = [
        0.40,
        0.20,
    ]

    violations = (
        detect_calendar_arbitrage(
            strikes=strikes,
            maturities=maturities,
            volatilities=volatilities,
        )
    )

    assert len(
        violations
    ) == 1

    violation = (
        violations[0]
    )

    assert (
        violation.strike
        == 100.0
    )

    assert (
        violation.earlier_maturity
        == 0.5
    )

    assert (
        violation.later_maturity
        == 1.0
    )

    assert (
        violation.difference
        < 0.0
    )


def test_calendar_inputs_must_have_equal_lengths():
    with pytest.raises(
        ValueError,
        match="equal lengths",
    ):
        detect_calendar_arbitrage(
            strikes=[
                90.0,
                100.0,
            ],
            maturities=[
                1.0,
            ],
            volatilities=[
                0.20,
                0.20,
            ],
        )


def test_butterfly_arbitrage_free_convex_prices():
    strikes = [
        90.0,
        100.0,
        110.0,
    ]

    maturities = [
        1.0,
        1.0,
        1.0,
    ]

    # Call prices decrease with strike
    # and remain convex:
    #
    # left slope  = (10 - 16) / 10 = -0.6
    # right slope = ( 6 - 10) / 10 = -0.4
    #
    # curvature = -0.4 - (-0.6) = +0.2
    option_prices = [
        16.0,
        10.0,
        6.0,
    ]

    violations = (
        detect_butterfly_arbitrage(
            strikes=strikes,
            maturities=maturities,
            option_prices=option_prices,
        )
    )

    assert violations == []


def test_butterfly_arbitrage_violation_detected():
    strikes = [
        90.0,
        100.0,
        110.0,
    ]

    maturities = [
        1.0,
        1.0,
        1.0,
    ]

    # Deliberately concave option prices:
    #
    # left slope  = (11 - 15) / 10 = -0.4
    # right slope = ( 5 - 11) / 10 = -0.6
    #
    # curvature = -0.6 - (-0.4) = -0.2
    option_prices = [
        15.0,
        11.0,
        5.0,
    ]

    violations = (
        detect_butterfly_arbitrage(
            strikes=strikes,
            maturities=maturities,
            option_prices=option_prices,
        )
    )

    assert len(
        violations
    ) == 1

    violation = (
        violations[0]
    )

    assert (
        violation.maturity
        == 1.0
    )

    assert (
        violation.center_strike
        == 100.0
    )

    assert (
        violation.curvature
        < 0.0
    )


def test_butterfly_handles_uneven_strike_spacing():
    strikes = [
        90.0,
        100.0,
        120.0,
    ]

    maturities = [
        1.0,
        1.0,
        1.0,
    ]

    option_prices = [
        16.0,
        10.0,
        4.0,
    ]

    violations = (
        detect_butterfly_arbitrage(
            strikes=strikes,
            maturities=maturities,
            option_prices=option_prices,
        )
    )

    assert violations == []


def test_butterfly_requires_three_points_per_maturity():
    violations = (
        detect_butterfly_arbitrage(
            strikes=[
                90.0,
                100.0,
            ],
            maturities=[
                1.0,
                1.0,
            ],
            option_prices=[
                15.0,
                10.0,
            ],
        )
    )

    assert violations == []


def test_butterfly_inputs_must_have_equal_lengths():
    with pytest.raises(
        ValueError,
        match="equal lengths",
    ):
        detect_butterfly_arbitrage(
            strikes=[
                90.0,
                100.0,
            ],
            maturities=[
                1.0,
            ],
            option_prices=[
                15.0,
                10.0,
            ],
        )


def test_full_diagnostic_arbitrage_free():
    result = (
        diagnose_volatility_arbitrage(
            strikes=[
                90.0,
                100.0,
                110.0,
                90.0,
                100.0,
                110.0,
            ],

            maturities=[
                0.5,
                0.5,
                0.5,
                1.0,
                1.0,
                1.0,
            ],

            volatilities=[
                0.22,
                0.20,
                0.21,
                0.23,
                0.21,
                0.22,
            ],

            option_prices=[
                14.0,
                8.0,
                4.0,
                16.0,
                10.0,
                6.0,
            ],
        )
    )

    assert (
        result.calendar_arbitrage_free
        is True
    )

    assert (
        result.butterfly_arbitrage_free
        is True
    )

    assert (
        result.arbitrage_free
        is True
    )

    assert (
        result.total_violation_count
        == 0
    )


def test_full_diagnostic_detects_both_violation_types():
    result = (
        diagnose_volatility_arbitrage(
            strikes=[
                90.0,
                100.0,
                110.0,
                90.0,
                100.0,
                110.0,
            ],

            maturities=[
                0.5,
                0.5,
                0.5,
                1.0,
                1.0,
                1.0,
            ],

            # At strike 100:
            #
            # short variance =
            # 0.40² * 0.5 = 0.08
            #
            # long variance =
            # 0.20² * 1.0 = 0.04
            #
            # calendar violation.
            volatilities=[
                0.25,
                0.40,
                0.25,
                0.25,
                0.20,
                0.25,
            ],

            # First maturity is deliberately
            # concave around K=100.
            option_prices=[
                15.0,
                11.0,
                5.0,
                16.0,
                10.0,
                6.0,
            ],
        )
    )

    assert (
        result.calendar_arbitrage_free
        is False
    )

    assert (
        result.butterfly_arbitrage_free
        is False
    )

    assert (
        result.arbitrage_free
        is False
    )

    assert (
        result.calendar_violation_count
        >= 1
    )

    assert (
        result.butterfly_violation_count
        >= 1
    )

    assert (
        result.total_violation_count
        ==
        (
            result.calendar_violation_count
            + result.butterfly_violation_count
        )
    )


def test_diagnostic_without_prices_only_checks_calendar():
    result = (
        diagnose_volatility_arbitrage(
            strikes=[
                100.0,
                100.0,
            ],

            maturities=[
                0.5,
                1.0,
            ],

            volatilities=[
                0.20,
                0.21,
            ],

            option_prices=None,
        )
    )

    assert (
        result.calendar_arbitrage_free
        is True
    )

    assert (
        result.butterfly_arbitrage_free
        is True
    )

    assert (
        result.butterfly_violation_count
        == 0
    )