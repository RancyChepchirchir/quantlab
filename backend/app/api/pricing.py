from fastapi import APIRouter

from app.models.black_scholes import (
    OptionInputs,
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
    BinomialPricingRequest,
    MonteCarloPricingRequest,
    FiniteDifferencePricingRequest,
)

from app.models.greeks import (
    black_scholes_greeks,
)

from app.models.finite_difference import (
    crank_nicolson_price,
)


router = APIRouter(
    prefix="/price",
    tags=["pricing"],
)


def to_inputs(
    request: PricingRequest,
) -> OptionInputs:
    return OptionInputs(
        spot=request.spot,
        strike=request.strike,
        rate=request.rate,
        volatility=request.volatility,
        maturity=request.maturity,
        dividend_yield=(
            request.dividend_yield
        ),
    )


@router.post("/black-scholes")
def price_black_scholes(
    request: PricingRequest,
):
    inputs = to_inputs(request)

    if request.option_type == "call":
        price = european_call(inputs)
    else:
        price = european_put(inputs)

    return {
        "method": "black-scholes",
        "option_type":
            request.option_type,
        "price": price,
    }


@router.post("/binomial")
def price_binomial(
    request: BinomialPricingRequest,
):
    inputs = to_inputs(request)

    result = binomial_price(
        inputs,
        option_type=request.option_type,
        steps=request.steps,
        american=request.american,
    )

    return {
        "method": "crr-binomial",
        "option_type":
            request.option_type,
        "american":
            request.american,
        "steps":
            result.steps,
        "price":
            result.price,
    }


@router.post("/monte-carlo")
def price_monte_carlo(
    request: MonteCarloPricingRequest,
):
    inputs = to_inputs(request)

    result = monte_carlo_price(
        inputs,
        option_type=request.option_type,
        simulations=request.simulations,
        seed=request.seed,
    )

    return {
        "method": "monte-carlo",
        "option_type":
            request.option_type,
        "simulations":
            result.simulations,
        "price":
            result.price,
        "standard_error":
            result.standard_error,
        "confidence_interval": [
            result.confidence_low,
            result.confidence_high,
        ],
    }

@router.post("/greeks")
def price_greeks(
    request: PricingRequest,
):
    inputs = to_inputs(request)

    greeks = black_scholes_greeks(
        inputs,
        option_type=request.option_type,
    )

    return {
        "method": "black-scholes",
        "option_type": request.option_type,
        "delta": greeks.delta,
        "gamma": greeks.gamma,
        "vega": greeks.vega,
        "theta": greeks.theta,
        "rho": greeks.rho,
    }

@router.post(
    "/finite-difference"
)
def price_finite_difference(
    request:
        FiniteDifferencePricingRequest,
):
    inputs = to_inputs(request)

    result = crank_nicolson_price(
        inputs,
        option_type=request.option_type,
        space_steps=request.space_steps,
        time_steps=request.time_steps,
    )

    return {
        "method":
            "crank-nicolson",
        "option_type":
            request.option_type,
        "space_steps":
            request.space_steps,
        "time_steps":
            request.time_steps,
        "price":
            result.price,
    }