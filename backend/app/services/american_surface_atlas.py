from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.models.black_scholes import OptionInputs
from app.models.binomial import binomial_price
from app.models.american_finite_difference import (
    projected_crank_nicolson_put,
)

PINN_SURFACE_PATH = (
    Path(__file__).resolve().parents[2]
    / "experiments"
    / "results"
    / "american_pinn_v2_surface.json"
)

PINN_CONVERGENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "experiments"
    / "results"
    / "american_pinn_convergence_atlas.json"
)

@dataclass(frozen=True)
class AmericanSurfaceAtlas:
    spot_grid: List[float]
    time_to_maturity_grid: List[float]

    cn_surface: List[List[float]]
    crr_surface: List[List[float]]

    pinn_surface: Optional[
    List[List[float]]]
    pinn_signed_error_surface: Optional[
    List[List[float]]]
    pinn_absolute_error_surface: Optional[
    List[List[float]]]

    payoff_surface: List[List[float]]
    exercise_gap_surface: List[List[float]]

    crr_signed_error_surface: List[List[float]]
    crr_absolute_error_surface: List[List[float]]

    pinn_available: bool
    pinn_method: Optional[str]
    pinn_final_loss: Optional[float]
    pinn_training_seconds: Optional[float]
    pinn_max_absolute_error: Optional[float]
    pinn_rmse: Optional[float]
    pinn_mae: Optional[float]

    pinn_convergence_available: bool
    pinn_convergence_epochs: List[int]
    pinn_convergence_surfaces: Dict[
        str,
        List[List[float]],]
    pinn_convergence_signed_errors: Dict[
        str,
        List[List[float]],]
    pinn_convergence_absolute_errors: Dict[
        str,
        List[List[float]],]
    pinn_convergence_metrics: Dict[
        str,
        Dict[str, float],]

    pinn_boundary_diagnostics: Dict[
    str,
    Dict,]

    pinn_boundary_distance_profiles: Dict[
    str,
    Dict,]

    pinn_improvement_surface: Optional[
        List[List[float]]]

    exercise_boundary: List[
        Dict[str, Optional[float]]
    ]

    min_price: float
    max_price: float
    max_exercise_gap: float
    max_crr_absolute_error: float

    space_steps: int
    time_steps: int
    crr_steps: int


def _estimate_exercise_boundary(
    spot_grid: np.ndarray,
    time_to_maturity_grid: np.ndarray,
    value_grid: np.ndarray,
    strike: float,
    tolerance: float,
) -> List[Dict[str, Optional[float]]]:

    payoff = np.maximum(
        strike - spot_grid,
        0.0,
    )

    boundary: List[
        Dict[str, Optional[float]]
    ] = []

    for time_index, tau in enumerate(
        time_to_maturity_grid
    ):
        option_values = value_grid[
            time_index,
            :,
        ]

        gap = option_values - payoff

        exercise_region = (
            (spot_grid < strike)
            & (gap <= tolerance)
        )

        candidates = spot_grid[
            exercise_region
        ]

        if candidates.size == 0:
            boundary_spot = None
        else:
            boundary_spot = float(
                np.max(candidates)
            )

        boundary.append(
            {
                "time_to_maturity":
                    float(tau),
                "spot":
                    boundary_spot,
            }
        )

    return boundary


def _build_crr_surface(
    *,
    spot_grid: np.ndarray,
    time_to_maturity_grid: np.ndarray,
    strike: float,
    rate: float,
    volatility: float,
    dividend_yield: float,
    crr_steps: int,
) -> np.ndarray:

    surface = np.zeros(
        (
            len(time_to_maturity_grid),
            len(spot_grid),
        ),
        dtype=float,
    )

    payoff = np.maximum(
        strike - spot_grid,
        0.0,
    )

    for time_index, tau in enumerate(
        time_to_maturity_grid
    ):
        # At expiry the value is exactly the payoff.
        if tau <= 1e-12:
            surface[
                time_index,
                :,
            ] = payoff

            continue

        for spot_index, current_spot in enumerate(
            spot_grid
        ):
            inputs = OptionInputs(
                spot=float(current_spot),
                strike=strike,
                rate=rate,
                volatility=volatility,
                maturity=float(tau),
                dividend_yield=
                    dividend_yield,
            )

            result = binomial_price(
                inputs,
                option_type="put",
                steps=crr_steps,
                american=True,
            )

            surface[
                time_index,
                spot_index,
            ] = result.price

    return surface

