from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from app.services.market_data.service import (
    get_option_chain,
)


router = APIRouter(
    prefix="/market-data",
    tags=["market-data"],
)


@router.get(
    "/options/{symbol}"
)
def option_chain(
    symbol: str,
    provider: str = Query(
        default="mock"
    ),
):
    try:
        snapshot = (
            get_option_chain(
                symbol=symbol,
                provider=provider,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "symbol":
            snapshot.symbol,

        "spot":
            snapshot.spot,

        "currency":
            snapshot.currency,

        "expiries":
            snapshot.expiries,

        "source":
            snapshot.source,

        "quotes": [
            {
                "symbol":
                    quote.symbol,

                "expiry":
                    quote.expiry,

                "option_type":
                    quote.option_type,

                "strike":
                    quote.strike,

                "bid":
                    quote.bid,

                "ask":
                    quote.ask,

                "last":
                    quote.last,

                "volume":
                    quote.volume,

                "open_interest":
                    quote.open_interest,

                "implied_volatility":
                    quote.implied_volatility,

                "source":
                    quote.source,
            }
            for quote
            in snapshot.quotes
        ],
    }