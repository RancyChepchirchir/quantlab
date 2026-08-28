from typing import List, Optional

from fastapi import (
    APIRouter,
    HTTPException,
)

from pydantic import (
    BaseModel,
    Field,
)

from app.services.volatility_surface import (
    OptionQuote,
    calibrate_option_chain,
)

from app.services.volatility_diagnostics import (
    calculate_volatility_diagnostics,
)

from app.services.volatility_interpolation import (
    interpolate_volatility_surface,
)

from app.services.svi import (
    fit_svi_surface,
)

from app.services.ssvi import (
    fit_ssvi_surface,
)

from app.services.volatility_model_comparison import (
    compare_svi_and_ssvi,
)

from app.services.volatility_arbitrage_layers import (
    compare_arbitrage_layers,
)

router = APIRouter(
    prefix="/calibration",
    tags=["calibration"],
)


# =============================================================
# Request models
# =============================================================


class OptionQuoteRequest(
    BaseModel
):
    strike: float = Field(
        gt=0
    )

    maturity: float = Field(
        gt=0
    )

    market_price: float = Field(
        gt=0
    )

    option_type: str = "call"


class VolatilitySurfaceRequest(
    BaseModel
):
    spot: float = Field(
        gt=0
    )

    rate: float

    dividend_yield: float = 0.0

    quotes: List[
        OptionQuoteRequest
    ]


# =============================================================
# SSVI response models
# =============================================================


class SSVIParametersResponse(
    BaseModel
):
    eta: float
    rho: float
    gamma: float

    rmse: float

    observation_count: int
    maturity_count: int


class SSVIAtmSliceResponse(
    BaseModel
):
    maturity: float

    forward: float

    atm_strike: float
    atm_implied_volatility: float

    theta: float


class SSVIPointResponse(
    BaseModel
):
    strike: float
    maturity: float

    forward: float

    log_forward_moneyness: float

    theta: float

    observed_iv: Optional[
        float
    ] = None

    fitted_iv: float

    observed_total_variance: Optional[
        float
    ] = None

    fitted_total_variance: float


class SSVIArbitrageDiagnosticResponse(
    BaseModel
):
    maturity: float

    theta: float
    phi: float

    first_butterfly_bound: float
    second_butterfly_bound: float

    first_bound_satisfied: bool
    second_bound_satisfied: bool

    butterfly_warning: bool


class SSVICalendarDiagnosticResponse(
    BaseModel
):
    shorter_maturity: float
    longer_maturity: float

    minimum_variance_difference: float

    violation_detected: bool
    violation_count: int

    comparison_point_count: int


class SSVIResponse(
    BaseModel
):
    available: bool

    parameters: Optional[
        SSVIParametersResponse
    ] = None

    atm_slices: List[
        SSVIAtmSliceResponse
    ] = []

    points: List[
        SSVIPointResponse
    ] = []

    arbitrage_diagnostics: List[
        SSVIArbitrageDiagnosticResponse
    ] = []

    calendar_diagnostics: List[
        SSVICalendarDiagnosticResponse
    ] = []

    butterfly_warning: Optional[
        bool
    ] = None

    calendar_warning: Optional[
        bool
    ] = None

    message: Optional[
        str
    ] = None


# =============================================================
# Endpoint
# =============================================================

