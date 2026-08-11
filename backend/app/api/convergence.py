from math import sqrt
from time import perf_counter

from fastapi import APIRouter

from app.models.black_scholes import (
    european_call,
    european_put,
)
from app.models.binomial import (
    binomial_price,
)
from app.models.monte_carlo import (
    monte_carlo_price,
)
from app.schemas.pricing import (
    PricingRequest,
)
from app.api.pricing import (
    to_inputs,
)


router = APIRouter(
    prefix="/convergence",
    tags=["convergence"],
)


# Production convergence grid.
#
# Large-scale experiments belong in experiments/.
# The API only needs enough points to demonstrate
# deterministic and stochastic convergence clearly.

CRR_STEPS = [
    10,
    25,
    50,
    100,
    250,
    500,
]

MC_SIMULATIONS = [
    100,
    1_000,
    5_000,
    10_000,
    50_000,
    100_000,
]


@router.post("")
def convergence_analysis(
    request: PricingRequest,
):
    inputs = to_inputs(request)

    # ---------------------------------------------------------
    # Analytical benchmark
    # ---------------------------------------------------------

    if request.option_type == "call":
        benchmark = european_call(inputs)
    else:
        benchmark = european_put(inputs)

    # ---------------------------------------------------------
    # CRR convergence
    # ---------------------------------------------------------

    crr_results = []

    for steps in CRR_STEPS:
        start = perf_counter()

        result = binomial_price(
            inputs,
            option_type=request.option_type,
            steps=steps,
            american=False,
        )

        runtime = perf_counter() - start

        crr_results.append(
            {
                "steps": steps,
                "price": result.price,
                "absolute_error": abs(
                    result.price - benchmark
                ),
                "runtime_seconds": runtime,
            }
        )

    # ---------------------------------------------------------
    # Monte Carlo convergence
    # ---------------------------------------------------------

    mc_results = []

    for simulations in MC_SIMULATIONS:
        start = perf_counter()

        result = monte_carlo_price(
            inputs,
            option_type=request.option_type,
            simulations=simulations,
            seed=42,
        )

        runtime = perf_counter() - start

        mc_results.append(
            {
                "simulations": simulations,
                "price": result.price,
                "absolute_error": abs(
                    result.price - benchmark
                ),
                "standard_error":
                    result.standard_error,
                "confidence_low":
                    result.confidence_low,
                "confidence_high":
                    result.confidence_high,
                "runtime_seconds":
                    runtime,
            }
        )

    # ---------------------------------------------------------
    # Theoretical Monte Carlo convergence
    #
    # Standard Monte Carlo error decreases approximately
    # according to:
    #
    #              error ~ 1 / sqrt(N)
    #
    # We scale the theoretical curve using the first
    # empirical standard error.
    # ---------------------------------------------------------

    reference_scale = (
        mc_results[0]["standard_error"]
        * sqrt(
            mc_results[0]["simulations"]
        )
    )

    for item in mc_results:
        item["theoretical_error"] = (
            reference_scale
            / sqrt(
                item["simulations"]
            )
        )

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------

    return {
        "benchmark": {
            "method": "black-scholes",
            "price": benchmark,
        },

        "crr": crr_results,

        "monte_carlo": mc_results,
    }