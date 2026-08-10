from time import perf_counter

import numpy as np
import torch

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.american_finite_difference import (
    projected_crank_nicolson_put,
)

from app.models.american_deeponet_data import (
    generate_american_deeponet_dataset,
    normalize_branch,
    normalize_trunk,
)

from app.models.deeponet import (
    train_deeponet,
)

from experiments.results_io import (
    save_result,
)


def mae(
    prediction: np.ndarray,
    target: np.ndarray,
) -> float:
    return float(
        np.mean(
            np.abs(
                prediction - target
            )
        )
    )


def rmse(
    prediction: np.ndarray,
    target: np.ndarray,
) -> float:
    return float(
        np.sqrt(
            np.mean(
                (
                    prediction
                    - target
                )
                ** 2
            )
        )
    )


def main():
    seed = 123
    rng = np.random.default_rng(
        seed
    )

    print()
    print(
        "American DeepONet "
        "Amortised Inference Benchmark"
    )
    print("=" * 72)

    # --------------------------------------------------
    # Training dataset
    # --------------------------------------------------

    print()
    print(
        "Generating training data..."
    )

    start = perf_counter()

    train_data = (
        generate_american_deeponet_dataset(
            n_parameter_sets=200,
            n_spot_points=40,
            space_steps=160,
            time_steps=160,
            seed=42,
        )
    )

    data_generation_time = (
        perf_counter()
        - start
    )

    print(
        f"Training-data generation: "
        f"{data_generation_time:.3f} s"
    )

    # --------------------------------------------------
    # Train DeepONet
    # --------------------------------------------------

    print()
    print(
        "Training DeepONet..."
    )

    start = perf_counter()

    training_result = train_deeponet(
        train_data.branch_inputs,
        train_data.trunk_inputs,
        train_data.targets,
        epochs=2500,
        batch_size=1024,
        learning_rate=1e-3,
        seed=42,
    )

    training_time = (
        perf_counter()
        - start
    )

    model = training_result.model
    model.eval()

    print()
    print(
        f"DeepONet training time: "
        f"{training_time:.3f} s"
    )

    print(
        f"Final training loss: "
        f"{training_result.final_loss:.6e}"
    )

    # --------------------------------------------------
    # Random out-of-sample queries
    # --------------------------------------------------

    n_queries = 1000

    strikes = rng.uniform(
        80.0,
        120.0,
        n_queries,
    )

    rates = rng.uniform(
        0.0,
        0.08,
        n_queries,
    )

    volatilities = rng.uniform(
        0.10,
        0.50,
        n_queries,
    )

    maturities = rng.uniform(
        0.25,
        2.0,
        n_queries,
    )

    dividend_yields = rng.uniform(
        0.0,
        0.04,
        n_queries,
    )

    spots = rng.uniform(
        50.0,
        150.0,
        n_queries,
    )

    raw_branch = np.column_stack(
        [
            strikes,
            rates,
            volatilities,
            maturities,
            dividend_yields,
        ]
    ).astype(
        np.float32
    )

    raw_trunk = np.column_stack(
        [
            spots,
            np.zeros(
                n_queries,
                dtype=np.float32,
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

    # --------------------------------------------------
    # DeepONet inference
    # --------------------------------------------------

    # Warm-up pass
    with torch.no_grad():
        _ = model(
            branch_tensor[:10],
            trunk_tensor[:10],
        )

    start = perf_counter()

    with torch.no_grad():
        deeponet_prices = (
            model(
                branch_tensor,
                trunk_tensor,
            )
            .cpu()
            .numpy()
            .reshape(-1)
        )

    deeponet_runtime = (
        perf_counter()
        - start
    )

    # --------------------------------------------------
    # Projected CN benchmark
    # --------------------------------------------------

    print()
    print(
        "Running Projected CN "
        "benchmark queries..."
    )

    classical_prices = np.empty(
        n_queries,
        dtype=float,
    )

    start = perf_counter()

    for i in range(
        n_queries
    ):
        inputs = OptionInputs(
            spot=float(
                spots[i]
            ),
            strike=float(
                strikes[i]
            ),
            rate=float(
                rates[i]
            ),
            volatility=float(
                volatilities[i]
            ),
            maturity=float(
                maturities[i]
            ),
            dividend_yield=float(
                dividend_yields[i]
            ),
        )

        result = (
            projected_crank_nicolson_put(
                inputs,
                space_steps=160,
                time_steps=160,
            )
        )

        classical_prices[i] = (
            result.price
        )

        if (
            (i + 1) % 100 == 0
            or i
            == n_queries - 1
        ):
            print(
                f"Completed "
                f"{i + 1}/"
                f"{n_queries}"
            )

    classical_runtime = (
        perf_counter()
        - start
    )

    # --------------------------------------------------
    # Error metrics
    # --------------------------------------------------

    absolute_errors = np.abs(
        deeponet_prices
        - classical_prices
    )

    test_mae = mae(
        deeponet_prices,
        classical_prices,
    )

    test_rmse = rmse(
        deeponet_prices,
        classical_prices,
    )

    median_error = float(
        np.median(
            absolute_errors
        )
    )

    percentile_95 = float(
        np.quantile(
            absolute_errors,
            0.95,
        )
    )

    max_err = float(
        np.max(
            absolute_errors
        )
    )

    epsilon = 1e-3

    relative_errors = (
        absolute_errors
        / (
            np.abs(
                classical_prices
            )
            + epsilon
        )
    )

    median_relative_error = float(
        np.median(
            relative_errors
        )
    )

    # --------------------------------------------------
    # Speed metrics
    # --------------------------------------------------

    deeponet_per_query = (
        deeponet_runtime
        / n_queries
    )

    classical_per_query = (
        classical_runtime
        / n_queries
    )

    speedup = (
        classical_runtime
        / deeponet_runtime
        if deeponet_runtime > 0
        else float("inf")
    )

    queries_per_second = (
        n_queries
        / deeponet_runtime
    )

    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    print()
    print(
        "Online Inference Benchmark"
    )
    print("-" * 82)

    print(
        f"{'Method':<24}"
        f"{'Total Time':>16}"
        f"{'Mean / Query':>18}"
        f"{'Queries / sec':>18}"
    )

    print("-" * 82)

    print(
        f"{'Projected CN':<24}"
        f"{classical_runtime:>16.6f}"
        f"{classical_per_query:>18.8f}"
        f"{n_queries / classical_runtime:>18.2f}"
    )

    print(
        f"{'American DeepONet':<24}"
        f"{deeponet_runtime:>16.6f}"
        f"{deeponet_per_query:>18.8f}"
        f"{queries_per_second:>18.2f}"
    )

    print()
    print(
        f"Online speedup: "
        f"{speedup:.2f}x"
    )

    print()
    print(
        "Accuracy vs Projected CN"
    )
    print("-" * 55)

    print(
        f"MAE:                   "
        f"{test_mae:.6f}"
    )

    print(
        f"RMSE:                  "
        f"{test_rmse:.6f}"
    )

    print(
        f"Median absolute error: "
        f"{median_error:.6f}"
    )

    print(
        f"95th percentile error: "
        f"{percentile_95:.6f}"
    )

    print(
        f"Maximum error:         "
        f"{max_err:.6f}"
    )

    print(
        f"Median relative error: "
        f"{100.0 * median_relative_error:.3f}%"
    )

    print()
    print(
        "Offline cost"
    )
    print("-" * 55)

    print(
        f"Training-data generation: "
        f"{data_generation_time:.3f} s"
    )

    print(
        f"DeepONet training:         "
        f"{training_time:.3f} s"
    )

    total_offline_cost = (
        data_generation_time
        + training_time
    )

    print(
        f"Total offline cost:        "
        f"{total_offline_cost:.3f} s"
    )

    # --------------------------------------------------
    # Approximate break-even query count
    # --------------------------------------------------

    saved_time_per_query = (
        classical_per_query
        - deeponet_per_query
    )

    if saved_time_per_query > 0:

        break_even_queries = (
            total_offline_cost
            / saved_time_per_query
        )

        print()
        print(
            "Amortisation estimate"
        )
        print("-" * 55)

        print(
            "Approximate break-even "
            "query count: "
            f"{break_even_queries:.0f}"
        )

        print(
            "Interpretation: after "
            "roughly this many repeated "
            "pricing queries, the offline "
            "DeepONet cost is recovered "
            "through faster inference."
        )

    else:

        print()
        print(
            "DeepONet does not achieve "
            "an online runtime advantage "
            "under this benchmark."
        )

    # --------------------------------------------------
    # Selected prediction examples
    # --------------------------------------------------

    print()
    print(
        "Selected out-of-sample queries"
    )
    print("-" * 96)

    print(
        f"{'Spot':>8}"
        f"{'Strike':>10}"
        f"{'Vol':>10}"
        f"{'T':>8}"
        f"{'CN':>12}"
        f"{'DeepONet':>12}"
        f"{'Abs Error':>14}"
    )

    print("-" * 96)

    sample_indices = [
        0,
        n_queries // 4,
        n_queries // 2,
        3 * n_queries // 4,
        n_queries - 1,
    ]

    for i in sample_indices:

        print(
            f"{spots[i]:>8.2f}"
            f"{strikes[i]:>10.2f}"
            f"{volatilities[i]:>10.4f}"
            f"{maturities[i]:>8.3f}"
            f"{classical_prices[i]:>12.6f}"
            f"{deeponet_prices[i]:>12.6f}"
            f"{absolute_errors[i]:>14.6f}"
        )

    if saved_time_per_query > 0:
        break_even_queries = (
            total_offline_cost
            / saved_time_per_query
        )
    else:
        break_even_queries = None


    benchmark_payload = {
    "experiment":
        "american_deeponet_benchmark",

    "queries":
        n_queries,

    "offline": {
        "data_generation_seconds":
            data_generation_time,

        "training_seconds":
            training_time,

        "total_seconds":
            total_offline_cost,
    },

    "online": {
        "projected_cn": {
            "total_seconds":
                classical_runtime,

            "seconds_per_query":
                classical_per_query,

            "queries_per_second":
                (
                    n_queries
                    / classical_runtime
                ),
        },

        "deeponet": {
            "total_seconds":
                deeponet_runtime,

            "seconds_per_query":
                deeponet_per_query,

            "queries_per_second":
                queries_per_second,
        },

        "speedup":
            speedup,

        "break_even_queries":
            (
                float(
                    break_even_queries
                )
                if (
                    break_even_queries
                    is not None
                )
                else None
            ),
    },

    "accuracy": {
        "mae":
            test_mae,

        "rmse":
            test_rmse,

        "median_absolute_error":
            median_error,

        "p95_absolute_error":
            percentile_95,

        "max_error":
            max_err,

        "median_relative_error":
            median_relative_error,
    },
}

    save_result(
        "american_deeponet_benchmark.json",
        benchmark_payload,
    )


if __name__ == "__main__":
    main()