from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.american_surface_atlas import (
    build_american_surface_atlas,
)


router = APIRouter(
    prefix="/research",
    tags=["research"],
)


class AmericanSurfaceAtlasRequest(BaseModel):
    spot: float = Field(
        default=100.0,
        gt=0,
    )

    strike: float = Field(
        default=100.0,
        gt=0,
    )

    rate: float = 0.05

    volatility: float = Field(
        default=0.20,
        gt=0,
    )

    maturity: float = Field(
        default=1.0,
        gt=0,
    )

    dividend_yield: float = 0.0

    s_max: float = Field(
        default=250.0,
        gt=0,
    )

    space_steps: int = Field(
        default=80,
        ge=30,
        le=200,
    )

    time_steps: int = Field(
        default=80,
        ge=30,
        le=200,
    )

    crr_steps: int = Field(
        default=150,
        ge=25,
        le=500,
    )

    crr_surface_points: int = Field(
        default=31,
        ge=15,
        le=51,
    )

    boundary_tolerance: float = Field(
        default=1e-4,
        gt=0,
    )


@router.post(
    "/american-surface-atlas"
)
def american_surface_atlas(
    request: AmericanSurfaceAtlasRequest,
):
    atlas = build_american_surface_atlas(
        spot=request.spot,
        strike=request.strike,
        rate=request.rate,
        volatility=request.volatility,
        maturity=request.maturity,
        dividend_yield=
            request.dividend_yield,
        s_max=request.s_max,
        space_steps=request.space_steps,
        time_steps=request.time_steps,
        crr_steps=request.crr_steps,
        crr_surface_points=
            request.crr_surface_points,
        boundary_tolerance=
            request.boundary_tolerance,
    )

    return {
        "option_type": "put",

        "reference_method":
            "projected_crank_nicolson",

        "input": {
            "spot": request.spot,
            "strike": request.strike,
            "rate": request.rate,
            "volatility":
                request.volatility,
            "maturity":
                request.maturity,
            "dividend_yield":
                request.dividend_yield,
            "s_max":
                request.s_max,
        },

        "grid": {
            "spot":
                atlas.spot_grid,

            "time_to_maturity":
                atlas.time_to_maturity_grid,

            "space_steps":
                atlas.space_steps,

            "time_steps":
                atlas.time_steps,

            "crr_steps":
                atlas.crr_steps,
        },

        "surfaces": {
            "crank_nicolson":
                atlas.cn_surface,

            "crr":
                atlas.crr_surface,

            "pinn_v2":
                atlas.pinn_surface,  

            "payoff":
                atlas.payoff_surface,

            "exercise_gap":
                atlas.exercise_gap_surface,
        },

        "errors": {
            "crr_signed":
                atlas.crr_signed_error_surface,

            "crr_absolute":
                atlas.crr_absolute_error_surface,

            "pinn_signed":
                atlas.pinn_signed_error_surface,

            "pinn_absolute":
                atlas.pinn_absolute_error_surface,
        },

        "pinn_convergence": {
            "available":
                atlas.pinn_convergence_available,

            "epochs":
                atlas.pinn_convergence_epochs,

            "surfaces":
                atlas.pinn_convergence_surfaces,

            "signed_errors":
                atlas.pinn_convergence_signed_errors,

            "absolute_errors":
                atlas.pinn_convergence_absolute_errors,

            "metrics":
                atlas.pinn_convergence_metrics,

            "improvement_surface":
                atlas.pinn_improvement_surface,

            "boundary_diagnostics":
                atlas.pinn_boundary_diagnostics,

            "boundary_distance_profiles":
                atlas.pinn_boundary_distance_profiles,
        },

        "exercise_boundary":
            atlas.exercise_boundary,

        "pinn": {
            "available":
                atlas.pinn_available,

            "method":
                atlas.pinn_method,

            "final_loss":
                atlas.pinn_final_loss,

            "training_seconds":
                atlas.pinn_training_seconds,

            "mae_vs_cn":
                atlas.pinn_mae,

            "rmse_vs_cn":
                atlas.pinn_rmse,

            "max_absolute_error_vs_cn":
                atlas.pinn_max_absolute_error,
        },

        "summary": {
            "min_price":
                atlas.min_price,

            "max_price":
                atlas.max_price,

            "max_exercise_gap":
                atlas.max_exercise_gap,

            "max_crr_absolute_error":
                atlas.max_crr_absolute_error,
        },
    }