def _load_pinn_surface(
    *,
    target_spot_grid: np.ndarray,
    target_tau_grid: np.ndarray,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    dividend_yield: float,
):
    """
    Load the persisted PINN research surface and
    interpolate it onto the Atlas comparison grid.

    The artifact is parameter-specific. We only
    expose it when its contract matches the current
    Atlas parameters.
    """

    if not PINN_SURFACE_PATH.exists():
        return None

    with PINN_SURFACE_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:
        artifact = json.load(handle)

    artifact_input = artifact[
        "input"
    ]

    expected = {
        "strike": strike,
        "rate": rate,
        "volatility": volatility,
        "maturity": maturity,
        "dividend_yield":
            dividend_yield,
    }

    for key, expected_value in (
        expected.items()
    ):
        actual_value = float(
            artifact_input[key]
        )

        if not np.isclose(
            actual_value,
            expected_value,
            rtol=1e-8,
            atol=1e-10,
        ):
            return None

    source_spot = np.asarray(
        artifact["grid"]["spot"],
        dtype=float,
    )

    source_tau = np.asarray(
        artifact["grid"][
            "time_to_maturity"
        ],
        dtype=float,
    )

    source_surface = np.asarray(
        artifact["surface"],
        dtype=float,
    )

    expected_shape = (
        len(source_tau),
        len(source_spot),
    )

    if (
        source_surface.shape
        != expected_shape
    ):
        raise ValueError(
            "PINN surface artifact has "
            "an invalid grid shape."
        )

    # -------------------------------------------------
    # Interpolate along spot first.
    # -------------------------------------------------

    spot_interpolated = np.vstack(
        [
            np.interp(
                target_spot_grid,
                source_spot,
                row,
            )
            for row in source_surface
        ]
    )

    # -------------------------------------------------
    # Then interpolate along remaining maturity.
    # -------------------------------------------------

    target_surface = np.vstack(
        [
            np.interp(
                target_tau_grid,
                source_tau,
                spot_interpolated[:, j],
            )
            for j in range(
                len(target_spot_grid)
            )
        ]
    ).T

    return {
        "surface":
            target_surface,

        "method":
            artifact.get(
                "method"
            ),

        "final_loss":
            artifact.get(
                "training",
                {},
            ).get(
                "final_loss"
            ),

        "training_seconds":
            artifact.get(
                "training",
                {},
            ).get(
                "training_seconds"
            ),

        "diagnostics":
            artifact.get(
                "diagnostics",
                {},
            ),
    }

def _load_pinn_convergence(
    *,
    target_spot_grid: np.ndarray,
    target_tau_grid: np.ndarray,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    dividend_yield: float,
):
    if not PINN_CONVERGENCE_PATH.exists():
        return None

    with PINN_CONVERGENCE_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:
        artifact = json.load(handle)

    artifact_input = artifact["input"]

    expected = {
        "strike": strike,
        "rate": rate,
        "volatility": volatility,
        "maturity": maturity,
        "dividend_yield":
            dividend_yield,
    }

    for key, expected_value in (
        expected.items()
    ):
        actual_value = float(
            artifact_input[key]
        )

        if not np.isclose(
            actual_value,
            expected_value,
            rtol=1e-8,
            atol=1e-10,
        ):
            return None

    source_spot = np.asarray(
        artifact["grid"]["spot"],
        dtype=float,
    )

    source_tau = np.asarray(
        artifact["grid"][
            "time_to_maturity"
        ],
        dtype=float,
    )

    interpolated_snapshots = {}

    for (
        epoch,
        snapshot
    ) in artifact["snapshots"].items():

        source_surface = np.asarray(
            snapshot["surface"],
            dtype=float,
        )

        expected_shape = (
            len(source_tau),
            len(source_spot),
        )

        if (
            source_surface.shape
            != expected_shape
        ):
            raise ValueError(
                "PINN convergence surface "
                f"{epoch} has invalid shape."
            )

        # Spot interpolation.
        spot_interpolated = np.vstack(
            [
                np.interp(
                    target_spot_grid,
                    source_spot,
                    row,
                )
                for row
                in source_surface
            ]
        )

        # Time-to-maturity interpolation.
        target_surface = np.vstack(
            [
                np.interp(
                    target_tau_grid,
                    source_tau,
                    spot_interpolated[:, j],
                )
                for j in range(
                    len(
                        target_spot_grid
                    )
                )
            ]
        ).T

        interpolated_snapshots[
            str(epoch)
        ] = {
            "surface":
                target_surface,

            "training_loss":
                float(
                    snapshot[
                        "training_loss"
                    ]
                ),

            "elapsed_training_seconds":
                float(
                    snapshot[
                        "elapsed_training_seconds"
                    ]
                ),

            "inference_seconds":
                float(
                    snapshot[
                        "inference_seconds"
                    ]
                ),
        }

    epochs = sorted(
        int(epoch)
        for epoch in
        interpolated_snapshots.keys()
    )

    return {
        "epochs":
            epochs,

        "snapshots":
            interpolated_snapshots,

        "method":
            artifact.get(
                "method"
            ),
    }

