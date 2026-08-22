from typing import List

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


router = APIRouter(
    prefix="/calibration",
    tags=["calibration"],
)


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


@router.post(
    "/volatility-surface"
)
def calibrate_volatility_surface(
    request: VolatilitySurfaceRequest,
):
    # ---------------------------------------------------------
    # Convert API request to service-layer objects
    # ---------------------------------------------------------

    quotes = [
        OptionQuote(
            strike=
                quote.strike,

            maturity=
                quote.maturity,

            market_price=
                quote.market_price,

            option_type=
                quote.option_type,
        )
        for quote
        in request.quotes
    ]

    # ---------------------------------------------------------
    # Core IV calibration
    # ---------------------------------------------------------

    try:
        result = (
            calibrate_option_chain(
                spot=
                    request.spot,

                rate=
                    request.rate,

                dividend_yield=
                    request.dividend_yield,

                quotes=
                    quotes,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # ---------------------------------------------------------
    # Volatility diagnostics
    # ---------------------------------------------------------

    try:
        diagnostics = (
            calculate_volatility_diagnostics(
                quotes=
                    result.calibrated,

                spot=
                    request.spot,

                rate=
                    request.rate,

                dividend_yield=
                    request.dividend_yield,
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
    # SVI fitting + cross-maturity diagnostics
    # ---------------------------------------------------------

    try:
        svi_result = (
            fit_svi_surface(
                quotes=
                    result.calibrated,

                spot=
                    request.spot,

                minimum_strikes=
                    3,

                grid_points=
                    51,

                calendar_grid_points=
                    101,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------

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
                # European / Black-Scholes IV
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
                # BS vs American difference
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
                in diagnostics
                .atm_term_structure
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
                in diagnostics
                .put_call_parity
            ],

            "mean_absolute_parity_error":
                diagnostics
                .mean_absolute_parity_error,

            "max_absolute_parity_error":
                diagnostics
                .max_absolute_parity_error,
        },

        # -----------------------------------------------------
        # IDW baseline surface
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

        # -----------------------------------------------------
        # SVI
        # -----------------------------------------------------

        "svi": {
            "fitted_maturity_count":
                svi_result
                .fitted_maturity_count,

            # -------------------------------------------------
            # Global cross-maturity status
            # -------------------------------------------------

            "calendar_warning":
                svi_result
                .calendar_warning,

            # -------------------------------------------------
            # Calendar-arbitrage diagnostics
            # -------------------------------------------------

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
                            if diagnostic
                            .comparison_point_count
                            > 0
                            else 0.0
                        ),
                }
                for diagnostic
                in svi_result
                .calendar_diagnostics
            ],

            # -------------------------------------------------
            # Individual fitted smiles
            # -------------------------------------------------

            "smiles": [
                {
                    # -----------------------------------------
                    # Parameters
                    # -----------------------------------------

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

                    # -----------------------------------------
                    # Dense fitted smile
                    # -----------------------------------------

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

                    # -----------------------------------------
                    # Within-smile arbitrage diagnostics
                    # -----------------------------------------

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
    }