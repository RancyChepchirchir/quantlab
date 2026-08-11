from dataclasses import dataclass
from math import exp

import numpy as np

from app.models.black_scholes import (
    OptionInputs,
)

from typing import Optional


@dataclass(frozen=True)
class FiniteDifferenceResult:
    price: float
    spot_grid: np.ndarray
    value_grid: np.ndarray
    time_grid: np.ndarray

def solve_tridiagonal(
    lower: np.ndarray,
    diag: np.ndarray,
    upper: np.ndarray,
    rhs: np.ndarray,
) -> np.ndarray:
    """
    Solve a tridiagonal linear system using
    the Thomas algorithm.

    lower[i] is the sub-diagonal entry for row i.
    diag[i] is the diagonal entry.
    upper[i] is the super-diagonal entry.
    """

    n = len(diag)

    c_prime = np.zeros(
        n,
        dtype=float,
    )

    d_prime = np.zeros(
        n,
        dtype=float,
    )

    c_prime[0] = (
        upper[0]
        / diag[0]
    )

    d_prime[0] = (
        rhs[0]
        / diag[0]
    )

    for i in range(
        1,
        n,
    ):
        denominator = (
            diag[i]
            - lower[i]
            * c_prime[i - 1]
        )

        if i < n - 1:
            c_prime[i] = (
                upper[i]
                / denominator
            )

        d_prime[i] = (
            rhs[i]
            - lower[i]
            * d_prime[i - 1]
        ) / denominator

    solution = np.zeros(
        n,
        dtype=float,
    )

    solution[-1] = (
        d_prime[-1]
    )

    for i in range(
        n - 2,
        -1,
        -1,
    ):
        solution[i] = (
            d_prime[i]
            - c_prime[i]
            * solution[i + 1]
        )

    return solution

def crank_nicolson_price(
    inputs: OptionInputs,
    option_type: str = "call",
    s_max: Optional[float] = None,
    space_steps: int = 200,
    time_steps: int = 200,
) -> FiniteDifferenceResult:

    if option_type not in {
        "call",
        "put",
    }:
        raise ValueError(
            "option_type must be "
            "'call' or 'put'."
        )

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

    ds = (
        s_max
        / space_steps
    )

    dt = (
        maturity
        / time_steps
    )

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

    # Terminal payoff
    if option_type == "call":
        values[-1, :] = np.maximum(
            spot_grid - k,
            0.0,
        )
    else:
        values[-1, :] = np.maximum(
            k - spot_grid,
            0.0,
        )

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

    for n in range(
        time_steps - 1,
        -1,
        -1,
    ):
        tau = (
            maturity
            - time_grid[n]
        )

        # Boundary conditions
        if option_type == "call":
            lower_boundary = 0.0

            upper_boundary = (
                s_max
                * exp(-q * tau)
                - k
                * exp(-r * tau)
            )
        else:
            lower_boundary = (
                k
                * exp(-r * tau)
            )

            upper_boundary = 0.0

        values[
            n,
            0,
        ] = lower_boundary

        values[
            n,
            -1,
        ] = upper_boundary

        next_values = (
            values[
                n + 1,
                1:-1,
            ]
        )

        rhs = (
            diag_rhs
            * next_values
        )

        if interior_count > 1:
            rhs[1:] += (
                lower_rhs[1:]
                * next_values[:-1]
            )

            rhs[:-1] += (
                upper_rhs[:-1]
                * next_values[1:]
            )

        # Boundary contributions
        if interior_count > 0:
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

        values[
            n,
            1:-1,
        ] = solve_tridiagonal(
            lower,
            diag,
            upper,
            rhs,
        )

    price = float(
        np.interp(
            s0,
            spot_grid,
            values[0, :],
        )
    )

    return FiniteDifferenceResult(
        price=price,
        spot_grid=spot_grid,
        value_grid=values,
        time_grid=time_grid,
    )