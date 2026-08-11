from app.services.market_data.provider import (
    OptionChainProvider,
)

from app.services.market_data.providers.mock import (
    MockOptionChainProvider,
)

from app.services.market_data.types import (
    OptionChainSnapshot,
)

from app.services.market_data.providers.alpha_vantage import (
    AlphaVantageOptionChainProvider,
)


def get_provider(
    name: str = "mock",
) -> OptionChainProvider:

    normalized = (
        name
        .strip()
        .lower()
    )

    if normalized == "mock":
        return (
            MockOptionChainProvider()
        )

    if normalized in {
        "alpha_vantage",
        "alphavantage",
    }:
        return (
            AlphaVantageOptionChainProvider()
        )

    raise ValueError(
        f"Unknown option-chain "
        f"provider: {name}"
    )


def get_option_chain(
    symbol: str,
    provider: str = "mock",
) -> OptionChainSnapshot:

    client = get_provider(
        provider
    )

    return (
        client.get_option_chain(
            symbol
        )
    )