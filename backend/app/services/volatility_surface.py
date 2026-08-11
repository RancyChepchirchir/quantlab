from dataclasses import dataclass

import numpy as np

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.implied_volatility import (
    implied_volatility,
)

from typing import List


@dataclass(frozen=True)
class OptionQuote:
    strike: float
    maturity: float
    market_price: float
    option_type: str = "call"


@dataclass(frozen=True)
class CalibratedQuote:
    strike: float
    maturity: float
    market_price: float
    implied_volatility: float
    option_type: str


def calibrate_option_chain(
    spot: float,
    rate: float,
    dividend_yield: float,
    quotes: List[OptionQuote],
) -> list[CalibratedQuote]:

    calibrated = []

    for quote in quotes:
        inputs = OptionInputs(
            spot=spot,
            strike=quote.strike,
            rate=rate,
            volatility=0.20,
            maturity=quote.maturity,
            dividend_yield=
                dividend_yield,
        )

        sigma = implied_volatility(
            inputs,
            market_price=
                quote.market_price,
            option_type=
                quote.option_type,
        )

        calibrated.append(
            CalibratedQuote(
                strike=
                    quote.strike,
                maturity=
                    quote.maturity,
                market_price=
                    quote.market_price,
                implied_volatility=
                    sigma,
                option_type=
                    quote.option_type,
            )
        )

    return calibrated