from time import perf_counter

import numpy as np
import torch

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.deeponet import (
    train_deeponet,
)

from app.models.deeponet_data import (
    generate_deeponet_dataset,
    normalize_branch,
    normalize_trunk,
)


def main():

    train_data = (
        generate_deeponet_dataset(
            n_parameter_sets=500,
            n_spot_points=40,
            seed=42,
        )
    )

    result = train_deeponet(
        train_data.branch_inputs,
        train_data.trunk_inputs,
        train_data.targets,
        epochs=2000,
    )

    rng = np.random.default_rng(
        123
    )

    n_queries = 10_000

    raw_branch = np.column_stack(
        [
            rng.uniform(
                80,
                120,
                n_queries,
            ),
            rng.uniform(
                0,
                0.08,
                n_queries,
            ),
            rng.uniform(
                0.10,
                0.50,
                n_queries,
            ),
            rng.uniform(
                0.25,
                2.0,
                n_queries,
            ),
            rng.uniform(
                0,
                0.04,
                n_queries,
            ),
        ]
    ).astype(
        np.float32
    )

    raw_trunk = np.column_stack(
        [
            rng.uniform(
                50,
                150,
                n_queries,
            ),
            np.zeros(
                n_queries
            ),
        ]
    ).astype(
        np.float32
    )

    branch = normalize_branch(
        raw_branch
    )

    trunk = normalize_trunk(
        raw_trunk
    )

    branch_tensor = torch.tensor(
        branch,
        dtype=torch.float32,
    )

    trunk_tensor = torch.tensor(
        trunk,
        dtype=torch.float32,
    )

    result.model.eval()

    start = perf_counter()

    with torch.no_grad():
        deeponet_prices = (
            result.model(
                branch_tensor,
                trunk_tensor,
            )
            .numpy()
            .reshape(-1)
        )

    deeponet_runtime = (
        perf_counter() - start
    )

    start = perf_counter()

    analytical_prices = []

    for i in range(
        n_queries
    ):
        inputs = OptionInputs(
            spot=float(
                raw_trunk[i, 0]
            ),
            strike=float(
                raw_branch[i, 0]
            ),
            rate=float(
                raw_branch[i, 1]
            ),
            volatility=float(
                raw_branch[i, 2]
            ),
            maturity=float(
                raw_branch[i, 3]
            ),
            dividend_yield=float(
                raw_branch[i, 4]
            ),
        )

        analytical_prices.append(
            european_call(
                inputs
            )
        )

    bs_runtime = (
        perf_counter() - start
    )

    analytical_prices = (
        np.asarray(
            analytical_prices
        )
    )

    errors = np.abs(
        deeponet_prices
        - analytical_prices
    )

    print()
    print(
        "DeepONet inference benchmark"
    )

    print("-" * 55)

    print(
        f"Queries:        "
        f"{n_queries}"
    )

    print(
        f"DeepONet time:  "
        f"{deeponet_runtime:.6f} s"
    )

    print(
        f"BS time:        "
        f"{bs_runtime:.6f} s"
    )

    print(
        f"DeepONet MAE:   "
        f"{errors.mean():.6f}"
    )

    print(
        f"DeepONet max:   "
        f"{errors.max():.6f}"
    )

    print(
        f"Queries/sec:    "
        f"{n_queries / deeponet_runtime:.0f}"
    )


if __name__ == "__main__":
    main()