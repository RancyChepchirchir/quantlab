from time import perf_counter

import numpy as np

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.binomial import (
    binomial_price,
)


def main():

    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    steps_list = [
        100,
        250,
        500,
        1000,
        2000,
    ]

    print()
    print(
        "American Put CRR Benchmark"
    )

    print("-" * 65)

    print(
        f"{'Steps':>10}"
        f"{'Price':>14}"
        f"{'Runtime':>16}"
    )

    for steps in steps_list:

        start = perf_counter()

        result = binomial_price(
            inputs,
            option_type="put",
            steps=steps,
            american=True,
        )

        runtime = (
            perf_counter()
            - start
        )

        print(
            f"{steps:10d}"
            f"{result.price:14.6f}"
            f"{runtime:16.6f}"
        )


if __name__ == "__main__":
    main()