def _boundary_error_diagnostics(
    *,
    spot_grid: np.ndarray,
    tau_grid: np.ndarray,
    absolute_error_surface: np.ndarray,
    exercise_boundary: List[
        Dict[str, Optional[float]]
    ],
    strike: float,
):
    """
    Compare approximation error near the
    estimated American exercise boundary
    against error away from it.

    A grid point is classified as
    near-boundary when:

        |S - S*(tau)| <= band_width

    where the band width is set to 5% of K.
    """

    band_width = (
        0.05 * strike
    )

    boundary_by_tau = {
        float(
            point[
                "time_to_maturity"
            ]
        ):
        point["spot"]

        for point
        in exercise_boundary

        if point["spot"]
        is not None
    }

    near_errors = []
    away_errors = []

    near_locations = []
    away_locations = []

    for tau_index, tau in enumerate(
        tau_grid
    ):
        if not boundary_by_tau:
            continue

        nearest_tau = min(
            boundary_by_tau.keys(),
            key=lambda value: abs(
                value - float(tau)
            ),
        )

        boundary_spot = (
            boundary_by_tau[
                nearest_tau
            ]
        )

        if boundary_spot is None:
            continue

        for spot_index, spot in enumerate(
            spot_grid
        ):
            error = float(
                absolute_error_surface[
                    tau_index,
                    spot_index,
                ]
            )

            distance = abs(
                float(spot)
                - float(
                    boundary_spot
                )
            )

            location = {
                "spot":
                    float(spot),

                "time_to_maturity":
                    float(tau),

                "boundary_spot":
                    float(
                        boundary_spot
                    ),

                "distance_to_boundary":
                    float(distance),

                "absolute_error":
                    error,
            }

            if (
                distance
                <= band_width
            ):
                near_errors.append(
                    error
                )

                near_locations.append(
                    location
                )
            else:
                away_errors.append(
                    error
                )

                away_locations.append(
                    location
                )

    def summarize(
        values,
    ):
        if not values:
            return {
                "count": 0,
                "mae": None,
                "rmse": None,
                "max_absolute_error":
                    None,
            }

        array = np.asarray(
            values,
            dtype=float,
        )

        return {
            "count":
                int(
                    array.size
                ),

            "mae":
                float(
                    np.mean(
                        array
                    )
                ),

            "rmse":
                float(
                    np.sqrt(
                        np.mean(
                            array**2
                        )
                    )
                ),

            "max_absolute_error":
                float(
                    np.max(
                        array
                    )
                ),
        }

    near_summary = summarize(
        near_errors
    )

    away_summary = summarize(
        away_errors
    )

    ratio = None

    if (
        near_summary["mae"]
        is not None
        and away_summary["mae"]
        is not None
        and away_summary["mae"]
        > 0
    ):
        ratio = float(
            near_summary["mae"]
            / away_summary["mae"]
        )

    worst_near = (
        max(
            near_locations,
            key=lambda item:
                item[
                    "absolute_error"
                ],
        )
        if near_locations
        else None
    )

    worst_away = (
        max(
            away_locations,
            key=lambda item:
                item[
                    "absolute_error"
                ],
        )
        if away_locations
        else None
    )

    return {
        "band_width":
            float(
                band_width
            ),

        "near_boundary":
            near_summary,

        "away_from_boundary":
            away_summary,

        "near_to_away_mae_ratio":
            ratio,

        "worst_near_boundary":
            worst_near,

        "worst_away_from_boundary":
            worst_away,
    }

