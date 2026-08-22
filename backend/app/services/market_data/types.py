from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class OptionChainQuote:
    symbol: str
    expiry: str
    option_type: str
    strike: float

    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]

    volume: Optional[int]
    open_interest: Optional[int]

    implied_volatility: Optional[float]

    source: str


@dataclass(frozen=True)
class OptionChainSnapshot:
    symbol: str
    spot: float
    currency: str

    expiries: List[str]
    quotes: List[OptionChainQuote]

    source: str

    selected_expiries: Optional[
        List[str]
    ] = None

    requested_strikes_per_expiry: Optional[
        int
    ] = None

    returned_quote_count: Optional[
        int
    ] = None

    cache_hit: bool = False

    cache_age_seconds: Optional[
        float
    ] = None

    cache_ttl_seconds: Optional[
        int
    ] = None