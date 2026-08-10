from dataclasses import dataclass
from math import exp, sqrt

import numpy as np

from .black_scholes import OptionInputs
from typing import Optional


@dataclass(frozen=True)
class MonteCarloResult:
    price: float
    standard_error: float
    confidence_low: float
    confidence_high: float
    simulations: int


def monte_carlo_price(
    inputs: OptionInputs,
    option_type: str = "call",
    simulations: int = 100_000,
    seed: Optional[int] = 42,
) -> MonteCarloResult:

    if option_type not in {"call", "put"}:
        raise ValueError(
            "option_type must be 'call' or 'put'."
        )

    if simulations <= 1:
        raise ValueError(
            "simulations must be greater than 1."
        )

    rng = np.random.default_rng(seed)

    z = rng.standard_normal(simulations)

    terminal_prices = (
        inputs.spot
        * np.exp(
            (
                inputs.rate
                - inputs.dividend_yield
                - 0.5
                * inputs.volatility**2
            )
            * inputs.maturity
            + inputs.volatility
            * sqrt(inputs.maturity)
            * z
        )
    )

    if option_type == "call":
        payoffs = np.maximum(
            terminal_prices
            - inputs.strike,
            0.0,
        )
    else:
        payoffs = np.maximum(
            inputs.strike
            - terminal_prices,
            0.0,
        )

    discounted_payoffs = (
        exp(
            -inputs.rate
            * inputs.maturity
        )
        * payoffs
    )

    price = float(
        np.mean(discounted_payoffs)
    )

    standard_error = float(
        np.std(
            discounted_payoffs,
            ddof=1,
        )
        / sqrt(simulations)
    )

    confidence_low = (
        price
        - 1.96 * standard_error
    )

    confidence_high = (
        price
        + 1.96 * standard_error
    )

    return MonteCarloResult(
        price=price,
        standard_error=standard_error,
        confidence_low=confidence_low,
        confidence_high=confidence_high,
        simulations=simulations,
    )