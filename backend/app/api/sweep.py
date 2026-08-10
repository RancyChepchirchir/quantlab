import numpy as np
from fastapi import APIRouter

from app.models.black_scholes import (
    OptionInputs,
    european_call,
    european_put,
)
from app.models.greeks import (
    black_scholes_greeks,
)
from app.schemas.pricing import (
    SpotSweepRequest,
)


router = APIRouter(
    prefix="/sweep",
    tags=["sweep"],
)


@router.post("/spot")
def spot_sweep(
    request: SpotSweepRequest,
):
    if request.spot_max <= request.spot_min:
        raise ValueError(
            "spot_max must be greater than spot_min"
        )

    spots = np.linspace(
        request.spot_min,
        request.spot_max,
        request.points,
    )

    prices = []
    deltas = []
    gammas = []

    for spot in spots:
        inputs = OptionInputs(
            spot=float(spot),
            strike=request.strike,
            rate=request.rate,
            volatility=request.volatility,
            maturity=request.maturity,
            dividend_yield=request.dividend_yield,
        )

        if request.option_type == "call":
            price = european_call(inputs)
        else:
            price = european_put(inputs)

        greeks = black_scholes_greeks(
            inputs,
            option_type=request.option_type,
        )

        prices.append(price)
        deltas.append(greeks.delta)
        gammas.append(greeks.gamma)

    return {
        "spot": spots.tolist(),
        "price": prices,
        "delta": deltas,
        "gamma": gammas,
    }