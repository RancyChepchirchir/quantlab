from typing import List

from app.services.market_data.types import (
    OptionChainQuote,
)


def filter_option_quotes(
    quotes: List[OptionChainQuote],
    spot: float,
    min_moneyness: float = 0.80,
    max_moneyness: float = 1.20,
    require_positive_price: bool = True,
) -> List[OptionChainQuote]:
    """
    Basic cleaning for option-chain calibration.

    Keeps contracts within a configurable strike/spot
    range and rejects unusable observations.
    """

    filtered = []

    for quote in quotes:
        if quote.strike <= 0:
            continue

        moneyness = (
            quote.strike
            / spot
        )

        if (
            moneyness
            < min_moneyness
        ):
            continue

        if (
            moneyness
            > max_moneyness
        ):
            continue

        market_price = (
            quote.last
        )

        if (
            require_positive_price
            and (
                market_price is None
                or market_price <= 0
            )
        ):
            continue

        filtered.append(
            quote
        )

    return filtered