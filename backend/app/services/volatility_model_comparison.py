from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from app.services.svi import (
    SVISurfaceResult,
    svi_total_variance,
)

from app.services.ssvi import (
    SSVISurfaceResult,
    forward_log_moneyness,
    ssvi_total_variance,
)

from app.services.volatility_surface import (
    CalibratedQuote,
)


@dataclass(frozen=True)
class ModelErrorMetrics:
    rmse: float
    mae: float
    max_absolute_error: float
    observation_count: int


@dataclass(frozen=True)
class MaturityModelComparison:
    maturity: float
    observation_count: int

    svi: ModelErrorMetrics
    ssvi: ModelErrorMetrics

    better_rmse_model: str
    better_mae_model: str


@dataclass(frozen=True)
class VolatilityModelComparison:
    svi: ModelErrorMetrics
    ssvi: ModelErrorMetrics

    better_rmse_model: str
    better_mae_model: str

    maturity_comparisons: List[
        MaturityModelComparison
    ]


def _metrics(
    observed: np.ndarray,
    fitted: np.ndarray,
) -> ModelErrorMetrics:
    if (
        observed.shape
        != fitted.shape
    ):
        raise ValueError(
            "Observed and fitted arrays "
            "must have the same shape."
        )

    if observed.size == 0:
        raise ValueError(
            "At least one observation "
            "is required."
        )

    errors = (
        fitted
        - observed
    )

    absolute_errors = (
        np.abs(
            errors
        )
    )

    return ModelErrorMetrics(
        rmse=float(
            np.sqrt(
                np.mean(
                    errors ** 2
                )
            )
        ),

        mae=float(
            np.mean(
                absolute_errors
            )
        ),

        max_absolute_error=float(
            np.max(
                absolute_errors
            )
        ),

        observation_count=int(
            observed.size
        ),
    )


def _better_model(
    svi_value: float,
    ssvi_value: float,
    tolerance: float = 1e-12,
) -> str:
    difference = (
        svi_value
        - ssvi_value
    )

    if (
        abs(
            difference
        )
        <= tolerance
    ):
        return "tie"

    if (
        svi_value
        < ssvi_value
    ):
        return "svi"

    return "ssvi"


def _collapse_quotes(
    quotes: List[
        CalibratedQuote
    ],
) -> Dict[
    float,
    Dict[
        float,
        float,
    ],
]:
    """
    Collapse duplicate observations at the
    same maturity and strike by averaging
    their calibrated Black-Scholes IV.

    This means a matched call/put pair at
    the same strike counts as one surface
    observation.
    """

    grouped: Dict[
        float,
        Dict[
            float,
            List[float],
        ],
    ] = {}

    for quote in quotes:
        maturity = round(
            float(
                quote.maturity
            ),
            8,
        )

        strike = float(
            quote.strike
        )

        grouped.setdefault(
            maturity,
            {},
        )

        grouped[
            maturity
        ].setdefault(
            strike,
            [],
        )

        grouped[
            maturity
        ][
            strike
        ].append(
            float(
                quote
                .implied_volatility
            )
        )

    result: Dict[
        float,
        Dict[
            float,
            float,
        ],
    ] = {}

    for (
        maturity,
        strike_map,
    ) in grouped.items():
        result[
            maturity
        ] = {}

        for (
            strike,
            values,
        ) in strike_map.items():
            result[
                maturity
            ][
                strike
            ] = float(
                np.mean(
                    values
                )
            )

    return result