def _serialize_arbitrage_diagnostics(
    diagnostics,
):
    return {
        "calendar_arbitrage_free":
            diagnostics
            .calendar_arbitrage_free,

        "butterfly_arbitrage_free":
            diagnostics
            .butterfly_arbitrage_free,

        "arbitrage_free":
            diagnostics
            .arbitrage_free,

        "calendar_violation_count":
            diagnostics
            .calendar_violation_count,

        "butterfly_violation_count":
            diagnostics
            .butterfly_violation_count,

        "total_violation_count":
            diagnostics
            .total_violation_count,

        "calendar_violations": [
            {
                "strike":
                    item.strike,

                "earlier_maturity":
                    item.earlier_maturity,

                "later_maturity":
                    item.later_maturity,

                "earlier_total_variance":
                    item
                    .earlier_total_variance,

                "later_total_variance":
                    item
                    .later_total_variance,

                "difference":
                    item.difference,
            }
            for item
            in diagnostics
            .calendar_violations
        ],

        "butterfly_violations": [
            {
                "maturity":
                    item.maturity,

                "left_strike":
                    item.left_strike,

                "center_strike":
                    item.center_strike,

                "right_strike":
                    item.right_strike,

                "curvature":
                    item.curvature,
            }
            for item
            in diagnostics
            .butterfly_violations
        ],
    }

