from app.services.market_data.provider import (
    OptionChainProvider,
)

from app.services.market_data.providers.mock import (
    MockOptionChainProvider,
)

from app.services.market_data.types import (
    OptionChainSnapshot,
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