def _boundary_distance_profile(
    *,
    spot_grid: np.ndarray,
    tau_grid: np.ndarray,
    absolute_error_surface: np.ndarray,
    exercise_boundary: List[
        Dict[str, Optional[float]]
    ],
    strike: float,
):
    """
    Measure PINN approximation error as a
    function of distance from the estimated
    American exercise boundary.

    Distance is normalized by strike:

        d_norm = |S - S*(tau)| / K

    This makes the diagnostic more comparable
    across option parameterizations.
    """

    if strike <= 0:
        raise ValueError(
            "Strike must be positive."
        )

    boundary_by_tau = {
        float(
            point[
                "time_to_maturity"
            ]
        ):
        float(
            point["spot"]
        )

        for point
        in exercise_boundary

        if point["spot"]
        is not None
    }


    # ---------------------------------------------------------
    # Normalized distance bands.
    #
    # Example for K = 100:
    #
    #   0.000 - 0.025  -> 0 - 2.5 spot units
    #   0.025 - 0.050  -> 2.5 - 5
    #   0.050 - 0.100  -> 5 - 10
    #   0.100 - 0.200  -> 10 - 20
    #   0.200+         -> > 20
    # ---------------------------------------------------------

    spot_differences = np.diff(
    np.asarray(
        spot_grid,
        dtype=float,
    )
)

    if spot_differences.size == 0:
        raise ValueError(
            "spot_grid must contain "
            "at least two points."
        )

    grid_spacing = float(
        np.median(
            spot_differences
        )
    )

    if grid_spacing <= 0:
        raise ValueError(
            "spot_grid must be "
            "strictly increasing."
        )


    bin_edges = [
        0.0,
        1.0,
        2.0,
        4.0,
        8.0,
        np.inf,
    ]

    bin_labels = [
        "<1 ΔS",
        "1-2 ΔS",
        "2-4 ΔS",
        "4-8 ΔS",
        "8+ ΔS",
    ]


    observations = []


    for tau_index, tau in enumerate(
        tau_grid
    ):
        if not boundary_by_tau:
            continue

        nearest_tau = min(
            boundary_by_tau.keys(),
            key=lambda value: abs(
                value
                - float(tau)
            ),
        )

        boundary_spot = (
            boundary_by_tau[
                nearest_tau
            ]
        )


        for spot_index, spot in enumerate(
            spot_grid
        ):
            absolute_error = float(
                absolute_error_surface[
                    tau_index,
                    spot_index,
                ]
            )

            absolute_distance = abs(
                float(spot)
                - boundary_spot
            )

            normalized_distance = (
                absolute_distance
                / strike
            )

            grid_distance = (
                absolute_distance
                / grid_spacing
            )


            observations.append(
                {
                    "spot":
                        float(spot),

                    "time_to_maturity":
                        float(tau),

                    "boundary_spot":
                        float(
                            boundary_spot
                        ),

                    "absolute_distance":
                        float(
                            absolute_distance
                        ),

                    "normalized_distance":
                        float(
                            normalized_distance
                        ),

                    "grid_distance":
                        float(
                            grid_distance
                        ),

                    "absolute_error":
                        absolute_error,
                }
            )


    bins = []


    for index, label in enumerate(
        bin_labels
    ):
        lower = (
            bin_edges[index]
        )

        upper = (
            bin_edges[
                index + 1
            ]
        )


        if np.isinf(
            upper
        ):
            selected = [
                item
                for item
                in observations
                if (
                    item[
                        "grid_distance"
                    ]
                    >= lower
                )
            ]
        else:
            selected = [
                item
                for item
                in observations
                if (
                    item[
                        "grid_distance"
                    ]
                    >= lower
                    and
                    item[
                        "grid_distance"
                    ]
                    < upper
                )
            ]


        errors = np.asarray(
            [
                item[
                    "absolute_error"
                ]
                for item
                in selected
            ],
            dtype=float,
        )


        if errors.size == 0:
            bins.append(
                {
                    "label":
                        label,

                    "lower_distance":
                        float(lower),

                    "upper_distance":
                        (
                            None
                            if np.isinf(
                                upper
                            )
                            else float(
                                upper
                            )
                        ),

                    "count":
                        0,

                    "mae":
                        None,

                    "rmse":
                        None,

                    "median_absolute_error":
                        None,

                    "p90_absolute_error":
                        None,

                    "max_absolute_error":
                        None,
                }
            )

            continue


        bins.append(
            {
                "label":
                    label,

                "lower_distance":
                    float(lower),

                "upper_distance":
                    (
                        None
                        if np.isinf(
                            upper
                        )
                        else float(
                            upper
                        )
                    ),

                "count":
                    int(
                        errors.size
                    ),

                "mae":
                    float(
                        np.mean(
                            errors
                        )
                    ),

                "rmse":
                    float(
                        np.sqrt(
                            np.mean(
                                errors**2
                            )
                        )
                    ),

                "median_absolute_error":
                    float(
                        np.median(
                            errors
                        )
                    ),

                "p90_absolute_error":
                    float(
                        np.quantile(
                            errors,
                            0.90,
                        )
                    ),

                "max_absolute_error":
                    float(
                        np.max(
                            errors
                        )
                    ),
            }
        )


    if observations:
        distances = np.asarray(
            [
                item[
                    "grid_distance"
                ]
                for item
                in observations
            ],
            dtype=float,
        )

        errors = np.asarray(
            [
                item[
                    "absolute_error"
                ]
                for item
                in observations
            ],
            dtype=float,
        )


        if (
            distances.size > 1
            and np.std(
                distances
            ) > 0
            and np.std(
                errors
            ) > 0
        ):
            correlation = float(
                np.corrcoef(
                    distances,
                    errors,
                )[0, 1]
            )
        else:
            correlation = None

    else:
        correlation = None


    return {
        "distance_definition":
            "abs(S - S_star) / delta_S",

        "grid_spacing":
            grid_spacing,

        "strike":
            float(strike),

        "observation_count":
            len(
                observations
            ),

        "distance_error_correlation":
            correlation,

        "bins":
            bins,
    }

