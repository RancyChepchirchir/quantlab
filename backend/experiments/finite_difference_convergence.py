from time import perf_counter

import matplotlib.pyplot as plt

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.finite_difference import (
    crank_nicolson_price,
)


def main():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    benchmark = european_call(inputs)

    grids = [
        25,
        50,
        100,
        200,
        300,
    ]

    errors = []
    runtimes = []

    print()
    print(
        "Crank–Nicolson Convergence"
    )
    print("-" * 72)

    print(
        f"{'Grid':>10}"
        f"{'CN Price':>14}"
        f"{'BS Price':>14}"
        f"{'Abs Error':>14}"
        f"{'Runtime':>14}"
    )

    print("-" * 72)

    for grid in grids:
        start = perf_counter()

        result = crank_nicolson_price(
            inputs,
            option_type="call",
            space_steps=grid,
            time_steps=grid,
        )

        runtime = (
            perf_counter()
            - start
        )

        error = abs(
            result.price
            - benchmark
        )

        errors.append(error)
        runtimes.append(runtime)

        print(
            f"{grid:10d}"
            f"{result.price:14.6f}"
            f"{benchmark:14.6f}"
            f"{error:14.6f}"
            f"{runtime:14.6f}"
        )

    plt.figure()

    plt.plot(
        grids,
        errors,
        marker="o",
    )

    plt.xscale("log")
    plt.yscale("log")

    plt.xlabel(
        "Spatial / temporal grid size"
    )

    plt.ylabel(
        "Absolute pricing error"
    )

    plt.title(
        "Crank–Nicolson convergence "
        "to Black–Scholes"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "finite_difference_convergence.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()