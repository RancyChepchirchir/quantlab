from math import sqrt

import matplotlib.pyplot as plt

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.monte_carlo import (
    monte_carlo_price,
)


def main():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    bs_price = european_call(inputs)

    simulations_list = [
        100,
        1_000,
        10_000,
        100_000,
        1_000_000,
    ]

    errors = []
    standard_errors = []

    print(
        f"{'Simulations':>12} "
        f"{'MC Price':>12} "
        f"{'BS Price':>12} "
        f"{'Abs Error':>12} "
        f"{'Std Error':>12}"
    )

    print("-" * 68)

    for simulations in simulations_list:
        result = monte_carlo_price(
            inputs,
            option_type="call",
            simulations=simulations,
            seed=42,
        )

        error = abs(
            result.price - bs_price
        )

        errors.append(error)
        standard_errors.append(
            result.standard_error
        )

        print(
            f"{simulations:12d} "
            f"{result.price:12.6f} "
            f"{bs_price:12.6f} "
            f"{error:12.6f} "
            f"{result.standard_error:12.6f}"
        )

    plt.figure()

    plt.plot(
        simulations_list,
        errors,
        marker="o",
        label="Absolute pricing error",
    )

    plt.plot(
        simulations_list,
        standard_errors,
        marker="o",
        label="Monte Carlo standard error",
    )

    # theoretical O(M^-1/2) reference
    reference_scale = (
        standard_errors[0]
        * sqrt(simulations_list[0])
    )

    theoretical = [
        reference_scale / sqrt(m)
        for m in simulations_list
    ]

    plt.plot(
        simulations_list,
        theoretical,
        linestyle="--",
        label=r"Theoretical $O(M^{-1/2})$",
    )

    plt.xscale("log")
    plt.yscale("log")

    plt.xlabel(
        "Number of Monte Carlo simulations"
    )

    plt.ylabel(
        "Error"
    )

    plt.title(
        "Monte Carlo convergence to Black–Scholes"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "experiments/monte_carlo_convergence.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()