@router.post(
    "/volatility-surface"
)
def calibrate_volatility_surface(
    request: VolatilitySurfaceRequest,
):
    # ---------------------------------------------------------
    # Convert API input to service-layer quotes
    # ---------------------------------------------------------

    quotes = [
        OptionQuote(
            strike=quote.strike,
            maturity=quote.maturity,
            market_price=quote.market_price,
            option_type=quote.option_type,
        )
        for quote in request.quotes
    ]

    # ---------------------------------------------------------
    # Core implied-volatility calibration
    # ---------------------------------------------------------

    try:
        result = (
            calibrate_option_chain(
                spot=request.spot,
                rate=request.rate,
                dividend_yield=(
                    request.dividend_yield
                ),
                quotes=quotes,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    try:
        diagnostics = (
            calculate_volatility_diagnostics(
                quotes=result.calibrated,
                spot=request.spot,
                rate=request.rate,
                dividend_yield=(
                    request.dividend_yield
                ),
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # ---------------------------------------------------------
    # IDW baseline surface
    # ---------------------------------------------------------

    try:
        surface_grid = (
            interpolate_volatility_surface(
                result.calibrated,
                strike_points=25,
                maturity_points=15,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # ---------------------------------------------------------
    # Raw SVI
    #
    # This is the existing maturity-by-maturity SVI model.
    # Keep it separate from the new SSVI surface.
    # ---------------------------------------------------------

    try:
        svi_result = (
            fit_svi_surface(
                quotes=result.calibrated,
                spot=request.spot,
                minimum_strikes=3,
                grid_points=51,
                calendar_grid_points=101,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # ---------------------------------------------------------
    # SSVI
    #
    # SSVI is deliberately OPTIONAL.
    #
    # A valid ordinary volatility calibration should not fail
    # merely because there are too few maturities for SSVI.
    # ---------------------------------------------------------

    ssvi_result = None

    ssvi_response = SSVIResponse(
        available=False,
        message=(
            "SSVI requires at least two "
            "maturities with sufficient "
            "strike observations."
        ),
    )

    try:
        ssvi_result = (
            fit_ssvi_surface(
                quotes=result.calibrated,
                spot=request.spot,
                rate=request.rate,
                dividend_yield=(
                    request.dividend_yield
                ),
                minimum_strikes=3,
                grid_points_per_maturity=101,
                calendar_grid_points=201,
            )
        )

        ssvi_response = (
            SSVIResponse(
                available=True,

                parameters=(
                    SSVIParametersResponse(
                        eta=(
                            ssvi_result
                            .parameters
                            .eta
                        ),
                        rho=(
                            ssvi_result
                            .parameters
                            .rho
                        ),
                        gamma=(
                            ssvi_result
                            .parameters
                            .gamma
                        ),
                        rmse=(
                            ssvi_result
                            .parameters
                            .rmse
                        ),
                        observation_count=(
                            ssvi_result
                            .parameters
                            .observation_count
                        ),
                        maturity_count=(
                            ssvi_result
                            .parameters
                            .maturity_count
                        ),
                    )
                ),

                atm_slices=[
                    SSVIAtmSliceResponse(
                        maturity=(
                            item.maturity
                        ),
                        forward=(
                            item.forward
                        ),
                        atm_strike=(
                            item.atm_strike
                        ),
                        atm_implied_volatility=(
                            item
                            .atm_implied_volatility
                        ),
                        theta=(
                            item.theta
                        ),
                    )
                    for item
                    in ssvi_result.atm_slices
                ],

                points=[
                    SSVIPointResponse(
                        strike=(
                            item.strike
                        ),
                        maturity=(
                            item.maturity
                        ),
                        forward=(
                            item.forward
                        ),
                        log_forward_moneyness=(
                            item
                            .log_forward_moneyness
                        ),
                        theta=(
                            item.theta
                        ),
                        observed_iv=(
                            item.observed_iv
                        ),
                        fitted_iv=(
                            item.fitted_iv
                        ),
                        observed_total_variance=(
                            item
                            .observed_total_variance
                        ),
                        fitted_total_variance=(
                            item
                            .fitted_total_variance
                        ),
                    )
                    for item
                    in ssvi_result.points
                ],

                arbitrage_diagnostics=[
                    SSVIArbitrageDiagnosticResponse(
                        maturity=(
                            item.maturity
                        ),
                        theta=(
                            item.theta
                        ),
                        phi=(
                            item.phi
                        ),
                        first_butterfly_bound=(
                            item
                            .first_butterfly_bound
                        ),
                        second_butterfly_bound=(
                            item
                            .second_butterfly_bound
                        ),
                        first_bound_satisfied=(
                            item
                            .first_bound_satisfied
                        ),
                        second_bound_satisfied=(
                            item
                            .second_bound_satisfied
                        ),
                        butterfly_warning=(
                            item
                            .butterfly_warning
                        ),
                    )
                    for item
                    in (
                        ssvi_result
                        .arbitrage_diagnostics
                    )
                ],

                calendar_diagnostics=[
                    SSVICalendarDiagnosticResponse(
                        shorter_maturity=(
                            item
                            .shorter_maturity
                        ),
                        longer_maturity=(
                            item
                            .longer_maturity
                        ),
                        minimum_variance_difference=(
                            item
                            .minimum_variance_difference
                        ),
                        violation_detected=(
                            item
                            .violation_detected
                        ),
                        violation_count=(
                            item
                            .violation_count
                        ),
                        comparison_point_count=(
                            item
                            .comparison_point_count
                        ),
                    )
                    for item
                    in (
                        ssvi_result
                        .calendar_diagnostics
                    )
                ],

                butterfly_warning=(
                    ssvi_result
                    .butterfly_warning
                ),

                calendar_warning=(
                    ssvi_result
                    .calendar_warning
                ),

                message=None,
            )
        )

    except ValueError as error:
        ssvi_response = (
            SSVIResponse(
                available=False,
                message=str(error),
            )
        )

    # =========================================================
    # SVI vs SSVI model comparison
    # =========================================================

    model_comparison = None

    if ssvi_response.available:
        try:
            model_comparison = (
                compare_svi_and_ssvi(
                    quotes=
                        result.calibrated,

                    svi_surface=
                        svi_result,

                    ssvi_surface=
                        ssvi_result,

                    spot=
                        request.spot,
                )
            )

        except ValueError:
            model_comparison = None    

    # =====================================================
    # Market vs SVI vs SSVI arbitrage diagnostics
    # =====================================================

    arbitrage_layers = None

    if (
        ssvi_result is not None
    ):
        try:
            arbitrage_layers = (
                compare_arbitrage_layers(
                    quotes=(
                        result.calibrated
                    ),
                    svi_surface=(
                        svi_result
                    ),
                    ssvi_surface=(
                        ssvi_result
                    ),
                    spot=(
                        request.spot
                    ),
                    rate=(
                        request.rate
                    ),
                    dividend_yield=(
                        request.dividend_yield
                    ),
                )
            )

        except ValueError:
            arbitrage_layers = None

    # =========================================================
    # Response
    # =========================================================

    return {
        # -----------------------------------------------------
        # Inputs
        # -----------------------------------------------------

        "spot":
            request.spot,

        "rate":
            request.rate,

        "dividend_yield":
            request.dividend_yield,

        # -----------------------------------------------------
        # Calibration summary
        # -----------------------------------------------------

        "quote_count":
            result.input_count,

        "calibrated_count":
            result.calibrated_count,

        "rejected_count":
            result.rejected_count,

        "success_rate":
            result.success_rate,

        # -----------------------------------------------------
        # Calibrated observations
        # -----------------------------------------------------

        "quotes": [
            {
                "strike":
                    quote.strike,

                "maturity":
                    quote.maturity,

                "market_price":
                    quote.market_price,

                "option_type":
                    quote.option_type,

                # ---------------------------------------------
                # Black-Scholes IV
                # ---------------------------------------------

                "implied_volatility":
                    quote
                    .implied_volatility,

                "implied_volatility_percent":
                    (
                        100.0
                        * quote
                        .implied_volatility
                    ),

                # ---------------------------------------------
                # American CRR IV
                # ---------------------------------------------

                "american_implied_volatility":
                    quote
                    .american_implied_volatility,

                "american_implied_volatility_percent":
                    (
                        100.0
                        * quote
                        .american_implied_volatility
                        if quote
                        .american_implied_volatility
                        is not None
                        else None
                    ),

                # ---------------------------------------------
                # American / European difference
                # ---------------------------------------------

                "american_iv_difference":
                    quote
                    .american_iv_difference,

                "american_iv_difference_percentage_points":
                    (
                        100.0
                        * quote
                        .american_iv_difference
                        if quote
                        .american_iv_difference
                        is not None
                        else None
                    ),

                "american_iv_converged":
                    quote
                    .american_iv_converged,
            }
            for quote
            in result.calibrated
        ],

        # -----------------------------------------------------
        # Rejected observations
        # -----------------------------------------------------

        "rejected_quotes": [
            {
                "strike":
                    quote.strike,

                "maturity":
                    quote.maturity,

                "market_price":
                    quote.market_price,

                "option_type":
                    quote.option_type,

                "reason":
                    quote.reason,
            }
            for quote
            in result.rejected
        ],

        # -----------------------------------------------------
        # Diagnostics
        # -----------------------------------------------------

        "diagnostics": {
            # -------------------------------------------------
            # Moneyness
            # -------------------------------------------------

            "moneyness": [
                {
                    "strike":
                        item.strike,

                    "maturity":
                        item.maturity,

                    "option_type":
                        item.option_type,

                    "implied_volatility":
                        item
                        .implied_volatility,

                    "implied_volatility_percent":
                        (
                            100.0
                            * item
                            .implied_volatility
                        ),

                    "moneyness":
                        item.moneyness,

                    "log_moneyness":
                        item.log_moneyness,
                }
                for item
                in diagnostics.moneyness
            ],

            # -------------------------------------------------
            # Skew
            # -------------------------------------------------

            "skew": [
                {
                    "maturity":
                        item.maturity,

                    "atm_strike":
                        item.atm_strike,

                    "atm_implied_volatility":
                        item
                        .atm_implied_volatility,

                    "atm_implied_volatility_percent":
                        (
                            100.0
                            * item
                            .atm_implied_volatility
                        ),

                    "skew_slope":
                        item.skew_slope,

                    "observation_count":
                        item
                        .observation_count,
                }
                for item
                in diagnostics.skew
            ],

            # -------------------------------------------------
            # ATM term structure
            # -------------------------------------------------

            "atm_term_structure": [
                {
                    "maturity":
                        item.maturity,

                    "atm_strike":
                        item.atm_strike,

                    "atm_implied_volatility":
                        item
                        .atm_implied_volatility,

                    "atm_implied_volatility_percent":
                        (
                            100.0
                            * item
                            .atm_implied_volatility
                        ),
                }
                for item
                in (
                    diagnostics
                    .atm_term_structure
                )
            ],

            # -------------------------------------------------
            # European parity reference
            # -------------------------------------------------

            "put_call_parity": [
                {
                    "strike":
                        item.strike,

                    "maturity":
                        item.maturity,

                    "call_price":
                        item.call_price,

                    "put_price":
                        item.put_price,

                    "theoretical_difference":
                        item
                        .theoretical_difference,

                    "observed_difference":
                        item
                        .observed_difference,

                    "parity_error":
                        item.parity_error,

                    "absolute_parity_error":
                        abs(
                            item.parity_error
                        ),
                }
                for item
                in (
                    diagnostics
                    .put_call_parity
                )
            ],

            "mean_absolute_parity_error":
                diagnostics
                .mean_absolute_parity_error,

            "max_absolute_parity_error":
                diagnostics
                .max_absolute_parity_error,
        },

        # -----------------------------------------------------
        # IDW baseline
        # -----------------------------------------------------

        "surface_grid": {
            "strikes":
                surface_grid.strikes,

            "maturities":
                surface_grid.maturities,

            "observed_strike_count":
                surface_grid
                .observed_strike_count,

            "observed_maturity_count":
                surface_grid
                .observed_maturity_count,

            "is_two_dimensional":
                surface_grid
                .is_two_dimensional,

            "points": [
                {
                    "strike":
                        point.strike,

                    "maturity":
                        point.maturity,

                    "implied_volatility":
                        point
                        .implied_volatility,

                    "implied_volatility_percent":
                        (
                            100.0
                            * point
                            .implied_volatility
                        ),
                }
                for point
                in surface_grid.points
            ],
        },

        # =====================================================
        # Raw SVI
        # =====================================================

        "svi": {
            "fitted_maturity_count":
                svi_result
                .fitted_maturity_count,

            "calendar_warning":
                svi_result
                .calendar_warning,

            "calendar_diagnostics": [
                {
                    "shorter_maturity":
                        diagnostic
                        .shorter_maturity,

                    "longer_maturity":
                        diagnostic
                        .longer_maturity,

                    "minimum_variance_difference":
                        diagnostic
                        .minimum_variance_difference,

                    "violation_detected":
                        diagnostic
                        .violation_detected,

                    "violation_count":
                        diagnostic
                        .violation_count,

                    "comparison_point_count":
                        diagnostic
                        .comparison_point_count,

                    "violation_fraction":
                        (
                            diagnostic
                            .violation_count
                            / diagnostic
                            .comparison_point_count
                            if (
                                diagnostic
                                .comparison_point_count
                                > 0
                            )
                            else 0.0
                        ),
                }
                for diagnostic
                in (
                    svi_result
                    .calendar_diagnostics
                )
            ],

            "smiles": [
                {
                    "parameters": {
                        "maturity":
                            smile
                            .parameters
                            .maturity,

                        "a":
                            smile
                            .parameters
                            .a,

                        "b":
                            smile
                            .parameters
                            .b,

                        "rho":
                            smile
                            .parameters
                            .rho,

                        "m":
                            smile
                            .parameters
                            .m,

                        "sigma":
                            smile
                            .parameters
                            .sigma,

                        "rmse":
                            smile
                            .parameters
                            .rmse,

                        "observation_count":
                            smile
                            .parameters
                            .observation_count,
                    },

                    "points": [
                        {
                            "strike":
                                point.strike,

                            "maturity":
                                point.maturity,

                            "log_moneyness":
                                point
                                .log_moneyness,

                            "observed_iv":
                                point
                                .observed_iv,

                            "observed_iv_percent":
                                (
                                    100.0
                                    * point
                                    .observed_iv
                                    if point
                                    .observed_iv
                                    is not None
                                    else None
                                ),

                            "fitted_iv":
                                point
                                .fitted_iv,

                            "fitted_iv_percent":
                                (
                                    100.0
                                    * point
                                    .fitted_iv
                                ),

                            "total_variance":
                                point
                                .total_variance,
                        }
                        for point
                        in smile.points
                    ],

                    "arbitrage": {
                        "maturity":
                            smile
                            .arbitrage
                            .maturity,

                        "minimum_total_variance":
                            smile
                            .arbitrage
                            .minimum_total_variance,

                        "negative_variance_detected":
                            smile
                            .arbitrage
                            .negative_variance_detected,

                        "invalid_parameter_region":
                            smile
                            .arbitrage
                            .invalid_parameter_region,

                        "butterfly_warning":
                            smile
                            .arbitrage
                            .butterfly_warning,
                    },
                }
                for smile
                in svi_result.smiles
            ],
        },

        # =====================================================
        # SSVI
        # =====================================================

        "ssvi":
            ssvi_response
            .model_dump(),

        # =====================================================
        # SVI vs SSVI model comparison
        # =====================================================

        "model_comparison": (
            {
                "svi": {
                    "rmse":
                        model_comparison
                        .svi
                        .rmse,

                    "mae":
                        model_comparison
                        .svi
                        .mae,

                    "max_absolute_error":
                        model_comparison
                        .svi
                        .max_absolute_error,

                    "observation_count":
                        model_comparison
                        .svi
                        .observation_count,
                },

                "ssvi": {
                    "rmse":
                        model_comparison
                        .ssvi
                        .rmse,

                    "mae":
                        model_comparison
                        .ssvi
                        .mae,

                    "max_absolute_error":
                        model_comparison
                        .ssvi
                        .max_absolute_error,

                    "observation_count":
                        model_comparison
                        .ssvi
                        .observation_count,
                },

                "better_rmse_model":
                    model_comparison
                    .better_rmse_model,

                "better_mae_model":
                    model_comparison
                    .better_mae_model,

                "maturity_comparisons": [
                    {
                        "maturity":
                            item.maturity,

                        "observation_count":
                            item
                            .observation_count,

                        "svi": {
                            "rmse":
                                item.svi.rmse,

                            "mae":
                                item.svi.mae,

                            "max_absolute_error":
                                item
                                .svi
                                .max_absolute_error,

                            "observation_count":
                                item
                                .svi
                                .observation_count,
                        },

                        "ssvi": {
                            "rmse":
                                item.ssvi.rmse,

                            "mae":
                                item.ssvi.mae,

                            "max_absolute_error":
                                item
                                .ssvi
                                .max_absolute_error,

                            "observation_count":
                                item
                                .ssvi
                                .observation_count,
                        },

                        "better_rmse_model":
                            item
                            .better_rmse_model,

                        "better_mae_model":
                            item
                            .better_mae_model,
                    }

                    for item
                    in (
                        model_comparison
                        .maturity_comparisons
                    )
                ],
            }

            if model_comparison
            is not None

            else None
        ),

        # =====================================================
        # Market vs SVI vs SSVI arbitrage diagnostics
        # =====================================================

        "arbitrage_layers": (
            {
                "market": {
                    "name":
                        arbitrage_layers
                        .market
                        .name,

                    "diagnostics":
                        _serialize_arbitrage_diagnostics(
                            arbitrage_layers
                            .market
                            .diagnostics
                        ),
                },

                "svi": {
                    "name":
                        arbitrage_layers
                        .svi
                        .name,

                    "diagnostics":
                        _serialize_arbitrage_diagnostics(
                            arbitrage_layers
                            .svi
                            .diagnostics
                        ),
                },

                "ssvi": {
                    "name":
                        arbitrage_layers
                        .ssvi
                        .name,

                    "diagnostics":
                        _serialize_arbitrage_diagnostics(
                            arbitrage_layers
                            .ssvi
                            .diagnostics
                        ),
                },
            }

            if arbitrage_layers
            is not None

            else None
        ),

    }