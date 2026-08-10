from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import torch

from app.models.american_deeponet_data import (
    generate_american_deeponet_dataset,
)

from app.models.deeponet import (
    train_deeponet,
)

from experiments.results_io import (
    save_result,
)


def main():

    print(
        "Generating training data..."
    )

    train_data = (
        generate_american_deeponet_dataset(
            n_parameter_sets=200,
            n_spot_points=40,
            space_steps=160,
            time_steps=160,
            seed=42,
        )
    )

    print(
        "Generating test data..."
    )

    test_data = (
        generate_american_deeponet_dataset(
            n_parameter_sets=50,
            n_spot_points=40,
            space_steps=200,
            time_steps=200,
            seed=123,
        )
    )

    start = perf_counter()

    result = train_deeponet(
        train_data.branch_inputs,
        train_data.trunk_inputs,
        train_data.targets,
        epochs=2500,
        batch_size=1024,
        learning_rate=1e-3,
    )

    training_time = (
        perf_counter() - start
    )

    result.model.eval()

    with torch.no_grad():
        branch = torch.tensor(
            test_data.branch_inputs,
            dtype=torch.float32,
        )

        trunk = torch.tensor(
            test_data.trunk_inputs,
            dtype=torch.float32,
        )

        predictions = (
            result.model(
                branch,
                trunk,
            )
            .numpy()
            .reshape(-1)
        )

    targets = (
        test_data.targets
        .reshape(-1)
    )

    errors = np.abs(
        predictions
        - targets
    )

    print()
    print(
        "American DeepONet"
    )

    print("-" * 55)

    print(
        f"Test MAE:      "
        f"{errors.mean():.6f}"
    )

    print(
        f"Median error:  "
        f"{np.median(errors):.6f}"
    )

    print(
        f"95% error:     "
        f"{np.quantile(errors, 0.95):.6f}"
    )

    print(
        f"Max error:     "
        f"{errors.max():.6f}"
    )

    print(
        f"Training time: "
        f"{training_time:.3f} s"
    )

    print(
        f"Final loss:    "
        f"{result.final_loss:.6e}"
    )

    rmse = float(
    np.sqrt(
        np.mean(
            (
                predictions
                - targets
            )
            ** 2
        )
    )
)

    plt.figure()

    plt.semilogy(
        result.losses
    )

    plt.xlabel(
        "Training epoch"
    )

    plt.ylabel(
        "MSE loss"
    )

    plt.title(
        "American DeepONet "
        "training convergence"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "american_deeponet_loss.png",
        dpi=200,
    )

    plt.figure()

    plt.scatter(
        targets,
        predictions,
        alpha=0.25,
        s=8,
    )

    median_error = float(
            np.median(
                errors
            )
        )
    
    p95_error = float(
        np.quantile(
            errors,
            0.95,
        )
    )

    max_error = float(
        np.max(
            errors
        )
    )

    result_payload = {
        "experiment":
            "american_deeponet",

        "problem": {
            "instrument":
                "american_put",

            "target_solver":
                "projected_crank_nicolson",

            "train_parameter_sets":
                200,

            "test_parameter_sets":
                50,

            "spot_points_per_set":
                40,
        },

        "model": {
            "architecture":
                "deeponet",

            "branch_variables": [
                "strike",
                "rate",
                "volatility",
                "maturity",
                "dividend_yield",
            ],

            "trunk_variables": [
                "spot",
                "time",
            ],
        },

        "metrics": {
            "mae":
                float(
                    errors.mean()
                ),

            "rmse":
                rmse,

            "median_error":
                median_error,

            "p95_error":
                p95_error,

            "max_error":
                max_error,

            "training_seconds":
                training_time,

            "final_loss":
                float(
                    result.final_loss
                ),
        },

        "artifacts": {
            "training_plot":
                "experiments/"
                "american_deeponet_loss.png",

            "prediction_plot":
                "experiments/"
                "american_deeponet_predictions.png",
        },
    }

    save_result(
        "american_deeponet.json",
        result_payload,
    )

    minimum = min(
        targets.min(),
        predictions.min(),
    )

    maximum = max(
        targets.max(),
        predictions.max(),
    )

    plt.plot(
        [minimum, maximum],
        [minimum, maximum],
        linestyle="--",
    )

    plt.xlabel(
        "Projected CN price"
    )

    plt.ylabel(
        "DeepONet price"
    )

    plt.title(
        "American DeepONet "
        "vs classical solver"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "american_deeponet_predictions.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()