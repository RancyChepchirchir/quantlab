import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import torch

from app.models.black_scholes import (
    OptionInputs,
)
from app.models.american_pinn_v2 import (
    train_american_put_pinn_v2,
)


RESULTS_DIR = (
    Path(__file__).resolve().parent
    / "results"
)

DEFAULT_OUTPUT = (
    RESULTS_DIR
    / "american_pinn_v2_surface.json"
)


def evaluate_surface(
    model,
    spot_grid: np.ndarray,
    tau_grid: np.ndarray,
    maturity: float,
) -> np.ndarray:
    """
    Evaluate PINN on a common (spot, tau) mesh.

    The PINN itself was trained using calendar time t:

        t = 0       valuation date
        t = T       expiry

    The Surface Atlas uses remaining maturity:

        tau = T - t

    therefore:

        t = T - tau.
    """

    spot_mesh, tau_mesh = np.meshgrid(
        spot_grid,
        tau_grid,
    )

    calendar_time_mesh = (
        maturity - tau_mesh
    )

    spot_tensor = torch.tensor(
        spot_mesh.reshape(-1, 1),
        dtype=torch.float32,
    )

    time_tensor = torch.tensor(
        calendar_time_mesh.reshape(-1, 1),
        dtype=torch.float32,
    )

    model.eval()

    with torch.no_grad():
        values = model(
            spot_tensor,
            time_tensor,
        )

    return (
        values
        .detach()
        .cpu()
        .numpy()
        .reshape(
            len(tau_grid),
            len(spot_grid),
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Train American PINN V2 once and "
            "export an inference surface for "
            "QuantLab Surface Atlas."
        )
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=4000,
    )

    parser.add_argument(
        "--surface-points",
        type=int,
        default=31,
    )

    parser.add_argument(
        "--spot-min",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--spot-max",
        type=float,
        default=250.0,
    )

    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
    )

    args = parser.parse_args()

    base = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    print()
    print("=" * 74)
    print(
        "QuantLab — American PINN V2 Surface Export"
    )
    print("=" * 74)
    print()

    print(
        f"Training epochs: {args.epochs}"
    )

    print(
        "Surface grid: "
        f"{args.surface_points} x "
        f"{args.surface_points}"
    )

    print()

    training_start = perf_counter()

    training_result = (
        train_american_put_pinn_v2(
            base,
            epochs=args.epochs,
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

    training_seconds = (
        perf_counter()
        - training_start
    )

    print()
    print(
        "Training complete in "
        f"{training_seconds:.2f}s"
    )

    spot_grid = np.linspace(
        args.spot_min,
        args.spot_max,
        args.surface_points,
    )

    tau_grid = np.linspace(
        0.0,
        base.maturity,
        args.surface_points,
    )

    inference_start = perf_counter()

    surface = evaluate_surface(
        training_result.model,
        spot_grid,
        tau_grid,
        base.maturity,
    )

    inference_seconds = (
        perf_counter()
        - inference_start
    )

    payoff = np.maximum(
        base.strike
        - spot_grid,
        0.0,
    )

    payoff_surface = np.repeat(
        payoff[np.newaxis, :],
        len(tau_grid),
        axis=0,
    )

    obstacle_violation = np.maximum(
        payoff_surface - surface,
        0.0,
    )

    terminal_error = np.abs(
        surface[0, :]
        - payoff
    )

    payload = {
        "artifact": (
            "american_pinn_v2_surface"
        ),

        "method": (
            "pinn_v2_fischer_burmeister"
        ),

        "option_type": "put",

        "coordinate_system": {
            "surface_time":
                "time_to_maturity",

            "training_time":
                "calendar_time",

            "conversion":
                "t = T - tau",
        },

        "input": {
            "spot": base.spot,
            "strike": base.strike,
            "rate": base.rate,
            "volatility":
                base.volatility,
            "maturity":
                base.maturity,
            "dividend_yield":
                base.dividend_yield,
        },

        "training": {
            "epochs":
                args.epochs,

            "n_interior":
                3000,

            "n_terminal":
                1000,

            "n_boundary":
                1000,

            "learning_rate":
                1e-3,

            "lambda_comp":
                10.0,

            "lambda_terminal":
                5.0,

            "lambda_boundary":
                5.0,

            "seed":
                42,

            "final_loss":
                float(
                    training_result
                    .final_loss
                ),

            "training_seconds":
                float(
                    training_seconds
                ),

            "inference_seconds":
                float(
                    inference_seconds
                ),
        },

        "grid": {
            "spot": [
                float(x)
                for x in spot_grid
            ],

            "time_to_maturity": [
                float(x)
                for x in tau_grid
            ],
        },

        "surface": [
            [
                float(value)
                for value in row
            ]
            for row in surface
        ],

        "diagnostics": {
            "min_value":
                float(
                    np.min(surface)
                ),

            "max_value":
                float(
                    np.max(surface)
                ),

            "max_obstacle_violation":
                float(
                    np.max(
                        obstacle_violation
                    )
                ),

            "mean_obstacle_violation":
                float(
                    np.mean(
                        obstacle_violation
                    )
                ),

            "terminal_mae":
                float(
                    np.mean(
                        terminal_error
                    )
                ),

            "terminal_max_error":
                float(
                    np.max(
                        terminal_error
                    )
                ),
        },
    }

    output_path = Path(
        args.output
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            payload,
            handle,
            indent=2,
        )

    print()
    print(
        "PINN Surface Diagnostics"
    )
    print("-" * 74)

    print(
        "Final training loss:       "
        f"{payload['training']['final_loss']:.6e}"
    )

    print(
        "Maximum obstacle violation:"
        f" "
        f"{payload['diagnostics']['max_obstacle_violation']:.6e}"
    )

    print(
        "Terminal MAE:              "
        f"{payload['diagnostics']['terminal_mae']:.6e}"
    )

    print(
        "Terminal max error:        "
        f"{payload['diagnostics']['terminal_max_error']:.6e}"
    )

    print()
    print(
        f"Saved: {output_path}"
    )
    print()


if __name__ == "__main__":
    main()