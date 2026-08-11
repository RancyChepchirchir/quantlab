import numpy as np
import matplotlib.pyplot as plt

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.implied_volatility import (
    implied_volatility,
)


def synthetic_volatility(
    strike: float,
    maturity: float,
    spot: float = 100.0,
) -> float:
    """
    Simple synthetic smile/skew surface.

    This is intentionally deterministic so we can
    test whether implied-volatility inversion
    recovers the generating volatility.
    """

    moneyness = (
        strike / spot
        - 1.0
    )

    return (
        0.20
        + 0.35 * moneyness**2
        - 0.08 * moneyness
        + 0.025 * np.sqrt(maturity)
    )


def main():
    spot = 100.0
    rate = 0.05
    dividend_yield = 0.0

    strikes = np.linspace(
        70.0,
        130.0,
        31,
    )

    maturities = np.array(
        [
            0.25,
            0.50,
            1.00,
            1.50,
            2.00,
        ]
    )

    recovered_surface = np.zeros(
        (
            len(maturities),
            len(strikes),
        ),
        dtype=float,
    )

    true_surface = np.zeros_like(
        recovered_surface
    )

    errors = []

    for i, maturity in enumerate(
        maturities
    ):
        for j, strike in enumerate(
            strikes
        ):
            true_vol = (
                synthetic_volatility(
                    strike,
                    maturity,
                    spot,
                )
            )

            inputs = OptionInputs(
                spot=spot,
                strike=float(strike),
                rate=rate,
                volatility=float(
                    true_vol
                ),
                maturity=float(
                    maturity
                ),
                dividend_yield=
                    dividend_yield,
            )

            market_price = (
                european_call(
                    inputs
                )
            )

            recovered_vol = (
                implied_volatility(
                    inputs,
                    market_price=
                        market_price,
                    option_type="call",
                )
            )

            true_surface[
                i,
                j,
            ] = true_vol

            recovered_surface[
                i,
                j,
            ] = recovered_vol

            errors.append(
                abs(
                    recovered_vol
                    - true_vol
                )
            )

    errors = np.asarray(
        errors
    )

    print()
    print(
        "Implied Volatility Surface Recovery"
    )
    print("=" * 60)

    print(
        f"Mean absolute vol error: "
        f"{errors.mean():.8f}"
    )

    print(
        f"Maximum vol error:       "
        f"{errors.max():.8f}"
    )

    # --------------------------------------------------
    # Smile slices
    # --------------------------------------------------

    plt.figure()

    for i, maturity in enumerate(
        maturities
    ):
        plt.plot(
            strikes,
            recovered_surface[
                i
            ],
            label=(
                f"T={maturity:.2f}"
            ),
        )

    plt.xlabel(
        "Strike"
    )

    plt.ylabel(
        "Implied volatility"
    )

    plt.title(
        "Synthetic Implied-Volatility Smiles"
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "implied_volatility_smiles.png",
        dpi=200,
    )

    # --------------------------------------------------
    # Recovery error
    # --------------------------------------------------

    plt.figure()

    for i, maturity in enumerate(
        maturities
    ):
        plt.plot(
            strikes,
            np.abs(
                recovered_surface[i]
                - true_surface[i]
            ),
            label=(
                f"T={maturity:.2f}"
            ),
        )

    plt.xlabel(
        "Strike"
    )

    plt.ylabel(
        "Absolute volatility error"
    )

    plt.title(
        "Implied-Volatility Recovery Error"
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "implied_volatility_error.png",
        dpi=200,
    )

    # --------------------------------------------------
    # 3D surface
    # --------------------------------------------------

    strike_grid, maturity_grid = (
        np.meshgrid(
            strikes,
            maturities,
        )
    )

    figure = plt.figure()

    axis = figure.add_subplot(
        111,
        projection="3d",
    )

    axis.plot_surface(
        strike_grid,
        maturity_grid,
        recovered_surface,
    )

    axis.set_xlabel(
        "Strike"
    )

    axis.set_ylabel(
        "Maturity"
    )

    axis.set_zlabel(
        "Implied volatility"
    )

    axis.set_title(
        "Implied-Volatility Surface"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "implied_volatility_surface.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()