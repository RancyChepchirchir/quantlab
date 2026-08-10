from dataclasses import dataclass
from math import exp
from typing import Optional

import numpy as np

from app.models.black_scholes import (
    OptionInputs,
)


@dataclass(frozen=True)
class AmericanFiniteDifferenceResult:
    price: float
    spot_grid: np.ndarray
    value_grid: np.ndarray
    time_grid: np.ndarray


def projected_crank_nicolson_put(
    inputs: OptionInputs,
    s_max: Optional[float] = None,
    space_steps: int = 200,
    time_steps: int = 200,
) -> AmericanFiniteDifferenceResult:

    if space_steps < 3:
        raise ValueError(
            "space_steps must be >= 3."
        )

    if time_steps < 1:
        raise ValueError(
            "time_steps must be >= 1."
        )

    s0 = inputs.spot
    k = inputs.strike
    r = inputs.rate
    q = inputs.dividend_yield
    sigma = inputs.volatility
    maturity = inputs.maturity

    if s_max is None:
        s_max = max(
            4.0 * k,
            4.0 * s0,
        )

    ds = s_max / space_steps
    dt = maturity / time_steps

    spot_grid = np.linspace(
        0.0,
        s_max,
        space_steps + 1,
    )

    time_grid = np.linspace(
        0.0,
        maturity,
        time_steps + 1,
    )

    values = np.zeros(
        (
            time_steps + 1,
            space_steps + 1,
        )
    )

    payoff = np.maximum(
        k - spot_grid,
        0.0,
    )

    values[-1, :] = payoff

    interior_count = (
        space_steps - 1
    )

    lower = np.zeros(
        interior_count
    )
    diag = np.zeros(
        interior_count
    )
    upper = np.zeros(
        interior_count
    )

    lower_rhs = np.zeros(
        interior_count
    )
    diag_rhs = np.zeros(
        interior_count
    )
    upper_rhs = np.zeros(
        interior_count
    )

    for idx in range(
        1,
        space_steps,
    ):
        i = idx

        a = (
            0.25
            * dt
            * (
                sigma**2
                * i**2
                - (r - q) * i
            )
        )

        b = (
            -0.5
            * dt
            * (
                sigma**2
                * i**2
                + r
            )
        )

        c = (
            0.25
            * dt
            * (
                sigma**2
                * i**2
                + (r - q) * i
            )
        )

        j = idx - 1

        lower[j] = -a
        diag[j] = 1.0 - b
        upper[j] = -c

        lower_rhs[j] = a
        diag_rhs[j] = 1.0 + b
        upper_rhs[j] = c

    lhs = np.zeros(
        (
            interior_count,
            interior_count,
        )
    )

    rhs_matrix = np.zeros(
        (
            interior_count,
            interior_count,
        )
    )

    for j in range(
        interior_count
    ):
        lhs[j, j] = diag[j]
        rhs_matrix[j, j] = (
            diag_rhs[j]
        )

        if j > 0:
            lhs[j, j - 1] = (
                lower[j]
            )

            rhs_matrix[
                j,
                j - 1,
            ] = lower_rhs[j]

        if j < (
            interior_count - 1
        ):
            lhs[j, j + 1] = (
                upper[j]
            )

            rhs_matrix[
                j,
                j + 1,
            ] = upper_rhs[j]

    for n in range(
        time_steps - 1,
        -1,
        -1,
    ):
        tau = (
            maturity
            - time_grid[n]
        )

        # American put boundaries
        lower_boundary = k

        upper_boundary = 0.0

        values[
            n,
            0,
        ] = lower_boundary

        values[
            n,
            -1,
        ] = upper_boundary

        rhs = (
            rhs_matrix
            @ values[
                n + 1,
                1:-1,
            ]
        )

        rhs[0] += (
            lower_rhs[0]
            * values[
                n + 1,
                0,
            ]
            + lower[0]
            * lower_boundary
        )

        rhs[-1] += (
            upper_rhs[-1]
            * values[
                n + 1,
                -1,
            ]
            + upper[-1]
            * upper_boundary
        )

        continuation = (
            np.linalg.solve(
                lhs,
                rhs,
            )
        )

        intrinsic = payoff[
            1:-1
        ]

        values[
            n,
            1:-1,
        ] = np.maximum(
            continuation,
            intrinsic,
        )

    price = float(
        np.interp(
            s0,
            spot_grid,
            values[0, :],
        )
    )

    return (
        AmericanFiniteDifferenceResult(
            price=price,
            spot_grid=spot_grid,
            value_grid=values,
            time_grid=time_grid,
        )
    )