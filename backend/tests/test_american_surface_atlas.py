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
    )

    assert len(
        atlas.spot_grid
    ) == 41

    assert len(
        atlas.time_grid
    ) == 31

    price = np.asarray(
        atlas.price_surface
    )

    payoff = np.asarray(
        atlas.payoff_surface
    )

    gap = np.asarray(
        atlas.exercise_gap_surface
    )

    assert price.shape == (
        31,
        41,
    )

    assert payoff.shape == (
        31,
        41,
    )

    assert gap.shape == (
        31,
        41,
    )


def test_american_surface_dominates_payoff():
    atlas = build_american_surface_atlas(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        space_steps=40,
        time_steps=30,
    )

    gap = np.asarray(
        atlas.exercise_gap_surface
    )

    assert np.min(gap) >= -1e-8


def test_terminal_surface_equals_payoff():
    atlas = build_american_surface_atlas(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        space_steps=40,
        time_steps=30,
    )

    price = np.asarray(
        atlas.price_surface
    )

    payoff = np.asarray(
        atlas.payoff_surface
    )

    assert np.allclose(
        price[-1],
        payoff[-1],
    )