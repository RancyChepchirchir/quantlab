from dataclasses import replace

from app.models.black_scholes import (
    OptionInputs,
    european_call,
    european_put,
)


def implied_volatility(
    inputs: OptionInputs,
    market_price: float,
    option_type: str = "call",
    lower_vol: float = 1e-6,
    upper_vol: float = 5.0,
    tolerance: float = 1e-8,
    max_iterations: int = 200,
) -> float:
    """
    Recover Black-Scholes implied volatility
    using a robust bisection solver.
    """

    if option_type not in {
        "call",
        "put",
    }:
        raise ValueError(
            "option_type must be "
            "'call' or 'put'."
        )

    if market_price <= 0:
        raise ValueError(
            "market_price must be positive."
        )

    def price_at_vol(
        volatility: float,
    ) -> float:
        candidate = replace(
            inputs,
            volatility=volatility,
        )

        if option_type == "call":
            return european_call(
                candidate
            )

        return european_put(
            candidate
        )

    low_price = price_at_vol(
        lower_vol
    )

    high_price = price_at_vol(
        upper_vol
    )

    if market_price < low_price:
        raise ValueError(
            "Market price is below "
            "the model price at the "
            "minimum volatility."
        )

    if market_price > high_price:
        raise ValueError(
            "Market price is above "
            "the model price at the "
            "maximum volatility."
        )

    low = lower_vol
    high = upper_vol

    for _ in range(
        max_iterations
    ):
        mid = 0.5 * (
            low + high
        )

        model_price = price_at_vol(
            mid
        )

        error = (
            model_price
            - market_price
        )

        if abs(error) < tolerance:
            return mid

        if model_price < market_price:
            low = mid
        else:
            high = mid

    return 0.5 * (
        low + high
    )