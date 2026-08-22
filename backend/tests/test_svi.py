import numpy as np
import pytest

from app.services.svi import (
    SVIParameters,
    SVIFittedPoint,
    SVIArbitrageDiagnostic,
    SVISmileResult,
    build_calendar_diagnostics,
    fit_svi_smile,
    fit_svi_surface,
    svi_total_variance,
    svi_total_variance_from_parameters,
)

from app.services.volatility_surface import (
    CalibratedQuote,
)


def make_quote(
    strike: float,
    maturity: float,
    iv: float,
    option_type: str = "call",
) -> CalibratedQuote:

    return CalibratedQuote(
        strike=
            strike,

        maturity=
            maturity,

        market_price=
            10.0,

        option_type=
            option_type,

        implied_volatility=
            iv,

        american_implied_volatility=
            iv,

        american_iv_difference=
            0.0,

        american_iv_converged=
            True,
    )


def make_synthetic_smile(
    maturity: float,
    a: float,
    b: float = 0.10,
    rho: float = -0.20,
    m: float = 0.0,
    sigma: float = 0.20,
) -> SVISmileResult:

    parameters = (
        SVIParameters(
            maturity=
                maturity,

            a=
                a,

            b=
                b,

            rho=
                rho,

            m=
                m,

            sigma=
                sigma,

            rmse=
                0.0,

            observation_count=
                5,
        )
    )

    log_grid = np.linspace(
        -0.20,
        0.20,
        21,
    )

    total_variance = (
        svi_total_variance_from_parameters(
            log_grid,
            parameters,
        )
    )

    points = []

    for (
        k,
        variance,
    ) in zip(
        log_grid,
        total_variance,
    ):
        fitted_iv = float(
            np.sqrt(
                max(
                    float(
                        variance
                    ),
                    1e-12,
                )
                / maturity
            )
        )

        points.append(
            SVIFittedPoint(
                strike=
                    float(
                        100.0
                        * np.exp(
                            k
                        )
                    ),

                maturity=
                    maturity,

                log_moneyness=
                    float(
                        k
                    ),

                observed_iv=
                    None,

                fitted_iv=
                    fitted_iv,

                total_variance=
                    float(
                        variance
                    ),
            )
        )

    minimum_variance = float(
        np.min(
            total_variance
        )
    )

    arbitrage = (
        SVIArbitrageDiagnostic(
            maturity=
                maturity,

            minimum_total_variance=
                minimum_variance,

            negative_variance_detected=
                False,

            invalid_parameter_region=
                False,

            butterfly_warning=
                False,
        )
    )

    return SVISmileResult(
        parameters=
            parameters,

        points=
            points,

        arbitrage=
            arbitrage,
    )


def test_svi_total_variance_is_positive():
    k = np.array(
        [
            -0.2,
            -0.1,
            0.0,
            0.1,
            0.2,
        ]
    )

    variance = (
        svi_total_variance(
            log_moneyness=
                k,

            a=
                0.02,

            b=
                0.10,

            rho=
                -0.30,

            m=
                0.0,

            sigma=
                0.20,
        )
    )

    assert np.all(
        variance > 0
    )


def test_svi_parameter_wrapper_matches_direct_evaluation():
    parameters = (
        SVIParameters(
            maturity=
                1.0,

            a=
                0.02,

            b=
                0.10,

            rho=
                -0.30,

            m=
                0.0,

            sigma=
                0.20,

            rmse=
                0.0,

            observation_count=
                3,
        )
    )

    k = np.array(
        [
            -0.1,
            0.0,
            0.1,
        ]
    )

    direct = (
        svi_total_variance(
            log_moneyness=
                k,

            a=
                parameters.a,

            b=
                parameters.b,

            rho=
                parameters.rho,

            m=
                parameters.m,

            sigma=
                parameters.sigma,
        )
    )

    wrapped = (
        svi_total_variance_from_parameters(
            k,
            parameters,
        )
    )

    assert np.allclose(
        direct,
        wrapped,
    )


def test_svi_smile_fits_three_strikes():
    quotes = [
        make_quote(
            90.0,
            1.0,
            0.24,
        ),

        make_quote(
            100.0,
            1.0,
            0.20,
        ),

        make_quote(
            110.0,
            1.0,
            0.22,
        ),
    ]

    result = (
        fit_svi_smile(
            quotes=
                quotes,

            spot=
                100.0,

            maturity=
                1.0,
        )
    )

    assert (
        result
        .parameters
        .observation_count
        == 3
    )

    assert (
        result.parameters.b
        >= 0.0
    )

    assert (
        -1.0
        < result.parameters.rho
        < 1.0
    )

    assert (
        result.parameters.sigma
        > 0.0
    )

    assert len(
        result.points
    ) == 51

    for point in (
        result.points
    ):
        assert (
            point.fitted_iv
            > 0.0
        )

        assert (
            point.total_variance
            > 0.0
        )


