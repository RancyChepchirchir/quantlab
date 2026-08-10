from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.finite_difference import (
    crank_nicolson_price,
)

from app.models.pinn import (
    pinn_price,
    train_european_pinn,
)


def main():
    base = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    spots = np.linspace(
        50,
        150,
        101,
    )

    # -------------------------
    # Train PINN
    # -------------------------

    start = perf_counter()

    pinn_result = train_european_pinn(
        base,
        option_type="call",
        epochs=3000,
        n_interior=2500,
        n_terminal=750,
        n_boundary=750,
    )

    pinn_training_time = (
        perf_counter() - start
    )

    # -------------------------
    # Crank–Nicolson solution
    # -------------------------

    start = perf_counter()

    cn_result = crank_nicolson_price(
        base,
        option_type="call",
        space_steps=300,
        time_steps=300,
    )

    cn_runtime = (
        perf_counter() - start
    )

    # -------------------------
    # Evaluate spot grid
    # -------------------------

    bs_prices = []
    pinn_prices = []
    cn_prices = []

    for spot in spots:
        inputs = OptionInputs(
            spot=float(spot),
            strike=base.strike,
            rate=base.rate,
            volatility=base.volatility,
            maturity=base.maturity,
            dividend_yield=base.dividend_yield,
        )

        bs_prices.append(
            european_call(inputs)
        )

        pinn_prices.append(
            pinn_price(
                pinn_result.model,
                float(spot),
                time=0.0,
            )
        )

        cn_prices.append(
            float(
                np.interp(
                    spot,
                    cn_result.spot_grid,
                    cn_result.value_grid[0],
                )
            )
        )

    bs_prices = np.asarray(
        bs_prices
    )

    pinn_prices = np.asarray(
        pinn_prices
    )

    cn_prices = np.asarray(
        cn_prices
    )

    # -------------------------
    # Errors
    # -------------------------

    pinn_errors = np.abs(
        pinn_prices - bs_prices
    )

    cn_errors = np.abs(
        cn_prices - bs_prices
    )

    print()
    print(
        "PINN vs Crank–Nicolson"
    )
    print("-" * 72)

    print(
        f"{'Method':<22}"
        f"{'MAE':>14}"
        f"{'Max Error':>14}"
        f"{'Runtime (s)':>18}"
    )

    print("-" * 72)

    print(
        f"{'Crank–Nicolson':<22}"
        f"{np.mean(cn_errors):>14.6f}"
        f"{np.max(cn_errors):>14.6f}"
        f"{cn_runtime:>18.6f}"
    )

    print(
        f"{'PINN':<22}"
        f"{np.mean(pinn_errors):>14.6f}"
        f"{np.max(pinn_errors):>14.6f}"
        f"{pinn_training_time:>18.6f}"
    )

    # -------------------------
    # Solution curves
    # -------------------------

    plt.figure()

    plt.plot(
        spots,
        bs_prices,
        label="Black–Scholes",
    )

    plt.plot(
        spots,
        cn_prices,
        linestyle="--",
        label="Crank–Nicolson",
    )

    plt.plot(
        spots,
        pinn_prices,
        linestyle=":",
        label="PINN",
    )

    plt.xlabel(
        "Spot price"
    )

    plt.ylabel(
        "European call price"
    )

    plt.title(
        "Black–Scholes solution comparison"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "pinn_vs_fdm_solution.png",
        dpi=200,
    )

    # -------------------------
    # Error curves
    # -------------------------

    plt.figure()

    plt.plot(
        spots,
        cn_errors,
        label="Crank–Nicolson",
    )

    plt.plot(
        spots,
        pinn_errors,
        label="PINN",
    )

    plt.xlabel(
        "Spot price"
    )

    plt.ylabel(
        "Absolute pricing error"
    )

    plt.title(
        "Numerical error across spot"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "pinn_vs_fdm_error.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()