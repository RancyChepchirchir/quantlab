from dataclasses import dataclass
from math import exp, log, sqrt

from scipy.stats import norm


@dataclass(frozen=True)
class OptionInputs:
    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    dividend_yield: float = 0.0


def _validate(inputs: OptionInputs) -> None:
    if inputs.spot <= 0:
        raise ValueError("Spot price must be positive.")

    if inputs.strike <= 0:
        raise ValueError("Strike price must be positive.")

    if inputs.volatility <= 0:
        raise ValueError("Volatility must be positive.")

    if inputs.maturity <= 0:
        raise ValueError("Maturity must be positive.")


def d1_d2(inputs: OptionInputs) -> tuple[float, float]:
    _validate(inputs)

    s = inputs.spot
    k = inputs.strike
    r = inputs.rate
    sigma = inputs.volatility
    t = inputs.maturity
    q = inputs.dividend_yield

    d1 = (
        log(s / k)
        + (r - q + 0.5 * sigma**2) * t
    ) / (sigma * sqrt(t))

    d2 = d1 - sigma * sqrt(t)

    return d1, d2


def european_call(inputs: OptionInputs) -> float:
    d1, d2 = d1_d2(inputs)

    s = inputs.spot
    k = inputs.strike
    r = inputs.rate
    t = inputs.maturity
    q = inputs.dividend_yield

    return (
        s * exp(-q * t) * norm.cdf(d1)
        - k * exp(-r * t) * norm.cdf(d2)
    )


def european_put(inputs: OptionInputs) -> float:
    d1, d2 = d1_d2(inputs)

    s = inputs.spot
    k = inputs.strike
    r = inputs.rate
    t = inputs.maturity
    q = inputs.dividend_yield

    return (
        k * exp(-r * t) * norm.cdf(-d2)
        - s * exp(-q * t) * norm.cdf(-d1)
    )