def test_svi_collapses_call_put_duplicates():
    quotes = [
        make_quote(
            90.0,
            1.0,
            0.24,
            "call",
        ),

        make_quote(
            90.0,
            1.0,
            0.25,
            "put",
        ),

        make_quote(
            100.0,
            1.0,
            0.20,
            "call",
        ),

        make_quote(
            100.0,
            1.0,
            0.21,
            "put",
        ),

        make_quote(
            110.0,
            1.0,
            0.22,
            "call",
        ),

        make_quote(
            110.0,
            1.0,
            0.23,
            "put",
        ),
    ]

    result = (
        fit_svi_smile(
            quotes=
                quotes,

            spot=
                100.0,

            maturity=
                1.0,
        )
    )

    assert (
        result
        .parameters
        .observation_count
        == 3
    )


def test_svi_requires_three_distinct_strikes():
    quotes = [
        make_quote(
            95.0,
            1.0,
            0.22,
        ),

        make_quote(
            105.0,
            1.0,
            0.21,
        ),
    ]

    with pytest.raises(
        ValueError,
        match=(
            "at least 3 "
            "distinct strikes"
        ),
    ):
        fit_svi_smile(
            quotes=
                quotes,

            spot=
                100.0,

            maturity=
                1.0,
        )


def test_svi_surface_fits_multiple_maturities():
    quotes = []

    for maturity in (
        0.5,
        1.0,
    ):
        quotes.extend(
            [
                make_quote(
                    90.0,
                    maturity,
                    0.24,
                ),

                make_quote(
                    100.0,
                    maturity,
                    0.20,
                ),

                make_quote(
                    110.0,
                    maturity,
                    0.22,
                ),
            ]
        )

    result = (
        fit_svi_surface(
            quotes=
                quotes,

            spot=
                100.0,
        )
    )

    assert (
        result
        .fitted_maturity_count
        == 2
    )

    assert len(
        result.smiles
    ) == 2

    assert (
        len(
            result
            .calendar_diagnostics
        )
        == 1
    )


def test_svi_surface_skips_insufficient_maturity():
    quotes = [
        make_quote(
            90.0,
            0.5,
            0.24,
        ),

        make_quote(
            100.0,
            0.5,
            0.20,
        ),

        make_quote(
            110.0,
            0.5,
            0.22,
        ),

        make_quote(
            95.0,
            1.0,
            0.21,
        ),

        make_quote(
            105.0,
            1.0,
            0.22,
        ),
    ]

    result = (
        fit_svi_surface(
            quotes=
                quotes,

            spot=
                100.0,
        )
    )

    assert (
        result
        .fitted_maturity_count
        == 1
    )

    assert (
        result
        .smiles[0]
        .parameters
        .maturity
        == pytest.approx(
            0.5
        )
    )

    assert (
        result
        .calendar_diagnostics
        == []
    )

    assert (
        result.calendar_warning
        is False
    )


def test_calendar_diagnostic_passes_when_total_variance_increases():
    shorter = (
        make_synthetic_smile(
            maturity=
                0.5,

            a=
                0.02,
        )
    )

    longer = (
        make_synthetic_smile(
            maturity=
                1.0,

            a=
                0.04,
        )
    )

    diagnostics = (
        build_calendar_diagnostics(
            [
                shorter,
                longer,
            ]
        )
    )

    assert len(
        diagnostics
    ) == 1

    diagnostic = (
        diagnostics[0]
    )

    assert (
        diagnostic
        .shorter_maturity
        == pytest.approx(
            0.5
        )
    )

    assert (
        diagnostic
        .longer_maturity
        == pytest.approx(
            1.0
        )
    )

    assert (
        diagnostic
        .violation_detected
        is False
    )

    assert (
        diagnostic
        .violation_count
        == 0
    )

    assert (
        diagnostic
        .minimum_variance_difference
        >= -1e-8
    )


def test_calendar_diagnostic_detects_decreasing_total_variance():
    shorter = (
        make_synthetic_smile(
            maturity=
                0.5,

            a=
                0.05,
        )
    )

    longer = (
        make_synthetic_smile(
            maturity=
                1.0,

            a=
                0.02,
        )
    )

    diagnostics = (
        build_calendar_diagnostics(
            [
                shorter,
                longer,
            ]
        )
    )

    assert len(
        diagnostics
    ) == 1

    diagnostic = (
        diagnostics[0]
    )

    assert (
        diagnostic
        .violation_detected
        is True
    )

    assert (
        diagnostic
        .violation_count
        > 0
    )

    assert (
        diagnostic
        .minimum_variance_difference
        < 0.0
    )


def test_invalid_spot_rejected():
    quotes = [
        make_quote(
            90.0,
            1.0,
            0.24,
        ),

        make_quote(
            100.0,
            1.0,
            0.20,
        ),

        make_quote(
            110.0,
            1.0,
            0.22,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="spot must be positive",
    ):
        fit_svi_surface(
            quotes=
                quotes,

            spot=
                0.0,
        )


def test_invalid_calendar_grid_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "grid_points must be >= 2"
        ),
    ):
        build_calendar_diagnostics(
            smiles=[],
            grid_points=1,
        )