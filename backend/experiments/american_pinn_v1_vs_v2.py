from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.binomial import (
    binomial_price,
)

from app.models.american_finite_difference import (
    projected_crank_nicolson_put,
)

from app.models.american_pinn import (
    train_american_put_pinn,
    american_pinn_price,
)

from app.models.american_pinn_v2 import (
    train_american_put_pinn_v2,
    american_pinn_v2_price,
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


def max_error(
    prediction: np.ndarray,
    target: np.ndarray,
) -> float:
    return float(
        np.max(
            np.abs(
                prediction - target
            )
        )
    )


def main():
    base = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    spots = np.linspace(
        50.0,
        150.0,
        101,
    )

    print()
    print(
        "American Put PINN V1 vs V2"
    )
    print("=" * 82)
    print()

    # --------------------------------------------------
    # CRR reference surface
    # --------------------------------------------------

    print(
        "Generating CRR benchmark..."
    )

    crr_prices = []

    start = perf_counter()

    for spot in spots:
        inputs = OptionInputs(
            spot=float(spot),
            strike=base.strike,
            rate=base.rate,
            volatility=base.volatility,
            maturity=base.maturity,
            dividend_yield=(
                base.dividend_yield
            ),
        )

        result = binomial_price(
            inputs,
            option_type="put",
            steps=2000,
            american=True,
        )

        crr_prices.append(
            result.price
        )

    crr_runtime = (
        perf_counter()
        - start
    )

    crr_prices = np.asarray(
        crr_prices,
        dtype=float,
    )

    # --------------------------------------------------
    # Projected Crank-Nicolson
    # --------------------------------------------------

    print(
        "Running Projected CN..."
    )

    start = perf_counter()

    cn_result = (
        projected_crank_nicolson_put(
            base,
            space_steps=300,
            time_steps=300,
        )
    )

    cn_runtime = (
        perf_counter()
        - start
    )

    cn_prices = np.asarray(
        [
            float(
                np.interp(
                    spot,
                    cn_result.spot_grid,
                    cn_result.value_grid[
                        0
                    ],
                )
            )
            for spot in spots
        ],
        dtype=float,
    )

    # --------------------------------------------------
    # PINN V1
    # --------------------------------------------------

    print()
    print(
        "Training American PINN V1..."
    )

    start = perf_counter()

    pinn_v1_result = (
        train_american_put_pinn(
            base,
            epochs=3000,
            n_interior=2500,
            n_terminal=750,
            n_boundary=750,
            learning_rate=1e-3,
            lambda_pde=1.0,
            lambda_obstacle=10.0,
            lambda_terminal=5.0,
            lambda_boundary=5.0,
            seed=42,
        )
    )

    pinn_v1_training_time = (
        perf_counter()
        - start
    )

    start = perf_counter()

    pinn_v1_prices = np.asarray(
        [
            american_pinn_price(
                pinn_v1_result.model,
                spot=float(spot),
                time=0.0,
            )
            for spot in spots
        ],
        dtype=float,
    )

    pinn_v1_inference_time = (
        perf_counter()
        - start
    )

    # --------------------------------------------------
    # PINN V2
    # --------------------------------------------------

    print()
    print(
        "Training American PINN V2..."
    )

    start = perf_counter()

    pinn_v2_result = (
        train_american_put_pinn_v2(
            base,
            epochs=4000,
            n_interior=3000,
            n_terminal=1000,
            n_boundary=1000,
            learning_rate=1e-3,
            lambda_comp=10.0,
            lambda_terminal=5.0,
            lambda_boundary=5.0,
            seed=42,
        )
    )

    pinn_v2_training_time = (
        perf_counter()
        - start
    )

    start = perf_counter()

    pinn_v2_prices = np.asarray(
        [
            american_pinn_v2_price(
                pinn_v2_result.model,
                spot=float(spot),
                time=0.0,
            )
            for spot in spots
        ],
        dtype=float,
    )

    pinn_v2_inference_time = (
        perf_counter()
        - start
    )

    # --------------------------------------------------
    # Error metrics
    # --------------------------------------------------

    cn_mae = mae(
        cn_prices,
        crr_prices,
    )

    cn_rmse = rmse(
        cn_prices,
        crr_prices,
    )

    cn_max = max_error(
        cn_prices,
        crr_prices,
    )

    pinn_v1_mae = mae(
        pinn_v1_prices,
        crr_prices,
    )

    pinn_v1_rmse = rmse(
        pinn_v1_prices,
        crr_prices,
    )

    pinn_v1_max = max_error(
        pinn_v1_prices,
        crr_prices,
    )

    pinn_v2_mae = mae(
        pinn_v2_prices,
        crr_prices,
    )

    pinn_v2_rmse = rmse(
        pinn_v2_prices,
        crr_prices,
    )

    pinn_v2_max = max_error(
        pinn_v2_prices,
        crr_prices,
    )

    atm_index = int(
        np.argmin(
            np.abs(
                spots - base.spot
            )
        )
    )

    cn_atm_error = abs(
        cn_prices[atm_index]
        - crr_prices[atm_index]
    )

    pinn_v1_atm_error = abs(
        pinn_v1_prices[
            atm_index
        ]
        - crr_prices[
            atm_index
        ]
    )

    pinn_v2_atm_error = abs(
        pinn_v2_prices[
            atm_index
        ]
        - crr_prices[
            atm_index
        ]
    )

    result_payload = {
    "experiment": (
        "american_pinn_v1_vs_v2"
    ),

    "problem": {
        "instrument":
            "american_put",

        "benchmark":
            "crr",

        "spot":
            base.spot,

        "strike":
            base.strike,

        "rate":
            base.rate,

        "volatility":
            base.volatility,

        "maturity":
            base.maturity,

        "dividend_yield":
            base.dividend_yield,

        "evaluation_spot_min":
            float(
                spots.min()
            ),

        "evaluation_spot_max":
            float(
                spots.max()
            ),

        "evaluation_points":
            len(spots),
    },

    "methods": {
        "crr": {
            "role":
                "benchmark",

            "mae":
                0.0,

            "rmse":
                0.0,

            "max_error":
                0.0,

            "atm_error":
                0.0,

            "runtime_seconds":
                crr_runtime,

            "atm_price":
                float(
                    crr_prices[
                        atm_index
                    ]
                ),
        },

        "projected_cn": {
            "role":
                "classical_solver",

            "mae":
                cn_mae,

            "rmse":
                cn_rmse,

            "max_error":
                cn_max,

            "atm_error":
                cn_atm_error,

            "runtime_seconds":
                cn_runtime,

            "atm_price":
                float(
                    cn_prices[
                        atm_index
                    ]
                ),
        },

        "pinn_v1": {
            "role":
                "scientific_ml",

            "formulation":
                "obstacle_penalty",

            "mae":
                pinn_v1_mae,

            "rmse":
                pinn_v1_rmse,

            "max_error":
                pinn_v1_max,

            "atm_error":
                pinn_v1_atm_error,

            "training_seconds":
                pinn_v1_training_time,

            "inference_seconds":
                pinn_v1_inference_time,

            "final_loss":
                float(
                    pinn_v1_result
                    .final_loss
                ),

            "atm_price":
                float(
                    pinn_v1_prices[
                        atm_index
                    ]
                ),
        },

        "pinn_v2": {
            "role":
                "scientific_ml",

            "formulation":
                "fischer_burmeister",

            "mae":
                pinn_v2_mae,

            "rmse":
                pinn_v2_rmse,

            "max_error":
                pinn_v2_max,

            "atm_error":
                pinn_v2_atm_error,

            "training_seconds":
                pinn_v2_training_time,

            "inference_seconds":
                pinn_v2_inference_time,

            "final_loss":
                float(
                    pinn_v2_result
                    .final_loss
                ),

            "atm_price":
                float(
                    pinn_v2_prices[
                        atm_index
                    ]
                ),
        },
    },

    "artifacts": {
        "solution_plot":
            "experiments/"
            "american_pinn_v1_vs_v2_solution.png",

        "error_plot":
            "experiments/"
            "american_pinn_v1_vs_v2_error.png",

        "training_plot":
            "experiments/"
            "american_pinn_v1_vs_v2_training.png",
        },
    }

    save_result(
        "american_pinn_v1_vs_v2.json",
        result_payload,
)

    # --------------------------------------------------
    # Summary table
    # --------------------------------------------------

    print()
    print(
        "American Put Solver Comparison"
    )
    print("-" * 112)

    print(
        f"{'Method':<22}"
        f"{'MAE':>12}"
        f"{'RMSE':>12}"
        f"{'Max Error':>14}"
        f"{'ATM Error':>14}"
        f"{'Train/Solve (s)':>18}"
        f"{'Infer (s)':>14}"
    )

    print("-" * 112)

    print(
        f"{'CRR benchmark':<22}"
        f"{0.0:>12.6f}"
        f"{0.0:>12.6f}"
        f"{0.0:>14.6f}"
        f"{0.0:>14.6f}"
        f"{crr_runtime:>18.6f}"
        f"{'-':>14}"
    )

    print(
        f"{'Projected CN':<22}"
        f"{cn_mae:>12.6f}"
        f"{cn_rmse:>12.6f}"
        f"{cn_max:>14.6f}"
        f"{cn_atm_error:>14.6f}"
        f"{cn_runtime:>18.6f}"
        f"{'-':>14}"
    )

    print(
        f"{'PINN V1':<22}"
        f"{pinn_v1_mae:>12.6f}"
        f"{pinn_v1_rmse:>12.6f}"
        f"{pinn_v1_max:>14.6f}"
        f"{pinn_v1_atm_error:>14.6f}"
        f"{pinn_v1_training_time:>18.6f}"
        f"{pinn_v1_inference_time:>14.6f}"
    )

    print(
        f"{'PINN V2':<22}"
        f"{pinn_v2_mae:>12.6f}"
        f"{pinn_v2_rmse:>12.6f}"
        f"{pinn_v2_max:>14.6f}"
        f"{pinn_v2_atm_error:>14.6f}"
        f"{pinn_v2_training_time:>18.6f}"
        f"{pinn_v2_inference_time:>14.6f}"
    )

    print()
    print(
        "ATM prices"
    )
    print("-" * 50)

    print(
        f"CRR:          "
        f"{crr_prices[atm_index]:.6f}"
    )

    print(
        f"Projected CN: "
        f"{cn_prices[atm_index]:.6f}"
    )

    print(
        f"PINN V1:      "
        f"{pinn_v1_prices[atm_index]:.6f}"
    )

    print(
        f"PINN V2:      "
        f"{pinn_v2_prices[atm_index]:.6f}"
    )

    print()
    print(
        "Final training losses"
    )
    print("-" * 50)

    print(
        f"PINN V1: "
        f"{pinn_v1_result.final_loss:.6e}"
    )

    print(
        f"PINN V2: "
        f"{pinn_v2_result.final_loss:.6e}"
    )

    # --------------------------------------------------
    # Solution plot
    # --------------------------------------------------

    plt.figure()

    plt.plot(
        spots,
        crr_prices,
        label="CRR benchmark",
    )

    plt.plot(
        spots,
        cn_prices,
        linestyle="--",
        label="Projected CN",
    )

    plt.plot(
        spots,
        pinn_v1_prices,
        linestyle=":",
        label="PINN V1",
    )

    plt.plot(
        spots,
        pinn_v2_prices,
        linestyle="-.",
        label="PINN V2",
    )

    plt.xlabel(
        "Spot price"
    )

    plt.ylabel(
        "American put value"
    )

    plt.title(
        "American Put Solver Comparison"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "american_pinn_v1_vs_v2_solution.png",
        dpi=200,
    )

    # --------------------------------------------------
    # Error profile
    # --------------------------------------------------

    plt.figure()

    plt.plot(
        spots,
        np.abs(
            cn_prices
            - crr_prices
        ),
        label="Projected CN",
    )

    plt.plot(
        spots,
        np.abs(
            pinn_v1_prices
            - crr_prices
        ),
        label="PINN V1",
    )

    plt.plot(
        spots,
        np.abs(
            pinn_v2_prices
            - crr_prices
        ),
        label="PINN V2",
    )

    plt.xlabel(
        "Spot price"
    )

    plt.ylabel(
        "Absolute error vs CRR"
    )

    plt.title(
        "American Put Error Profile"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "american_pinn_v1_vs_v2_error.png",
        dpi=200,
    )

    # --------------------------------------------------
    # Training loss comparison
    # --------------------------------------------------

    plt.figure()

    plt.semilogy(
        pinn_v1_result.losses,
        label="PINN V1",
    )

    plt.semilogy(
        pinn_v2_result.losses,
        label="PINN V2",
    )

    plt.xlabel(
        "Training epoch"
    )

    plt.ylabel(
        "Training loss"
    )

    plt.title(
        "American PINN Training Convergence"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "american_pinn_v1_vs_v2_training.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()