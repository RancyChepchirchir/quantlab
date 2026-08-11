from fastapi import (
    APIRouter,
    HTTPException,
)

from pydantic import BaseModel, Field

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.implied_volatility import (
    implied_volatility,
)


router = APIRouter(
    prefix="/calibration",
    tags=["calibration"],
)


class ImpliedVolatilityRequest(
    BaseModel
):
    spot: float = Field(gt=0)
    strike: float = Field(gt=0)

    rate: float

    maturity: float = Field(gt=0)

    dividend_yield: float = 0.0

    market_price: float = Field(
        gt=0
    )

    option_type: str = "call"


@router.post(
    "/implied-volatility"
)
def calibrate_implied_volatility(
    request:
        ImpliedVolatilityRequest,
):
    inputs = OptionInputs(
        spot=request.spot,
        strike=request.strike,
        rate=request.rate,
        volatility=0.20,
        maturity=request.maturity,
        dividend_yield=
            request.dividend_yield,
    )

    try:
        sigma = implied_volatility(
            inputs,
            market_price=
                request.market_price,
            option_type=
                request.option_type,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "implied_volatility":
            sigma,

        "implied_volatility_percent":
            100.0 * sigma,

        "market_price":
            request.market_price,

        "option_type":
            request.option_type,
    }