from time import perf_counter

import matplotlib.pyplot as plt
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

    test_data = (
        generate_deeponet_dataset(
            n_parameter_sets=100,
            n_spot_points=40,
            seed=123,
        )
    )

    start = perf_counter()

    result = train_deeponet(
        train_data.branch_inputs,
        train_data.trunk_inputs,
        train_data.targets,
        epochs=2000,
        batch_size=1024,
    )

    training_time = (
        perf_counter() - start
    )

    result.model.eval()

    with torch.no_grad():

        branch_test = torch.tensor(
            test_data.branch_inputs,
            dtype=torch.float32,
        )

        trunk_test = torch.tensor(
            test_data.trunk_inputs,
            dtype=torch.float32,
        )

        predictions = (
            result.model(
                branch_test,
                trunk_test,
            )
            .numpy()
            .reshape(-1)
        )

    targets = (
        test_data.targets
        .reshape(-1)
    )

    errors = np.abs(
        predictions - targets
    )

    print()
    print(
        "DeepONet generalisation"
    )

    print("-" * 50)

    print(
        f"Test MAE: "
        f"{np.mean(errors):.6f}"
    )

    print(
        f"Max error: "
        f"{np.max(errors):.6f}"
    )

    print(
        f"Training time: "
        f"{training_time:.3f} s"
    )

    print(
        f"Final loss: "
        f"{result.final_loss:.6e}"
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
        "DeepONet training convergence"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "deeponet_training_loss.png",
        dpi=200,
    )

    plt.figure()

    plt.scatter(
        targets,
        predictions,
        alpha=0.3,
        s=8,
    )

    lower = min(
        targets.min(),
        predictions.min(),
    )

    upper = max(
        targets.max(),
        predictions.max(),
    )

    plt.plot(
        [lower, upper],
        [lower, upper],
        linestyle="--",
    )

    plt.xlabel(
        "Black–Scholes price"
    )

    plt.ylabel(
        "DeepONet price"
    )

    plt.title(
        "DeepONet prediction "
        "vs analytical benchmark"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "deeponet_predictions.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()