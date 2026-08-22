from dataclasses import dataclass
from math import (
    exp,
    sqrt,
)
from typing import Optional

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.binomial import (
    binomial_price,
)


@dataclass(frozen=True)
class AmericanImpliedVolatilityResult:
    implied_volatility: float
    iterations: int
    model_price: float
    market_price: float
    absolute_pricing_error: float
    converged: bool


def american_implied_volatility(
    inputs: OptionInputs,
    market_price: float,
    option_type: str = "put",
    steps: int = 500,
    lower_vol: float = 1e-4,
    upper_vol: float = 5.0,
    tolerance: float = 1e-6,
    max_iterations: int = 100,
) -> AmericanImpliedVolatilityResult:
    """
    Recover American-option implied volatility
    using CRR pricing and bisection.

    The solver automatically adjusts the lower
    volatility bound when the requested bound
    would make the CRR risk-neutral probability
    invalid.
    """

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

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

    if inputs.spot <= 0:
        raise ValueError(
            "spot must be positive."
        )

    if inputs.strike <= 0:
        raise ValueError(
            "strike must be positive."
        )

    if inputs.maturity <= 0:
        raise ValueError(
            "maturity must be positive."
        )

    if steps < 2:
        raise ValueError(
            "steps must be >= 2."
        )

    if lower_vol <= 0:
        raise ValueError(
            "lower_vol must be positive."
        )

    if upper_vol <= lower_vol:
        raise ValueError(
            "upper_vol must exceed lower_vol."
        )

    if tolerance <= 0:
        raise ValueError(
            "tolerance must be positive."
        )

    if max_iterations < 1:
        raise ValueError(
            "max_iterations must be >= 1."
        )

    # --------------------------------------------------
    # CRR-valid lower volatility
    # --------------------------------------------------
    #
    # CRR requires:
    #
    #     d <= exp((r-q)dt) <= u
    #
    # where
    #
    #     u = exp(sigma sqrt(dt))
    #     d = exp(-sigma sqrt(dt))
    #
    # Therefore sigma must be sufficiently large
    # relative to |r-q| sqrt(dt).
    #
    # Add a small safety margin so numerical
    # round-off does not place p just outside
    # [0, 1].
    # --------------------------------------------------

    dt = (
        inputs.maturity
        / steps
    )

    minimum_crr_vol = (
        abs(
            inputs.rate
            - inputs.dividend_yield
        )
        * sqrt(dt)
    )

    effective_lower_vol = max(
        lower_vol,
        minimum_crr_vol
        * 1.01,
        1e-8,
    )

    if (
        effective_lower_vol
        >= upper_vol
    ):
        raise ValueError(
            "No valid CRR volatility "
            "search interval exists."
        )

    # --------------------------------------------------
    # CRR probability helper
    # --------------------------------------------------

    def valid_crr_probability(
        volatility: float,
    ) -> bool:
        u = exp(
            volatility
            * sqrt(dt)
        )

        d = 1.0 / u

        denominator = (
            u - d
        )

        if denominator <= 0:
            return False

        growth = exp(
            (
                inputs.rate
                - inputs.dividend_yield
            )
            * dt
        )

        probability = (
            growth - d
        ) / denominator

        return (
            0.0
            <= probability
            <= 1.0
        )

    # Defensive adjustment in case floating-point
    # behaviour still leaves the lower bound invalid.
    adjustment_count = 0

    while (
        not valid_crr_probability(
            effective_lower_vol
        )
    ):
        effective_lower_vol *= 1.10

        adjustment_count += 1

        if (
            effective_lower_vol
            >= upper_vol
            or adjustment_count
            > 100
        ):
            raise ValueError(
                "Unable to construct "
                "a valid CRR volatility "
                "search interval."
            )

    # --------------------------------------------------
    # Pricing helper
    # --------------------------------------------------

    def price_at_volatility(
        volatility: float,
    ) -> float:
        candidate = OptionInputs(
            spot=
                inputs.spot,

            strike=
                inputs.strike,

            rate=
                inputs.rate,

            volatility=
                volatility,

            maturity=
                inputs.maturity,

            dividend_yield=
                inputs.dividend_yield,
        )

        result = binomial_price(
            candidate,
            option_type=
                option_type,
            steps=
                steps,
            american=
                True,
        )

        return float(
            result.price
        )

    # --------------------------------------------------
    # Evaluate search interval
    # --------------------------------------------------

    low_price = (
        price_at_volatility(
            effective_lower_vol
        )
    )

    high_price = (
        price_at_volatility(
            upper_vol
        )
    )

    # --------------------------------------------------
    # Check whether market price is attainable
    # --------------------------------------------------

    if (
        market_price
        < low_price - tolerance
    ):
        raise ValueError(
            "Market price is below "
            "the American model price "
            "at the minimum valid "
            "volatility."
        )

    if (
        market_price
        > high_price + tolerance
    ):
        raise ValueError(
            "Market price is above "
            "the American model price "
            "at the maximum volatility."
        )

    # --------------------------------------------------
    # Boundary solutions
    # --------------------------------------------------

    if abs(
        market_price
        - low_price
    ) <= tolerance:
        return (
            AmericanImpliedVolatilityResult(
                implied_volatility=
                    effective_lower_vol,

                iterations=
                    0,

                model_price=
                    low_price,

                market_price=
                    market_price,

                absolute_pricing_error=
                    abs(
                        low_price
                        - market_price
                    ),

                converged=
                    True,
            )
        )

    if abs(
        market_price
        - high_price
    ) <= tolerance:
        return (
            AmericanImpliedVolatilityResult(
                implied_volatility=
                    upper_vol,

                iterations=
                    0,

                model_price=
                    high_price,

                market_price=
                    market_price,

                absolute_pricing_error=
                    abs(
                        high_price
                        - market_price
                    ),

                converged=
                    True,
            )
        )

    # --------------------------------------------------
    # Bisection
    # --------------------------------------------------

    low = (
        effective_lower_vol
    )

    high = (
        upper_vol
    )

    best_volatility: Optional[
        float
    ] = None

    best_price: Optional[
        float
    ] = None

    best_error = float(
        "inf"
    )

    for iteration in range(
        1,
        max_iterations + 1,
    ):
        mid = (
            0.5
            * (
                low + high
            )
        )

        model_price = (
            price_at_volatility(
                mid
            )
        )

        pricing_error = (
            model_price
            - market_price
        )

        absolute_error = abs(
            pricing_error
        )

        if (
            absolute_error
            < best_error
        ):
            best_error = (
                absolute_error
            )

            best_volatility = (
                mid
            )

            best_price = (
                model_price
            )

        if (
            absolute_error
            <= tolerance
        ):
            return (
                AmericanImpliedVolatilityResult(
                    implied_volatility=
                        mid,

                    iterations=
                        iteration,

                    model_price=
                        model_price,

                    market_price=
                        market_price,

                    absolute_pricing_error=
                        absolute_error,

                    converged=
                        True,
                )
            )

        # American option value is normally
        # non-decreasing in volatility.
        if (
            model_price
            < market_price
        ):
            low = mid

        else:
            high = mid

    # --------------------------------------------------
    # Maximum iterations reached
    # --------------------------------------------------

    if (
        best_volatility is None
        or best_price is None
    ):
        raise ValueError(
            "American implied-volatility "
            "solver failed to produce "
            "a candidate solution."
        )

    return (
        AmericanImpliedVolatilityResult(
            implied_volatility=
                best_volatility,

            iterations=
                max_iterations,

            model_price=
                best_price,

            market_price=
                market_price,

            absolute_pricing_error=
                best_error,

            converged=
                best_error
                <= tolerance,
        )
    )