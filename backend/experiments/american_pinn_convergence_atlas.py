import json
from pathlib import Path
from time import perf_counter

import numpy as np
import torch

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.american_pinn_v2 import (
    AmericanPutPINNV2,
    fischer_burmeister,
    value_and_operator,
)


RESULTS_DIR = (
    Path(__file__).resolve().parent
    / "results"
)

OUTPUT_PATH = (
    RESULTS_DIR
    / "american_pinn_convergence_atlas.json"
)


CHECKPOINT_EPOCHS = [
    500,
    1000,
    2000,
    4000,
]


SURFACE_POINTS = 31


def evaluate_surface(
    model: AmericanPutPINNV2,
    *,
    spot_grid: np.ndarray,
    tau_grid: np.ndarray,
    maturity: float,
) -> np.ndarray:
    """
    Evaluate the PINN on the Surface Atlas
    coordinate system:

        (S, tau)

    where tau is remaining maturity.

    The network itself uses calendar time t:

        t = T - tau.
    """

    spot_mesh, tau_mesh = np.meshgrid(
        spot_grid,
        tau_grid,
    )

    time_mesh = (
        maturity
        - tau_mesh
    )

    spot_tensor = torch.tensor(
        spot_mesh.reshape(-1, 1),
        dtype=torch.float32,
    )

    time_tensor = torch.tensor(
        time_mesh.reshape(-1, 1),
        dtype=torch.float32,
    )

    model.eval()

    with torch.no_grad():
        prediction = model(
            spot_tensor,
            time_tensor,
        )

    return (
        prediction
        .cpu()
        .numpy()
        .reshape(
            len(tau_grid),
            len(spot_grid),
        )
    )


