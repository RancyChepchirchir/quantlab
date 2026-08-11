from typing import List

from fastapi import (
    APIRouter,
    HTTPException,
)

from pydantic import (
    BaseModel,
    Field,
)

from app.services.volatility_surface import (
    OptionQuote,
    calibrate_option_chain,
)


router = APIRouter(
    prefix="/calibration",
    tags=["calibration"],
)


class OptionQuoteRequest(BaseModel):
    strike: float = Field(gt=0)
    maturity: float = Field(gt=0)
    market_price: float = Field(gt=0)
    option_type: str = "call"


class VolatilitySurfaceRequest(BaseModel):
    spot: float = Field(gt=0)
    rate: float
    dividend_yield: float = 0.0

    quotes: List[
        OptionQuoteRequest
    ]


@router.post(
    "/volatility-surface"
)
def calibrate_volatility_surface(
    request: VolatilitySurfaceRequest,
):
    quotes = [
        OptionQuote(
            strike=quote.strike,
            maturity=quote.maturity,
            market_price=
                quote.market_price,
            option_type=
                quote.option_type,
        )
        for quote in request.quotes
    ]

    try:
        calibrated = (
            calibrate_option_chain(
                spot=request.spot,
                rate=request.rate,
                dividend_yield=
                    request.dividend_yield,
                quotes=quotes,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "spot":
            request.spot,

        "rate":
            request.rate,

        "dividend_yield":
            request.dividend_yield,

        "quote_count":
            len(calibrated),

        "quotes": [
            {
                "strike":
                    quote.strike,

                "maturity":
                    quote.maturity,

                "market_price":
                    quote.market_price,

                "option_type":
                    quote.option_type,

                "implied_volatility":
                    quote.implied_volatility,

                "implied_volatility_percent":
                    100.0
                    * quote.implied_volatility,
            }
            for quote in calibrated
        ],
    }