def build_american_surface_atlas(
    *,
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    dividend_yield: float = 0.0,
    s_max: Optional[float] = None,
    space_steps: int = 80,
    time_steps: int = 80,
    crr_steps: int = 150,
    crr_surface_points: int = 31,
    boundary_tolerance: float = 1e-4,
) -> AmericanSurfaceAtlas:

    inputs = OptionInputs(
        spot=spot,
        strike=strike,
        rate=rate,
        volatility=volatility,
        maturity=maturity,
        dividend_yield=dividend_yield,
    )

    cn = projected_crank_nicolson_put(
        inputs,
        s_max=s_max,
        space_steps=space_steps,
        time_steps=time_steps,
    )

    # ---------------------------------------------------------
    # CN solver stores calendar time:
    #
    #     t = 0 ... T
    #
    # For cross-model comparison we use remaining maturity:
    #
    #     tau = T - t
    #
    # and order it from 0 ... T.
    # ---------------------------------------------------------

    full_spot_grid = cn.spot_grid

    cn_tau_grid = (
        maturity - cn.time_grid
    )[::-1]

    cn_surface_full = (
        cn.value_grid[::-1, :]
    )

    # ---------------------------------------------------------
    # Use a smaller common comparison mesh for CRR.
    #
    # Calling a tree solver at every point of an 81 x 81
    # surface would be unnecessarily expensive.
    # ---------------------------------------------------------

    comparison_spot_grid = np.linspace(
        float(full_spot_grid[0]),
        float(full_spot_grid[-1]),
        crr_surface_points,
    )

    comparison_tau_grid = np.linspace(
        0.0,
        maturity,
        crr_surface_points,
    )

    # Interpolate CN onto the same grid used by CRR.
    cn_spot_interpolated = np.vstack(
        [
            np.interp(
                comparison_spot_grid,
                full_spot_grid,
                row,
            )
            for row in cn_surface_full
        ]
    )

    cn_comparison_surface = np.vstack(
        [
            np.interp(
                comparison_tau_grid,
                cn_tau_grid,
                cn_spot_interpolated[:, j],
            )
            for j in range(
                len(comparison_spot_grid)
            )
        ]
    ).T

    crr_surface = _build_crr_surface(
        spot_grid=
            comparison_spot_grid,
        time_to_maturity_grid=
            comparison_tau_grid,
        strike=strike,
        rate=rate,
        volatility=volatility,
        dividend_yield=
            dividend_yield,
        crr_steps=crr_steps,
    )

    payoff = np.maximum(
        strike - comparison_spot_grid,
        0.0,
    )

    payoff_surface = np.repeat(
        payoff[np.newaxis, :],
        len(comparison_tau_grid),
        axis=0,
    )

    exercise_gap = (
        cn_comparison_surface
        - payoff_surface
    )

    exercise_boundary = (
            _estimate_exercise_boundary(
                spot_grid=
                    comparison_spot_grid,
                time_to_maturity_grid=
                    comparison_tau_grid,
                value_grid=
                    cn_comparison_surface,
                strike=strike,
                tolerance=
                    boundary_tolerance,
            )
        )

    crr_signed_error = (
        crr_surface
        - cn_comparison_surface
    )

    crr_absolute_error = np.abs(
        crr_signed_error
    )

    pinn_artifact = _load_pinn_surface(
    target_spot_grid=
        comparison_spot_grid,

    target_tau_grid=
        comparison_tau_grid,

    strike=strike,
    rate=rate,
    volatility=volatility,
    maturity=maturity,

    dividend_yield=
        dividend_yield,
)


    pinn_surface = None

    pinn_signed_error = None
    pinn_absolute_error = None

    pinn_available = False

    pinn_method = None
    pinn_final_loss = None
    pinn_training_seconds = None

    pinn_max_absolute_error = None
    pinn_rmse = None
    pinn_mae = None


    if pinn_artifact is not None:
        pinn_available = True

        pinn_surface = (
            pinn_artifact[
                "surface"
            ]
        )

        pinn_method = (
            pinn_artifact[
                "method"
            ]
        )

        pinn_final_loss = (
            pinn_artifact[
                "final_loss"
            ]
        )

        pinn_training_seconds = (
            pinn_artifact[
                "training_seconds"
            ]
        )

        pinn_signed_error = (
            pinn_surface
            - cn_comparison_surface
        )

        pinn_absolute_error = np.abs(
            pinn_signed_error
        )

        pinn_max_absolute_error = float(
            np.max(
                pinn_absolute_error
            )
        )

        pinn_rmse = float(
            np.sqrt(
                np.mean(
                    pinn_signed_error**2
                )
            )
        )

        pinn_mae = float(
            np.mean(
                pinn_absolute_error
            )
        )

    pinn_convergence_artifact = (
        _load_pinn_convergence(
            target_spot_grid=
                comparison_spot_grid,

            target_tau_grid=
                comparison_tau_grid,

            strike=strike,
            rate=rate,
            volatility=volatility,
            maturity=maturity,

            dividend_yield=
                dividend_yield,
        )
    )


    pinn_convergence_available = False

    pinn_convergence_epochs = []

    pinn_convergence_surfaces = {}

    pinn_convergence_signed_errors = {}

    pinn_convergence_absolute_errors = {}

    pinn_convergence_metrics = {}

    pinn_boundary_diagnostics = {}

    pinn_boundary_distance_profiles = {}

    pinn_improvement_surface = None


    if (
        pinn_convergence_artifact
        is not None
    ):
        pinn_convergence_available = True

        pinn_convergence_epochs = (
            pinn_convergence_artifact[
                "epochs"
            ]
        )

        for epoch in (
            pinn_convergence_epochs
        ):
            key = str(epoch)

            snapshot = (
                pinn_convergence_artifact[
                    "snapshots"
                ][key]
            )

            surface = snapshot[
                "surface"
            ]

            signed_error = (
                surface
                - cn_comparison_surface
            )

            absolute_error = np.abs(
                signed_error
            )

            mae = float(
                np.mean(
                    absolute_error
                )
            )

            rmse = float(
                np.sqrt(
                    np.mean(
                        signed_error**2
                    )
                )
            )

            max_absolute_error = float(
                np.max(
                    absolute_error
                )
            )

            pinn_convergence_surfaces[
                key
            ] = surface.tolist()

            pinn_convergence_signed_errors[
                key
            ] = signed_error.tolist()

            pinn_convergence_absolute_errors[
                key
            ] = absolute_error.tolist()

            pinn_convergence_metrics[
                key
            ] = {
                "mae":
                    mae,

                "rmse":
                    rmse,

                "max_absolute_error":
                    max_absolute_error,

                "training_loss":
                    snapshot[
                        "training_loss"
                    ],

                "elapsed_training_seconds":
                    snapshot[
                        "elapsed_training_seconds"
                    ],

                "inference_seconds":
                    snapshot[
                        "inference_seconds"
                    ],
            }

            pinn_boundary_diagnostics[
                key
            ] = (
                _boundary_error_diagnostics(
                    spot_grid=
                        comparison_spot_grid,

                    tau_grid=
                        comparison_tau_grid,

                    absolute_error_surface=
                        absolute_error,

                    exercise_boundary=
                        exercise_boundary,

                    strike=strike,
                )
            )

            pinn_boundary_distance_profiles[
                key
            ] = (
                _boundary_distance_profile(
                    spot_grid=
                        comparison_spot_grid,

                    tau_grid=
                        comparison_tau_grid,

                    absolute_error_surface=
                        absolute_error,

                    exercise_boundary=
                        exercise_boundary,

                    strike=strike,
                )
            )

        first_key = str(
            pinn_convergence_epochs[0]
        )

        last_key = str(
            pinn_convergence_epochs[-1]
        )

        first_absolute_error = np.asarray(
            pinn_convergence_absolute_errors[
                first_key
            ],
            dtype=float,
        )

        last_absolute_error = np.asarray(
            pinn_convergence_absolute_errors[
                last_key
            ],
            dtype=float,
        )

        pinn_improvement_surface = (
            first_absolute_error
            - last_absolute_error
        ).tolist()

    return AmericanSurfaceAtlas(
        spot_grid=[
            float(value)
            for value
            in comparison_spot_grid
        ],

        time_to_maturity_grid=[
            float(value)
            for value
            in comparison_tau_grid
        ],

        cn_surface=
            cn_comparison_surface.tolist(),

        crr_surface=
            crr_surface.tolist(),

        pinn_surface=(
            pinn_surface.tolist()
            if pinn_surface is not None
            else None
        ),

        pinn_signed_error_surface=(
            pinn_signed_error.tolist()
            if pinn_signed_error is not None
            else None
        ),

        pinn_absolute_error_surface=(
            pinn_absolute_error.tolist()
            if pinn_absolute_error is not None
            else None
        ),

        payoff_surface=
            payoff_surface.tolist(),

        exercise_gap_surface=
            exercise_gap.tolist(),

        crr_signed_error_surface=
            crr_signed_error.tolist(),

        crr_absolute_error_surface=
            crr_absolute_error.tolist(),

        exercise_boundary=
            exercise_boundary,

        min_price=float(
            min(
                np.min(
                    cn_comparison_surface
                ),
                np.min(
                    crr_surface
                ),
            )
        ),

        max_price=float(
            max(
                np.max(
                    cn_comparison_surface
                ),
                np.max(
                    crr_surface
                ),
            )
        ),

        max_exercise_gap=float(
            np.max(
                exercise_gap
            )
        ),

        max_crr_absolute_error=float(
            np.max(
                crr_absolute_error
            )
        ),

        pinn_available=
            pinn_available,

        pinn_method=
            pinn_method,

        pinn_final_loss=(
            float(pinn_final_loss)
            if pinn_final_loss is not None
            else None
        ),

        pinn_training_seconds=(
            float(
                pinn_training_seconds
            )
            if pinn_training_seconds
            is not None
            else None
        ),

        pinn_max_absolute_error=
            pinn_max_absolute_error,

        pinn_rmse=
            pinn_rmse,

        pinn_mae=
            pinn_mae,

        pinn_convergence_available=(
            pinn_convergence_available
        ),

        pinn_convergence_epochs=(
            pinn_convergence_epochs
        ),

        pinn_convergence_surfaces=(
            pinn_convergence_surfaces
        ),

        pinn_convergence_signed_errors=(
            pinn_convergence_signed_errors
        ),

        pinn_convergence_absolute_errors=(
            pinn_convergence_absolute_errors
        ),

        pinn_convergence_metrics=(
            pinn_convergence_metrics
        ),

        pinn_improvement_surface=(
            pinn_improvement_surface
        ),

        pinn_boundary_diagnostics=(
            pinn_boundary_diagnostics
                ),

        pinn_boundary_distance_profiles=(
            pinn_boundary_distance_profiles
        ),

        space_steps=space_steps,
        time_steps=time_steps,
        crr_steps=crr_steps,
    )