from time import perf_counter

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.binomial import (
    binomial_price,
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

    start = perf_counter()

    bs_price = european_call(inputs)

    bs_runtime = (
        perf_counter() - start
    )

    start = perf_counter()

    crr = binomial_price(
        inputs,
        option_type="call",
        steps=1000,
    )

    crr_runtime = (
        perf_counter() - start
    )

    start = perf_counter()

    mc = monte_carlo_price(
        inputs,
        option_type="call",
        simulations=1_000_000,
        seed=42,
    )

    mc_runtime = (
        perf_counter() - start
    )

    print()
    print(
        "European Call Pricing Comparison"
    )
    print("-" * 72)

    print(
        f"{'Method':<20}"
        f"{'Price':>12}"
        f"{'Abs Error':>14}"
        f"{'Runtime (s)':>16}"
    )

    print("-" * 72)

    print(
        f"{'Black-Scholes':<20}"
        f"{bs_price:>12.6f}"
        f"{0.0:>14.6f}"
        f"{bs_runtime:>16.6f}"
    )

    print(
        f"{'CRR (1000)':<20}"
        f"{crr.price:>12.6f}"
        f"{abs(crr.price-bs_price):>14.6f}"
        f"{crr_runtime:>16.6f}"
    )

    print(
        f"{'Monte Carlo (1M)':<20}"
        f"{mc.price:>12.6f}"
        f"{abs(mc.price-bs_price):>14.6f}"
        f"{mc_runtime:>16.6f}"
    )

    print()
    print(
        "Monte Carlo 95% CI:"
    )

    print(
        f"[{mc.confidence_low:.6f}, "
        f"{mc.confidence_high:.6f}]"
    )


if __name__ == "__main__":
    main()