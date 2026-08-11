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