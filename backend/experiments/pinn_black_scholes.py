import matplotlib.pyplot as plt

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.models.pinn import (
    pinn_price,
    train_european_pinn,
)


def main():

    inputs = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
    )

    benchmark = european_call(
        inputs
    )

    result = train_european_pinn(
        inputs,
        option_type="call",
        epochs=2000,
    )

    prediction = pinn_price(
        result.model,
        spot=inputs.spot,
        time=0.0,
    )

    error = abs(
        prediction
        - benchmark
    )

    print()
    print(
        "PINN vs Black-Scholes"
    )

    print("-" * 45)

    print(
        f"Black-Scholes: "
        f"{benchmark:.6f}"
    )

    print(
        f"PINN:          "
        f"{prediction:.6f}"
    )

    print(
        f"Absolute error:"
        f" {error:.6f}"
    )

    print(
        f"Final loss:    "
        f"{result.final_loss:.6e}"
    )

    plt.figure()

    plt.semilogy(
        result.losses
    )

    plt.xlabel(
        "Training epoch"
    )

    plt.ylabel(
        "PINN loss"
    )

    plt.title(
        "Black–Scholes PINN "
        "training convergence"
    )

    plt.tight_layout()

    plt.savefig(
        "experiments/"
        "pinn_training_loss.png",
        dpi=200,
    )

    plt.show()


if __name__ == "__main__":
    main()