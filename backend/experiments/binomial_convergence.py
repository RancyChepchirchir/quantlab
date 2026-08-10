from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.binomial import (
    binomial_price,
)

import matplotlib.pyplot as plt


def main():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    bs_price = european_call(inputs)

    steps_list = [
        10,
        25,
        50,
        100,
        250,
        500,
        1000,
    ]

    print("-" * 50)

    errors = []

    for steps in steps_list:
        crr_price = binomial_price(
            inputs,
            option_type="call",
            steps=steps,
            american=False,
        ).price

        error = abs(
            crr_price - bs_price
        )

        errors.append(error)

        print(
            f"{steps:8d} "
            f"{crr_price:12.6f} "
            f"{bs_price:12.6f} "
            f"{error:12.6f}"
        )

    plt.figure()

    plt.plot(
        steps_list,
        errors,
        marker="o",
    )

    plt.xscale("log")
    plt.yscale("log")

    plt.xlabel("Number of CRR steps")
    plt.ylabel("Absolute pricing error")

    plt.title(
        "CRR convergence to Black–Scholes"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/binomial_convergence.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()