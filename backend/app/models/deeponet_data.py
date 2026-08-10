from dataclasses import dataclass

import numpy as np

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)


@dataclass(frozen=True)
class DeepONetDataset:
    branch_inputs: np.ndarray
    trunk_inputs: np.ndarray
    targets: np.ndarray


def generate_deeponet_dataset(
    n_parameter_sets: int = 500,
    n_spot_points: int = 50,
    seed: int = 42,
) -> DeepONetDataset:

    rng = np.random.default_rng(seed)

    branch_rows = []
    trunk_rows = []
    target_rows = []

    for _ in range(n_parameter_sets):

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

        spots = np.linspace(
            50.0,
            150.0,
            n_spot_points,
        )

        for spot in spots:

            inputs = OptionInputs(
                spot=float(spot),
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

            price = european_call(
                inputs
            )

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

        branch_array = np.asarray(
        branch_rows,
        dtype=np.float32,
    )

    trunk_array = np.asarray(
        trunk_rows,
        dtype=np.float32,
    )

    target_array = np.asarray(
        target_rows,
        dtype=np.float32,
    )

    return DeepONetDataset(
        branch_inputs=
            normalize_branch(
                branch_array
            ),
        trunk_inputs=
            normalize_trunk(
                trunk_array
            ),
        targets=target_array,
    )

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