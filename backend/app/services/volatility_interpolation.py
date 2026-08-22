from dataclasses import dataclass
from typing import List

import numpy as np

from app.services.volatility_surface import (
    CalibratedQuote,
)


@dataclass(frozen=True)
class SurfaceGridPoint:
    strike: float
    maturity: float
    implied_volatility: float


@dataclass(frozen=True)
class SurfaceGrid:
    strikes: List[float]
    maturities: List[float]
    points: List[
        SurfaceGridPoint
    ]

    observed_strike_count: int
    observed_maturity_count: int
    is_two_dimensional: bool


def interpolate_volatility_surface(
    quotes: List[
        CalibratedQuote
    ],
    strike_points: int = 25,
    maturity_points: int = 15,
) -> SurfaceGrid:
    """
    Interpolate calibrated implied-volatility
    observations onto a regular strike/maturity
    grid using inverse-distance weighting.

    A genuine 2-D surface requires observations
    at more than one strike AND more than one
    maturity.

    If only one maturity is available, the
    function returns a one-row smile grid rather
    than fabricating a maturity dimension.
    """

    if not quotes:
        raise ValueError(
            "At least one calibrated quote "
            "is required."
        )

    if strike_points < 2:
        raise ValueError(
            "strike_points must be >= 2."
        )

    if maturity_points < 2:
        raise ValueError(
            "maturity_points must be >= 2."
        )

    strikes = np.array(
        [
            quote.strike
            for quote
            in quotes
        ],
        dtype=float,
    )

    maturities = np.array(
        [
            quote.maturity
            for quote
            in quotes
        ],
        dtype=float,
    )

    ivs = np.array(
        [
            quote.implied_volatility
            for quote
            in quotes
        ],
        dtype=float,
    )

    unique_strikes = np.unique(
        strikes
    )

    unique_maturities = np.unique(
        np.round(
            maturities,
            10,
        )
    )

    observed_strike_count = len(
        unique_strikes
    )

    observed_maturity_count = len(
        unique_maturities
    )

    is_two_dimensional = (
        observed_strike_count >= 2
        and observed_maturity_count >= 2
    )

    # --------------------------------------------------
    # Strike grid
    # --------------------------------------------------

    if observed_strike_count == 1:
        strike_grid = np.array(
            [
                float(
                    unique_strikes[0]
                )
            ]
        )

    else:
        strike_grid = np.linspace(
            float(
                np.min(
                    strikes
                )
            ),
            float(
                np.max(
                    strikes
                )
            ),
            strike_points,
        )

    # --------------------------------------------------
    # Maturity grid
    #
    # Do NOT fabricate a maturity dimension if only
    # one expiry was observed.
    # --------------------------------------------------

    if observed_maturity_count == 1:
        maturity_grid = np.array(
            [
                float(
                    unique_maturities[0]
                )
            ]
        )

    else:
        maturity_grid = np.linspace(
            float(
                np.min(
                    maturities
                )
            ),
            float(
                np.max(
                    maturities
                )
            ),
            maturity_points,
        )

    # --------------------------------------------------
    # Normalisation scales
    # --------------------------------------------------

    strike_scale = max(
        float(
            np.ptp(
                strikes
            )
        ),
        1e-8,
    )

    maturity_scale = max(
        float(
            np.ptp(
                maturities
            )
        ),
        1e-8,
    )

    points: List[
        SurfaceGridPoint
    ] = []

    # --------------------------------------------------
    # Inverse-distance interpolation
    # --------------------------------------------------

    for maturity in (
        maturity_grid
    ):
        for strike in (
            strike_grid
        ):
            strike_distance = (
                (
                    strikes
                    - strike
                )
                / strike_scale
            )

            # If all observations have one maturity,
            # maturity contributes no distance.
            if (
                observed_maturity_count
                == 1
            ):
                maturity_distance = (
                    np.zeros_like(
                        maturities
                    )
                )

            else:
                maturity_distance = (
                    (
                        maturities
                        - maturity
                    )
                    / maturity_scale
                )

            squared_distance = (
                strike_distance
                ** 2
                + maturity_distance
                ** 2
            )

            exact_match = np.where(
                squared_distance
                < 1e-12
            )[0]

            if len(
                exact_match
            ) > 0:
                # There may be both call and put
                # observations at the same K,T.
                # Average their calibrated IVs.
                interpolated_iv = float(
                    np.mean(
                        ivs[
                            exact_match
                        ]
                    )
                )

            else:
                weights = (
                    1.0
                    / (
                        squared_distance
                        + 1e-8
                    )
                )

                interpolated_iv = float(
                    np.sum(
                        weights
                        * ivs
                    )
                    / np.sum(
                        weights
                    )
                )

            points.append(
                SurfaceGridPoint(
                    strike=
                        float(
                            strike
                        ),

                    maturity=
                        float(
                            maturity
                        ),

                    implied_volatility=
                        interpolated_iv,
                )
            )

    return SurfaceGrid(
        strikes=[
            float(
                value
            )
            for value
            in strike_grid
        ],

        maturities=[
            float(
                value
            )
            for value
            in maturity_grid
        ],

        points=
            points,

        observed_strike_count=
            observed_strike_count,

        observed_maturity_count=
            observed_maturity_count,

        is_two_dimensional=
            is_two_dimensional,
    )