def snapshot_diagnostics(
    surface: np.ndarray,
    *,
    strike: float,
    spot_grid: np.ndarray,
) -> dict:
    """
    Diagnostics available without choosing a
    separate numerical reference.

    At tau = 0, the American option must equal
    the terminal payoff.
    """

    payoff = np.maximum(
        strike - spot_grid,
        0.0,
    )

    payoff_surface = np.repeat(
        payoff[np.newaxis, :],
        surface.shape[0],
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

    return {
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
    }


def main():
    torch.manual_seed(42)

    base = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    s_max = 250.0

    n_interior = 3000
    n_terminal = 1000
    n_boundary = 1000

    learning_rate = 1e-3

    lambda_comp = 10.0
    lambda_terminal = 5.0
    lambda_boundary = 5.0

    max_epochs = max(
        CHECKPOINT_EPOCHS
    )

    spot_grid = np.linspace(
        0.0,
        s_max,
        SURFACE_POINTS,
    )

    tau_grid = np.linspace(
        0.0,
        base.maturity,
        SURFACE_POINTS,
    )

    model = AmericanPutPINNV2(
        s_max=s_max,
        maturity=base.maturity,
        hidden_width=64,
        hidden_layers=4,
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate,
    )

    losses = []

    snapshots = {}

    print()
    print("=" * 78)
    print(
        "QuantLab — PINN V2 Convergence Surface Atlas"
    )
    print("=" * 78)
    print()

    print(
        "Checkpoint epochs:",
        CHECKPOINT_EPOCHS,
    )

    print(
        "Surface:",
        f"{SURFACE_POINTS} x "
        f"{SURFACE_POINTS}",
    )

    print()

    experiment_start = perf_counter()

    for epoch_index in range(
        max_epochs
    ):
        model.train()

        # -----------------------------------------
        # Interior collocation points
        # -----------------------------------------

        spot = (
            torch.rand(
                n_interior,
                1,
            )
            * s_max
        )

        time = (
            torch.rand(
                n_interior,
                1,
            )
            * base.maturity
        )

        value, operator = (
            value_and_operator(
                model,
                spot,
                time,
                base,
            )
        )

        payoff = torch.relu(
            base.strike
            - spot
        )

        gap = (
            value
            - payoff
        )

        continuation_residual = (
            -operator
        )

        complementarity = (
            fischer_burmeister(
                gap,
                continuation_residual,
            )
        )

        comp_loss = torch.mean(
            complementarity**2
        )

        # -----------------------------------------
        # Terminal condition
        # -----------------------------------------

        terminal_spot = (
            torch.rand(
                n_terminal,
                1,
            )
            * s_max
        )

        terminal_time = torch.full(
            (
                n_terminal,
                1,
            ),
            base.maturity,
        )

        terminal_prediction = model(
            terminal_spot,
            terminal_time,
        )

        terminal_target = torch.relu(
            base.strike
            - terminal_spot
        )

        terminal_loss = torch.mean(
            (
                terminal_prediction
                - terminal_target
            )
            ** 2
        )

        # -----------------------------------------
        # Spatial boundaries
        # -----------------------------------------

        boundary_time = (
            torch.rand(
                n_boundary,
                1,
            )
            * base.maturity
        )

        lower_spot = torch.zeros(
            n_boundary,
            1,
        )

        upper_spot = torch.full(
            (
                n_boundary,
                1,
            ),
            s_max,
        )

        lower_prediction = model(
            lower_spot,
            boundary_time,
        )

        upper_prediction = model(
            upper_spot,
            boundary_time,
        )

        lower_target = torch.full(
            (
                n_boundary,
                1,
            ),
            base.strike,
        )

        upper_target = torch.zeros(
            n_boundary,
            1,
        )

        boundary_loss = (
            torch.mean(
                (
                    lower_prediction
                    - lower_target
                )
                ** 2
            )
            +
            torch.mean(
                (
                    upper_prediction
                    - upper_target
                )
                ** 2
            )
        )

        # -----------------------------------------
        # Total objective
        # -----------------------------------------

        loss = (
            lambda_comp
            * comp_loss
            +
            lambda_terminal
            * terminal_loss
            +
            lambda_boundary
            * boundary_loss
        )

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

        loss_value = float(
            loss.detach()
        )

        losses.append(
            loss_value
        )

        completed_epoch = (
            epoch_index + 1
        )

        if (
            completed_epoch % 200 == 0
            or completed_epoch == 1
        ):
            print(
                f"Epoch "
                f"{completed_epoch:5d}"
                f" | Total "
                f"{loss_value:.6e}"
                f" | Comp "
                f"{float(comp_loss.detach()):.6e}"
                f" | TC "
                f"{float(terminal_loss.detach()):.6e}"
                f" | BC "
                f"{float(boundary_loss.detach()):.6e}"
            )

        # -----------------------------------------
        # Research checkpoint
        # -----------------------------------------

        if (
            completed_epoch
            in CHECKPOINT_EPOCHS
        ):
            checkpoint_start = (
                perf_counter()
            )

            surface = evaluate_surface(
                model,
                spot_grid=spot_grid,
                tau_grid=tau_grid,
                maturity=base.maturity,
            )

            inference_seconds = (
                perf_counter()
                - checkpoint_start
            )

            diagnostics = (
                snapshot_diagnostics(
                    surface,
                    strike=base.strike,
                    spot_grid=spot_grid,
                )
            )

            snapshots[
                str(completed_epoch)
            ] = {
                "epoch":
                    completed_epoch,

                "training_loss":
                    loss_value,

                "elapsed_training_seconds":
                    float(
                        perf_counter()
                        - experiment_start
                    ),

                "inference_seconds":
                    float(
                        inference_seconds
                    ),

                "surface": [
                    [
                        float(value)
                        for value in row
                    ]
                    for row in surface
                ],

                "diagnostics":
                    diagnostics,
            }

            print()
            print(
                "Captured checkpoint "
                f"{completed_epoch}"
            )

            print(
                "  terminal MAE: "
                f"{diagnostics['terminal_mae']:.6e}"
            )

            print(
                "  max obstacle violation: "
                f"{diagnostics['max_obstacle_violation']:.6e}"
            )

            print()

    total_training_seconds = (
        perf_counter()
        - experiment_start
    )

    payload = {
        "experiment":
            "american_pinn_convergence_atlas",

        "method":
            "pinn_v2_fischer_burmeister",

        "option_type":
            "put",

        "coordinate_system": {
            "surface_time":
                "time_to_maturity",

            "training_time":
                "calendar_time",

            "conversion":
                "t = T - tau",
        },

        "input": {
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

            "s_max":
                s_max,
        },

        "architecture": {
            "input_dimension":
                2,

            "hidden_width":
                64,

            "hidden_layers":
                4,

            "activation":
                "tanh",

            "output_dimension":
                1,
        },

        "training": {
            "max_epochs":
                max_epochs,

            "checkpoint_epochs":
                CHECKPOINT_EPOCHS,

            "n_interior":
                n_interior,

            "n_terminal":
                n_terminal,

            "n_boundary":
                n_boundary,

            "learning_rate":
                learning_rate,

            "lambda_comp":
                lambda_comp,

            "lambda_terminal":
                lambda_terminal,

            "lambda_boundary":
                lambda_boundary,

            "seed":
                42,

            "total_training_seconds":
                float(
                    total_training_seconds
                ),
        },

        "grid": {
            "spot": [
                float(value)
                for value in spot_grid
            ],

            "time_to_maturity": [
                float(value)
                for value in tau_grid
            ],
        },

        "loss_history": [
            float(value)
            for value in losses
        ],

        "snapshots":
            snapshots,
    }

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            payload,
            handle,
            indent=2,
        )

    print()
    print("=" * 78)
    print(
        "Experiment complete"
    )
    print("=" * 78)

    print(
        "Training seconds:",
        f"{total_training_seconds:.2f}",
    )

    print(
        "Snapshots:",
        ", ".join(
            snapshots.keys()
        ),
    )

    print(
        "Saved:",
        OUTPUT_PATH,
    )

    print()


if __name__ == "__main__":
    main()