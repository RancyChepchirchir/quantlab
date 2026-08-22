from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from app.services.market_data.errors import (
    MarketDataProviderError,
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

    provider: str = "mock",

    refresh: bool = Query(
        default=False,
        description=(
            "Bypass successful-chain cache "
            "and provider failure cooldown."
        ),
    ),
):
    try:
        return (
            get_option_chain(
                symbol=symbol,
                provider=provider,
                use_cache=(
                    not refresh
                ),
            )
        )

    except MarketDataProviderError as error:
        raise HTTPException(
            status_code=(
                error.status_code
            ),

            detail={
                "message":
                    error.message,

                "provider":
                    error.provider,

                "upstream_status":
                    error
                    .upstream_status,

                "retryable":
                    error.retryable,

                "cached":
                    error.cached,

                "retry_after_seconds":
                    error
                    .retry_after_seconds,
            },
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,

            detail={
                "message":
                    str(error),

                "provider":
                    provider,

                "upstream_status":
                    None,

                "retryable":
                    False,

                "cached":
                    False,

                "retry_after_seconds":
                    None,
            },
        ) from error