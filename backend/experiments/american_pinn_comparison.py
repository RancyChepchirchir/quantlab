from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.binomial import (
    binomial_price,
)

from app.models.american_finite_difference import (
    projected_crank_nicolson_put,
)

from app.models.american_pinn import (
    train_american_put_pinn,
    american_pinn_price,
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

    # --------------------
    # Train PINN
    # --------------------

    start = perf_counter()

    pinn_result = (
        train_american_put_pinn(
            base,
            epochs=3000,
        )
    )

    pinn_runtime = (
        perf_counter() - start
    )

    # --------------------
    # FDM benchmark
    # --------------------

    start = perf_counter()

    fdm_result = (
        projected_crank_nicolson_put(
            base,
            space_steps=300,
            time_steps=300,
        )
    )

    fdm_runtime = (
        perf_counter() - start
    )

    # --------------------
    # Evaluate grid
    # --------------------

    crr_prices = []
    fdm_prices = []
    pinn_prices = []

    for spot in spots:

        inputs = OptionInputs(
            spot=float(spot),
            strike=base.strike,
            rate=base.rate,
            volatility=base.volatility,
            maturity=base.maturity,
            dividend_yield=base.dividend_yield,
        )

        crr = binomial_price(
            inputs,
            option_type="put",
            steps=1500,
            american=True,
        ).price

        fdm = float(
            np.interp(
                spot,
                fdm_result.spot_grid,
                fdm_result.value_grid[0],
            )
        )

        pinn = american_pinn_price(
            pinn_result.model,
            float(spot),
        )

        crr_prices.append(crr)
        fdm_prices.append(fdm)
        pinn_prices.append(pinn)

    crr_prices = np.asarray(
        crr_prices
    )

    fdm_prices = np.asarray(
        fdm_prices
    )

    pinn_prices = np.asarray(
        pinn_prices
    )

    fdm_errors = np.abs(
        fdm_prices
        - crr_prices
    )

    pinn_errors = np.abs(
        pinn_prices
        - crr_prices
    )

    print()
    print(
        "American Put: PINN vs Classical"
    )

    print("-" * 76)

    print(
        f"{'Method':<22}"
        f"{'MAE vs CRR':>16}"
        f"{'Max Error':>16}"
        f"{'Runtime (s)':>18}"
    )

    print("-" * 76)

    print(
        f"{'Projected CN':<22}"
        f"{fdm_errors.mean():>16.6f}"
        f"{fdm_errors.max():>16.6f}"
        f"{fdm_runtime:>18.6f}"
    )

    print(
        f"{'American PINN':<22}"
        f"{pinn_errors.mean():>16.6f}"
        f"{pinn_errors.max():>16.6f}"
        f"{pinn_runtime:>18.6f}"
    )

    plt.figure()

    plt.plot(
        spots,
        crr_prices,
        label="CRR benchmark",
    )

    plt.plot(
        spots,
        fdm_prices,
        linestyle="--",
        label="Projected CN",
    )

    plt.plot(
        spots,
        pinn_prices,
        linestyle=":",
        label="American PINN",
    )

    plt.xlabel(
        "Spot price"
    )

    plt.ylabel(
        "American put value"
    )

    plt.title(
        "American put solution comparison"
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "american_pinn_solution.png",
        dpi=200,
    )

    plt.figure()

    plt.plot(
        spots,
        fdm_errors,
        label="Projected CN",
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
        "Absolute error vs CRR"
    )

    plt.title(
        "American option pricing error"
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "american_pinn_error.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()