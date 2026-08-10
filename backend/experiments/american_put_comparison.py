from time import perf_counter

from app.models.black_scholes import (
    OptionInputs,
    european_put,
)

from app.models.binomial import (
    binomial_price,
)

from app.models.american_finite_difference import (
    projected_crank_nicolson_put,
)


def main():
    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    european = european_put(
        inputs
    )

    start = perf_counter()

    crr = binomial_price(
        inputs,
        option_type="put",
        steps=2000,
        american=True,
    )

    crr_runtime = (
        perf_counter() - start
    )

    start = perf_counter()

    fd = (
        projected_crank_nicolson_put(
            inputs,
            space_steps=300,
            time_steps=300,
        )
    )

    fd_runtime = (
        perf_counter() - start
    )

    print()
    print(
        "American Put Comparison"
    )

    print("-" * 68)

    print(
        f"{'Method':<24}"
        f"{'Price':>12}"
        f"{'Premium':>14}"
        f"{'Runtime':>16}"
    )

    print("-" * 68)

    print(
        f"{'European BS put':<24}"
        f"{european:>12.6f}"
        f"{0.0:>14.6f}"
        f"{'-':>16}"
    )

    print(
        f"{'American CRR':<24}"
        f"{crr.price:>12.6f}"
        f"{crr.price-european:>14.6f}"
        f"{crr_runtime:>16.6f}"
    )

    print(
        f"{'Projected CN':<24}"
        f"{fd.price:>12.6f}"
        f"{fd.price-european:>14.6f}"
        f"{fd_runtime:>16.6f}"
    )


if __name__ == "__main__":
    main()