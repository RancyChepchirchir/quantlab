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

    base_inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    result = train_european_pinn(
        base_inputs,
        option_type="call",
        epochs=3000,
        n_interior=2500,
        n_terminal=750,
        n_boundary=750,
    )

    spots = np.linspace(
        50,
        150,
        101,
    )

    bs_prices = []
    pinn_prices = []
    errors = []

    for spot in spots:

        inputs = OptionInputs(
            spot=float(spot),
            strike=base_inputs.strike,
            rate=base_inputs.rate,
            volatility=base_inputs.volatility,
            maturity=base_inputs.maturity,
            dividend_yield=(
                base_inputs.dividend_yield
            ),
        )

        bs = european_call(inputs)

        pinn = pinn_price(
            result.model,
            spot=float(spot),
            time=0.0,
        )

        bs_prices.append(bs)
        pinn_prices.append(pinn)

        errors.append(
            abs(pinn - bs)
        )

    print()
    print(
        "PINN solution-surface diagnostics"
    )

    print("-" * 48)

    print(
        f"Mean absolute error: "
        f"{np.mean(errors):.6f}"
    )

    print(
        f"Maximum absolute error: "
        f"{np.max(errors):.6f}"
    )

    print(
        f"ATM Black-Scholes: "
        f"{european_call(base_inputs):.6f}"
    )

    print(
        f"ATM PINN: "
        f"{pinn_price(result.model, 100.0):.6f}"
    )

    # ----------------------------------
    # Price comparison
    # ----------------------------------

    plt.figure()

    plt.plot(
        spots,
        bs_prices,
        label="Black–Scholes",
    )

    plt.plot(
        spots,
        pinn_prices,
        linestyle="--",
        label="PINN",
    )

    plt.xlabel(
        "Spot price"
    )

    plt.ylabel(
        "European call value"
    )

    plt.title(
        "PINN solution vs Black–Scholes"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "pinn_vs_black_scholes.png",
        dpi=200,
    )

    # ----------------------------------
    # Error profile
    # ----------------------------------

    plt.figure()

    plt.plot(
        spots,
        errors,
    )

    plt.xlabel(
        "Spot price"
    )

    plt.ylabel(
        "Absolute pricing error"
    )

    plt.title(
        "PINN pricing error across spot"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "pinn_error_profile.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()