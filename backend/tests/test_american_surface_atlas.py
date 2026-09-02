import numpy as np

from app.services.american_surface_atlas import (
    build_american_surface_atlas,
)


def test_american_surface_atlas_shapes():
    atlas = build_american_surface_atlas(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
        space_steps=40,
        time_steps=30,
        crr_surface_points=31,
    )

    spot_grid = np.asarray(
        atlas.spot_grid
    )

    tau_grid = np.asarray(
        atlas.time_to_maturity_grid
    )

    cn = np.asarray(
        atlas.cn_surface
    )

    crr = np.asarray(
        atlas.crr_surface
    )

    payoff = np.asarray(
        atlas.payoff_surface
    )

    exercise_gap = np.asarray(
        atlas.exercise_gap_surface
    )

    crr_signed = np.asarray(
        atlas.crr_signed_error_surface
    )

    crr_absolute = np.asarray(
        atlas.crr_absolute_error_surface
    )

    assert spot_grid.shape == (31,)
    assert tau_grid.shape == (31,)

    expected_shape = (
        tau_grid.size,
        spot_grid.size,
    )

    assert cn.shape == expected_shape
    assert crr.shape == expected_shape
    assert payoff.shape == expected_shape
    assert exercise_gap.shape == expected_shape
    assert crr_signed.shape == expected_shape
    assert crr_absolute.shape == expected_shape

    assert np.isclose(
        tau_grid[0],
        0.0,
    )

    assert np.isclose(
        tau_grid[-1],
        1.0,
    )

    assert np.all(
        np.diff(spot_grid) > 0.0
    )

    assert np.all(
        np.diff(tau_grid) > 0.0
    )


def test_american_surface_dominates_payoff():
    atlas = build_american_surface_atlas(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
        space_steps=40,
        time_steps=30,
        crr_surface_points=31,
    )

    cn = np.asarray(
        atlas.cn_surface
    )

    payoff = np.asarray(
        atlas.payoff_surface
    )

    exercise_gap = np.asarray(
        atlas.exercise_gap_surface
    )

    # Projected Crank-Nicolson enforces the
    # American obstacle:
    #
    # V(S, tau) >= Phi(S)
    assert np.all(
        cn >= payoff - 1e-10
    )

    # The stored exercise/continuation gap
    # must be exactly V_CN - payoff.
    np.testing.assert_allclose(
        exercise_gap,
        cn - payoff,
        atol=1e-10,
        rtol=1e-10,
    )

    assert np.min(
        exercise_gap
    ) >= -1e-10


def test_terminal_surface_equals_payoff():
    atlas = build_american_surface_atlas(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
        space_steps=40,
        time_steps=30,
        crr_surface_points=31,
    )

    spot_grid = np.asarray(
        atlas.spot_grid
    )

    tau_grid = np.asarray(
        atlas.time_to_maturity_grid
    )

    cn = np.asarray(
        atlas.cn_surface
    )

    crr = np.asarray(
        atlas.crr_surface
    )

    payoff_surface = np.asarray(
        atlas.payoff_surface
    )

    payoff = np.maximum(
        100.0 - spot_grid,
        0.0,
    )

    # Atlas uses time-to-maturity:
    #
    # tau = T - t
    #
    # Therefore tau = 0 is expiry.
    assert np.isclose(
        tau_grid[0],
        0.0,
    )

    np.testing.assert_allclose(
        payoff_surface[0],
        payoff,
        atol=1e-10,
        rtol=1e-10,
    )

    np.testing.assert_allclose(
        cn[0],
        payoff,
        atol=1e-10,
        rtol=1e-10,
    )

    np.testing.assert_allclose(
        crr[0],
        payoff,
        atol=1e-10,
        rtol=1e-10,
    )