def _raw_svi_predictions(
    observed: Dict[
        float,
        Dict[
            float,
            float,
        ],
    ],
    svi_surface: SVISurfaceResult,
    spot: float,
) -> Dict[
    float,
    Dict[
        float,
        float,
    ],
]:
    """
    Evaluate each fitted raw-SVI smile at
    the ORIGINAL observed strikes.

    This is preferable to extracting fitted
    values from smile.points because those
    points may represent a generated plotting
    grid rather than the original calibration
    observations.
    """

    if spot <= 0.0:
        raise ValueError(
            "Spot must be positive."
        )

    smile_map = {
        round(
            float(
                smile
                .parameters
                .maturity
            ),
            8,
        ):
            smile
        for smile
        in svi_surface.smiles
    }

    result: Dict[
        float,
        Dict[
            float,
            float,
        ],
    ] = {}

    for (
        maturity,
        strike_map,
    ) in observed.items():
        smile = (
            smile_map.get(
                maturity
            )
        )

        if smile is None:
            continue

        parameters = (
            smile.parameters
        )

        strikes = np.asarray(
            list(
                strike_map.keys()
            ),
            dtype=float,
        )

        # Raw SVI in this project uses
        # log spot-moneyness.
        log_moneyness = np.log(
            strikes
            / float(
                spot
            )
        )

        total_variance = (
            svi_total_variance(
                log_moneyness,
                parameters.a,
                parameters.b,
                parameters.rho,
                parameters.m,
                parameters.sigma,
            )
        )

        result[
            maturity
        ] = {}

        for (
            strike,
            variance,
        ) in zip(
            strikes,
            total_variance,
        ):
            variance_value = max(
                float(
                    variance
                ),
                1e-16,
            )

            fitted_iv = float(
                np.sqrt(
                    variance_value
                    / maturity
                )
            )

            result[
                maturity
            ][
                float(
                    strike
                )
            ] = fitted_iv

    return result


def _ssvi_predictions(
    observed: Dict[
        float,
        Dict[
            float,
            float,
        ],
    ],
    ssvi_surface: SSVISurfaceResult,
) -> Dict[
    float,
    Dict[
        float,
        float,
    ],
]:
    """
    Evaluate SSVI at exactly the same
    observed maturity/strike coordinates.
    """

    slice_map = {
        round(
            float(
                item.maturity
            ),
            8,
        ):
            item
        for item
        in ssvi_surface.atm_slices
    }

    result: Dict[
        float,
        Dict[
            float,
            float,
        ],
    ] = {}

    eta = float(
        ssvi_surface
        .parameters
        .eta
    )

    rho = float(
        ssvi_surface
        .parameters
        .rho
    )

    gamma = float(
        ssvi_surface
        .parameters
        .gamma
    )

    for (
        maturity,
        strike_map,
    ) in observed.items():
        atm_slice = (
            slice_map.get(
                maturity
            )
        )

        if atm_slice is None:
            continue

        strikes = list(
            strike_map.keys()
        )

        log_moneyness = np.asarray(
            [
                forward_log_moneyness(
                    strike=float(
                        strike
                    ),
                    forward=float(
                        atm_slice
                        .forward
                    ),
                )
                for strike
                in strikes
            ],
            dtype=float,
        )

        theta = np.full(
            len(
                strikes
            ),
            float(
                atm_slice.theta
            ),
            dtype=float,
        )

        total_variance = (
            ssvi_total_variance(
                log_moneyness=(
                    log_moneyness
                ),
                theta=theta,
                eta=eta,
                rho=rho,
                gamma=gamma,
            )
        )

        result[
            maturity
        ] = {}

        for (
            strike,
            variance,
        ) in zip(
            strikes,
            total_variance,
        ):
            variance_value = max(
                float(
                    variance
                ),
                1e-16,
            )

            fitted_iv = float(
                np.sqrt(
                    variance_value
                    / maturity
                )
            )

            result[
                maturity
            ][
                float(
                    strike
                )
            ] = fitted_iv

    return result


