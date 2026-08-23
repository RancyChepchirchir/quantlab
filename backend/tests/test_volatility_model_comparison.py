from types import (
    SimpleNamespace,
)

import pytest

from app.services.svi import (
    fit_svi_surface,
)

from app.services.ssvi import (
    fit_ssvi_surface,
)

from app.services.volatility_model_comparison import (
    compare_svi_and_ssvi,
)


def make_quote(
    strike: float,
    maturity: float,
    iv: float,
):
    return SimpleNamespace(
        strike=strike,
        maturity=maturity,
        implied_volatility=iv,
    )


def synthetic_quotes():
    quotes = []

    for (
        maturity,
        base_iv,
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
                0.050,
            ),
            (
                90.0,
                0.025,
            ),
            (
                100.0,
                0.000,
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
                    strike=strike,
                    maturity=maturity,
                    iv=(
                        base_iv
                        + adjustment
                    ),
                )
            )

    return quotes


def fitted_models():
    quotes = (
        synthetic_quotes()
    )

    svi = fit_svi_surface(
        quotes=quotes,
        spot=100.0,
        minimum_strikes=3,
        grid_points=51,
        calendar_grid_points=101,
    )

    ssvi = fit_ssvi_surface(
        quotes=quotes,
        spot=100.0,
        rate=0.0,
        dividend_yield=0.0,
        minimum_strikes=3,
        grid_points_per_maturity=51,
        calendar_grid_points=101,
    )

    return (
        quotes,
        svi,
        ssvi,
    )


def test_comparison_returns_global_metrics():
    (
        quotes,
        svi,
        ssvi,
    ) = fitted_models()

    result = (
        compare_svi_and_ssvi(
            quotes=quotes,
            svi_surface=svi,
            ssvi_surface=ssvi,
        )
    )

    assert (
        result.svi.rmse
        >= 0.0
    )

    assert (
        result.ssvi.rmse
        >= 0.0
    )

    assert (
        result.svi.mae
        >= 0.0
    )

    assert (
        result.ssvi.mae
        >= 0.0
    )

    assert (
        result
        .svi
        .max_absolute_error
        >= 0.0
    )

    assert (
        result
        .ssvi
        .max_absolute_error
        >= 0.0
    )


def test_comparison_uses_same_observations():
    (
        quotes,
        svi,
        ssvi,
    ) = fitted_models()

    result = (
        compare_svi_and_ssvi(
            quotes=quotes,
            svi_surface=svi,
            ssvi_surface=ssvi,
        )
    )

    assert (
        result
        .svi
        .observation_count
        ==
        result
        .ssvi
        .observation_count
    )

    assert (
        result
        .svi
        .observation_count
        == 15
    )


def test_comparison_has_all_maturities():
    (
        quotes,
        svi,
        ssvi,
    ) = fitted_models()

    result = (
        compare_svi_and_ssvi(
            quotes=quotes,
            svi_surface=svi,
            ssvi_surface=ssvi,
        )
    )

    assert (
        len(
            result
            .maturity_comparisons
        )
        == 3
    )

    maturities = [
        item.maturity
        for item
        in result
        .maturity_comparisons
    ]

    assert maturities == [
        0.5,
        1.0,
        2.0,
    ]


def test_each_maturity_uses_same_sample():
    (
        quotes,
        svi,
        ssvi,
    ) = fitted_models()

    result = (
        compare_svi_and_ssvi(
            quotes=quotes,
            svi_surface=svi,
            ssvi_surface=ssvi,
        )
    )

    for item in (
        result
        .maturity_comparisons
    ):
        assert (
            item
            .svi
            .observation_count
            ==
            item
            .ssvi
            .observation_count
        )

        assert (
            item
            .observation_count
            ==
            item
            .svi
            .observation_count
        )


def test_model_labels_are_valid():
    (
        quotes,
        svi,
        ssvi,
    ) = fitted_models()

    result = (
        compare_svi_and_ssvi(
            quotes=quotes,
            svi_surface=svi,
            ssvi_surface=ssvi,
        )
    )

    valid = {
        "svi",
        "ssvi",
        "tie",
    }

    assert (
        result
        .better_rmse_model
        in valid
    )

    assert (
        result
        .better_mae_model
        in valid
    )

    for item in (
        result
        .maturity_comparisons
    ):
        assert (
            item
            .better_rmse_model
            in valid
        )

        assert (
            item
            .better_mae_model
            in valid
        )


def test_duplicate_call_put_quotes_are_collapsed():
    quotes = (
        synthetic_quotes()
    )

    duplicate = (
        make_quote(
            strike=100.0,
            maturity=1.0,
            iv=0.22,
        )
    )

    quotes.append(
        duplicate
    )

    svi = fit_svi_surface(
        quotes=quotes,
        spot=100.0,
        minimum_strikes=3,
        grid_points=51,
        calendar_grid_points=101,
    )

    ssvi = fit_ssvi_surface(
        quotes=quotes,
        spot=100.0,
        rate=0.0,
        dividend_yield=0.0,
        minimum_strikes=3,
        grid_points_per_maturity=51,
        calendar_grid_points=101,
    )

    result = (
        compare_svi_and_ssvi(
            quotes=quotes,
            svi_surface=svi,
            ssvi_surface=ssvi,
        )
    )

    # Still 5 unique strikes
    # × 3 maturities.
    assert (
        result
        .svi
        .observation_count
        == 15
    )


def test_comparison_requires_common_observations():
    with pytest.raises(
        ValueError
    ):
        compare_svi_and_ssvi(
            quotes=[],
            svi_surface=SimpleNamespace(
                smiles=[]
            ),
            ssvi_surface=SimpleNamespace(
                parameters=SimpleNamespace(
                    eta=1.0,
                    rho=-0.2,
                    gamma=0.5,
                ),
                atm_slices=[],
            ),
        )