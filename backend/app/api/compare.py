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
from app.models.finite_difference import (
    crank_nicolson_price,
)
from app.schemas.pricing import (
    PricingRequest,
)
from app.api.pricing import (
    to_inputs,
)


router = APIRouter(
    tags=["comparison"],
)


# Production-friendly numerical settings.
#
# These are deliberately separate from the larger experiments
# used in the research/benchmark scripts.
CRR_STEPS = 500
CN_SPACE_STEPS = 150
CN_TIME_STEPS = 150
MC_SIMULATIONS = 50_000


@router.post("/compare")
def compare_methods(
    request: PricingRequest,
):
    inputs = to_inputs(request)

    # ---------------------------------------------------------
    # Black-Scholes analytical benchmark
    # ---------------------------------------------------------

    start = perf_counter()

    if request.option_type == "call":
        bs_price = european_call(inputs)
    else:
        bs_price = european_put(inputs)

    bs_runtime = perf_counter() - start

    # ---------------------------------------------------------
    # CRR binomial
    # ---------------------------------------------------------

    start = perf_counter()

    crr = binomial_price(
        inputs,
        option_type=request.option_type,
        steps=CRR_STEPS,
        american=False,
    )

    crr_runtime = perf_counter() - start

    # ---------------------------------------------------------
    # Crank-Nicolson finite difference
    # ---------------------------------------------------------

    start = perf_counter()

    cn = crank_nicolson_price(
        inputs,
        option_type=request.option_type,
        space_steps=CN_SPACE_STEPS,
        time_steps=CN_TIME_STEPS,
    )

    cn_runtime = perf_counter() - start

    # ---------------------------------------------------------
    # Monte Carlo
    # ---------------------------------------------------------

    start = perf_counter()

    mc = monte_carlo_price(
        inputs,
        option_type=request.option_type,
        simulations=MC_SIMULATIONS,
        seed=42,
    )

    mc_runtime = perf_counter() - start

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------

    return {
        "input": {
            "spot": request.spot,
            "strike": request.strike,
            "rate": request.rate,
            "volatility": request.volatility,
            "maturity": request.maturity,
            "dividend_yield": request.dividend_yield,
            "option_type": request.option_type,
        },

        "black_scholes": {
            "price": bs_price,
            "runtime_seconds": bs_runtime,
        },

        "binomial": {
            "price": crr.price,
            "steps": crr.steps,
            "absolute_error": abs(
                crr.price - bs_price
            ),
            "runtime_seconds": crr_runtime,
        },

        "finite_difference": {
            "price": cn.price,
            "space_steps": CN_SPACE_STEPS,
            "time_steps": CN_TIME_STEPS,
            "absolute_error": abs(
                cn.price - bs_price
            ),
            "runtime_seconds": cn_runtime,
        },

        "monte_carlo": {
            "price": mc.price,
            "simulations": mc.simulations,
            "standard_error": mc.standard_error,
            "confidence_interval": [
                mc.confidence_low,
                mc.confidence_high,
            ],
            "absolute_error": abs(
                mc.price - bs_price
            ),
            "runtime_seconds": mc_runtime,
        },
    }