def compare_svi_and_ssvi(
    quotes: List[
        CalibratedQuote
    ],
    svi_surface: SVISurfaceResult,
    ssvi_surface: SSVISurfaceResult,
    spot: float = 100.0,
) -> VolatilityModelComparison:
    """
    Compare raw SVI and SSVI against exactly
    the same observed IV coordinates.

    Metrics are expressed in decimal IV units.

    Example:
        RMSE = 0.01

    means approximately one volatility
    percentage point.
    """

    observed = (
        _collapse_quotes(
            quotes
        )
    )

    if (
        len(
            observed
        )
        == 0
    ):
        raise ValueError(
            "No observations were available "
            "for SVI/SSVI comparison."
        )

    svi_predictions = (
        _raw_svi_predictions(
            observed=observed,
            svi_surface=(
                svi_surface
            ),
            spot=spot,
        )
    )

    ssvi_predictions = (
        _ssvi_predictions(
            observed=observed,
            ssvi_surface=(
                ssvi_surface
            ),
        )
    )

    global_observed: List[
        float
    ] = []

    global_svi: List[
        float
    ] = []

    global_ssvi: List[
        float
    ] = []

    maturity_results: List[
        MaturityModelComparison
    ] = []

    for maturity in sorted(
        observed.keys()
    ):
        if (
            maturity
            not in svi_predictions
        ):
            continue

        if (
            maturity
            not in ssvi_predictions
        ):
            continue

        maturity_observed: List[
            float
        ] = []

        maturity_svi: List[
            float
        ] = []

        maturity_ssvi: List[
            float
        ] = []

        for strike in sorted(
            observed[
                maturity
            ].keys()
        ):
            if (
                strike
                not in svi_predictions[
                    maturity
                ]
            ):
                continue

            if (
                strike
                not in ssvi_predictions[
                    maturity
                ]
            ):
                continue

            observed_iv = float(
                observed[
                    maturity
                ][
                    strike
                ]
            )

            svi_iv = float(
                svi_predictions[
                    maturity
                ][
                    strike
                ]
            )

            ssvi_iv = float(
                ssvi_predictions[
                    maturity
                ][
                    strike
                ]
            )

            maturity_observed.append(
                observed_iv
            )

            maturity_svi.append(
                svi_iv
            )

            maturity_ssvi.append(
                ssvi_iv
            )

            global_observed.append(
                observed_iv
            )

            global_svi.append(
                svi_iv
            )

            global_ssvi.append(
                ssvi_iv
            )

        if (
            len(
                maturity_observed
            )
            == 0
        ):
            continue

        observed_array = (
            np.asarray(
                maturity_observed,
                dtype=float,
            )
        )

        svi_array = (
            np.asarray(
                maturity_svi,
                dtype=float,
            )
        )

        ssvi_array = (
            np.asarray(
                maturity_ssvi,
                dtype=float,
            )
        )

        svi_metrics = (
            _metrics(
                observed_array,
                svi_array,
            )
        )

        ssvi_metrics = (
            _metrics(
                observed_array,
                ssvi_array,
            )
        )

        maturity_results.append(
            MaturityModelComparison(
                maturity=(
                    float(
                        maturity
                    )
                ),

                observation_count=(
                    len(
                        maturity_observed
                    )
                ),

                svi=svi_metrics,

                ssvi=ssvi_metrics,

                better_rmse_model=(
                    _better_model(
                        svi_metrics.rmse,
                        ssvi_metrics.rmse,
                    )
                ),

                better_mae_model=(
                    _better_model(
                        svi_metrics.mae,
                        ssvi_metrics.mae,
                    )
                ),
            )
        )

    if (
        len(
            global_observed
        )
        == 0
    ):
        raise ValueError(
            "No common observations "
            "were available for SVI/SSVI "
            "model comparison."
        )

    observed_array = (
        np.asarray(
            global_observed,
            dtype=float,
        )
    )

    svi_array = (
        np.asarray(
            global_svi,
            dtype=float,
        )
    )

    ssvi_array = (
        np.asarray(
            global_ssvi,
            dtype=float,
        )
    )

    svi_metrics = (
        _metrics(
            observed_array,
            svi_array,
        )
    )

    ssvi_metrics = (
        _metrics(
            observed_array,
            ssvi_array,
        )
    )

    return VolatilityModelComparison(
        svi=svi_metrics,

        ssvi=ssvi_metrics,

        better_rmse_model=(
            _better_model(
                svi_metrics.rmse,
                ssvi_metrics.rmse,
            )
        ),

        better_mae_model=(
            _better_model(
                svi_metrics.mae,
                ssvi_metrics.mae,
            )
        ),

        maturity_comparisons=(
            maturity_results
        ),
    )