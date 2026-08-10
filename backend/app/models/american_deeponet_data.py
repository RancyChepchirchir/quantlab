from dataclasses import dataclass

import numpy as np

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.american_finite_difference import (
    projected_crank_nicolson_put,
)


@dataclass(frozen=True)
class AmericanDeepONetDataset:
    branch_inputs: np.ndarray
    trunk_inputs: np.ndarray
    targets: np.ndarray


def normalize_branch(
    branch_inputs: np.ndarray,
) -> np.ndarray:
    result = branch_inputs.copy()

    # strike: 80–120
    result[:, 0] = (
        result[:, 0] - 100.0
    ) / 20.0

    # rate: 0–0.08
    result[:, 1] = (
        result[:, 1] - 0.04
    ) / 0.04

    # volatility: 0.10–0.50
    result[:, 2] = (
        result[:, 2] - 0.30
    ) / 0.20

    # maturity: 0.25–2.0
    result[:, 3] = (
        result[:, 3] - 1.125
    ) / 0.875

    # dividend yield: 0–0.04
    result[:, 4] = (
        result[:, 4] - 0.02
    ) / 0.02

    return result


def normalize_trunk(
    trunk_inputs: np.ndarray,
) -> np.ndarray:
    result = trunk_inputs.copy()

    # spot: 50–150
    result[:, 0] = (
        result[:, 0] - 100.0
    ) / 50.0

    # time: 0–2
    result[:, 1] = (
        result[:, 1] - 1.0
    )

    return result


def generate_american_deeponet_dataset(
    n_parameter_sets: int = 200,
    n_spot_points: int = 40,
    space_steps: int = 160,
    time_steps: int = 160,
    seed: int = 42,
) -> AmericanDeepONetDataset:

    rng = np.random.default_rng(seed)

    branch_rows = []
    trunk_rows = []
    target_rows = []

    for index in range(
        n_parameter_sets
    ):
        strike = rng.uniform(
            80.0,
            120.0,
        )

        rate = rng.uniform(
            0.0,
            0.08,
        )

        volatility = rng.uniform(
            0.10,
            0.50,
        )

        maturity = rng.uniform(
            0.25,
            2.0,
        )

        dividend_yield = rng.uniform(
            0.0,
            0.04,
        )

        base = OptionInputs(
            spot=100.0,
            strike=float(strike),
            rate=float(rate),
            volatility=float(
                volatility
            ),
            maturity=float(
                maturity
            ),
            dividend_yield=float(
                dividend_yield
            ),
        )

        result = (
            projected_crank_nicolson_put(
                base,
                space_steps=space_steps,
                time_steps=time_steps,
            )
        )

        spots = np.linspace(
            50.0,
            150.0,
            n_spot_points,
        )

        prices = np.interp(
            spots,
            result.spot_grid,
            result.value_grid[0],
        )

        for spot, price in zip(
            spots,
            prices,
        ):
            branch_rows.append(
                [
                    strike,
                    rate,
                    volatility,
                    maturity,
                    dividend_yield,
                ]
            )

            trunk_rows.append(
                [
                    spot,
                    0.0,
                ]
            )

            target_rows.append(
                [price]
            )

        if (
            index % 20 == 0
            or index
            == n_parameter_sets - 1
        ):
            print(
                "Generated "
                f"{index + 1}/"
                f"{n_parameter_sets}"
            )

    branch_array = np.asarray(
        branch_rows,
        dtype=np.float32,
    )

    trunk_array = np.asarray(
        trunk_rows,
        dtype=np.float32,
    )

    targets = np.asarray(
        target_rows,
        dtype=np.float32,
    )

    return AmericanDeepONetDataset(
        branch_inputs=
            normalize_branch(
                branch_array
            ),
        trunk_inputs=
            normalize_trunk(
                trunk_array
            ),
        targets=targets,
    )