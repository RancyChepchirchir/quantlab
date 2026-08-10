from dataclasses import dataclass
from math import exp, log, pi, sqrt

from app.models.black_scholes import (
    OptionInputs,
)


@dataclass
class Greeks:
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def normal_pdf(x: float) -> float:
    return (
        exp(-0.5 * x * x)
        / sqrt(2.0 * pi)
    )


def normal_cdf(x: float) -> float:
    from math import erf

    return 0.5 * (
        1.0
        + erf(x / sqrt(2.0))
    )


def _d1_d2(
    inputs: OptionInputs,
) -> tuple[float, float]:

    s = inputs.spot
    k = inputs.strike
    r = inputs.rate
    sigma = inputs.volatility
    t = inputs.maturity
    q = inputs.dividend_yield

    d1 = (
        log(s / k)
        + (
            r
            - q
            + 0.5 * sigma**2
        )
        * t
    ) / (
        sigma * sqrt(t)
    )

    d2 = (
        d1
        - sigma * sqrt(t)
    )

    return d1, d2


def black_scholes_greeks(
    inputs: OptionInputs,
    option_type: str = "call",
) -> Greeks:

    s = inputs.spot
    k = inputs.strike
    r = inputs.rate
    sigma = inputs.volatility
    t = inputs.maturity
    q = inputs.dividend_yield

    d1, d2 = _d1_d2(inputs)

    discount_q = exp(-q * t)
    discount_r = exp(-r * t)

    pdf_d1 = normal_pdf(d1)

    gamma = (
        discount_q
        * pdf_d1
        / (
            s
            * sigma
            * sqrt(t)
        )
    )

    # Vega per 1.00 volatility unit.
    # Divide by 100 in the UI if
    # displaying change per 1 vol point.
    vega = (
        s
        * discount_q
        * pdf_d1
        * sqrt(t)
    )

    if option_type == "call":

        delta = (
            discount_q
            * normal_cdf(d1)
        )

        theta = (
            -(
                s
                * discount_q
                * pdf_d1
                * sigma
            )
            / (2 * sqrt(t))
            - r
            * k
            * discount_r
            * normal_cdf(d2)
            + q
            * s
            * discount_q
            * normal_cdf(d1)
        )

        rho = (
            k
            * t
            * discount_r
            * normal_cdf(d2)
        )

    elif option_type == "put":

        delta = (
            discount_q
            * (
                normal_cdf(d1)
                - 1
            )
        )

        theta = (
            -(
                s
                * discount_q
                * pdf_d1
                * sigma
            )
            / (2 * sqrt(t))
            + r
            * k
            * discount_r
            * normal_cdf(-d2)
            - q
            * s
            * discount_q
            * normal_cdf(-d1)
        )

        rho = (
            -k
            * t
            * discount_r
            * normal_cdf(-d2)
        )

    else:
        raise ValueError(
            "option_type must be "
            "'call' or 'put'"
        )

    return Greeks(
        delta=delta,
        gamma=gamma,
        vega=vega,
        theta=theta,
        rho=rho,
    )