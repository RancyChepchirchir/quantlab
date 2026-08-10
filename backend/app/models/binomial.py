from dataclasses import dataclass
from math import exp, sqrt

from .black_scholes import OptionInputs


@dataclass(frozen=True)
class BinomialResult:
    price: float
    steps: int


def binomial_price(
    inputs: OptionInputs,
    option_type: str = "call",
    steps: int = 100,
    american: bool = False,
) -> BinomialResult:
    """
    Cox-Ross-Rubinstein binomial option pricing model.

    Supports:
    - European calls
    - European puts
    - American calls
    - American puts
    """

    if option_type not in {"call", "put"}:
        raise ValueError(
            "option_type must be 'call' or 'put'."
        )

    if steps <= 0:
        raise ValueError(
            "steps must be positive."
        )

    s = inputs.spot
    k = inputs.strike
    r = inputs.rate
    sigma = inputs.volatility
    t = inputs.maturity
    q = inputs.dividend_yield

    dt = t / steps

    u = exp(sigma * sqrt(dt))
    d = 1.0 / u

    discount = exp(-r * dt)

    p = (
        exp((r - q) * dt) - d
    ) / (u - d)

    if not 0.0 <= p <= 1.0:
        raise ValueError(
            "Invalid risk-neutral probability."
        )

    # Terminal option values
    values = []

    for j in range(steps + 1):
        stock_price = (
            s
            * (u ** j)
            * (d ** (steps - j))
        )

        if option_type == "call":
            payoff = max(
                stock_price - k,
                0.0,
            )
        else:
            payoff = max(
                k - stock_price,
                0.0,
            )

        values.append(payoff)

    # Backward induction
    for step in range(
        steps - 1,
        -1,
        -1,
    ):
        next_values = []

        for j in range(step + 1):
            continuation = (
                discount
                * (
                    p * values[j + 1]
                    + (1.0 - p)
                    * values[j]
                )
            )

            if american:
                stock_price = (
                    s
                    * (u ** j)
                    * (d ** (step - j))
                )

                if option_type == "call":
                    exercise = max(
                        stock_price - k,
                        0.0,
                    )
                else:
                    exercise = max(
                        k - stock_price,
                        0.0,
                    )

                next_values.append(
                    max(
                        continuation,
                        exercise,
                    )
                )
            else:
                next_values.append(
                    continuation
                )

        values = next_values

    return BinomialResult(
        price=values[0],
        steps=steps,
    )