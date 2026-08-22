from dataclasses import dataclass
from math import exp
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.services.volatility_surface import (
    CalibratedQuote,
)


@dataclass(frozen=True)
class MoneynessDiagnostic:
    strike: float
    maturity: float
    option_type: str
    implied_volatility: float
    moneyness: float
    log_moneyness: float


@dataclass(frozen=True)
class SkewDiagnostic:
    maturity: float
    atm_strike: float
    atm_implied_volatility: float
    skew_slope: Optional[float]
    observation_count: int


@dataclass(frozen=True)
class TermStructurePoint:
    maturity: float
    atm_strike: float
    atm_implied_volatility: float


@dataclass(frozen=True)
class PutCallParityDiagnostic:
    strike: float
    maturity: float
    call_price: float
    put_price: float
    theoretical_difference: float
    observed_difference: float
    parity_error: float


@dataclass(frozen=True)
class VolatilityDiagnostics:
    moneyness: List[MoneynessDiagnostic]
    skew: List[SkewDiagnostic]
    atm_term_structure: List[
        TermStructurePoint
    ]
    put_call_parity: List[
        PutCallParityDiagnostic
    ]
    mean_absolute_parity_error: Optional[
        float
    ]
    max_absolute_parity_error: Optional[
        float
    ]


def _group_by_maturity(
    quotes: List[CalibratedQuote],
) -> Dict[
    float,
    List[CalibratedQuote],
]:
    grouped: Dict[
        float,
        List[CalibratedQuote],
    ] = {}

    for quote in quotes:
        key = round(
            quote.maturity,
            8,
        )

        grouped.setdefault(
            key,
            [],
        ).append(
            quote
        )

    return grouped


def build_moneyness_diagnostics(
    quotes: List[CalibratedQuote],
    spot: float,
) -> List[MoneynessDiagnostic]:

    if spot <= 0:
        raise ValueError(
            "spot must be positive."
        )

    diagnostics = []

    for quote in quotes:
        moneyness = (
            quote.strike
            / spot
        )

        log_moneyness = (
            np.log(
                moneyness
            )
        )

        diagnostics.append(
            MoneynessDiagnostic(
                strike=
                    quote.strike,

                maturity=
                    quote.maturity,

                option_type=
                    quote.option_type,

                implied_volatility=
                    quote.implied_volatility,

                moneyness=
                    float(
                        moneyness
                    ),

                log_moneyness=
                    float(
                        log_moneyness
                    ),
            )
        )

    return diagnostics


def build_skew_diagnostics(
    quotes: List[CalibratedQuote],
    spot: float,
) -> List[SkewDiagnostic]:

    if spot <= 0:
        raise ValueError(
            "spot must be positive."
        )

    grouped = (
        _group_by_maturity(
            quotes
        )
    )

    results = []

    for (
        maturity,
        maturity_quotes,
    ) in sorted(
        grouped.items()
    ):
        if not maturity_quotes:
            continue

        atm_quote = min(
            maturity_quotes,
            key=lambda quote:
                abs(
                    quote.strike
                    - spot
                ),
        )

        x = np.array(
            [
                np.log(
                    quote.strike
                    / spot
                )
                for quote
                in maturity_quotes
            ],
            dtype=float,
        )

        y = np.array(
            [
                quote
                .implied_volatility
                for quote
                in maturity_quotes
            ],
            dtype=float,
        )

        skew_slope = None

        if (
            len(
                maturity_quotes
            )
            >= 2
            and np.ptp(x) > 0
        ):
            slope, _ = np.polyfit(
                x,
                y,
                1,
            )

            skew_slope = float(
                slope
            )

        results.append(
            SkewDiagnostic(
                maturity=
                    maturity,

                atm_strike=
                    atm_quote.strike,

                atm_implied_volatility=
                    atm_quote
                    .implied_volatility,

                skew_slope=
                    skew_slope,

                observation_count=
                    len(
                        maturity_quotes
                    ),
            )
        )

    return results


def build_atm_term_structure(
    quotes: List[CalibratedQuote],
    spot: float,
) -> List[TermStructurePoint]:

    if spot <= 0:
        raise ValueError(
            "spot must be positive."
        )

    grouped = (
        _group_by_maturity(
            quotes
        )
    )

    term_structure = []

    for (
        maturity,
        maturity_quotes,
    ) in sorted(
        grouped.items()
    ):
        if not maturity_quotes:
            continue

        atm_quote = min(
            maturity_quotes,
            key=lambda quote:
                abs(
                    quote.strike
                    - spot
                ),
        )

        term_structure.append(
            TermStructurePoint(
                maturity=
                    maturity,

                atm_strike=
                    atm_quote.strike,

                atm_implied_volatility=
                    atm_quote
                    .implied_volatility,
            )
        )

    return term_structure


def build_put_call_parity_diagnostics(
    quotes: List[CalibratedQuote],
    spot: float,
    rate: float,
    dividend_yield: float,
) -> List[
    PutCallParityDiagnostic
]:

    if spot <= 0:
        raise ValueError(
            "spot must be positive."
        )

    calls: Dict[
        Tuple[float, float],
        CalibratedQuote,
    ] = {}

    puts: Dict[
        Tuple[float, float],
        CalibratedQuote,
    ] = {}

    for quote in quotes:
        key = (
            round(
                quote.strike,
                8,
            ),
            round(
                quote.maturity,
                8,
            ),
        )

        if (
            quote.option_type
            == "call"
        ):
            calls[
                key
            ] = quote

        elif (
            quote.option_type
            == "put"
        ):
            puts[
                key
            ] = quote

    common_keys = (
        calls.keys()
        & puts.keys()
    )

    diagnostics = []

    for key in sorted(
        common_keys
    ):
        call = calls[
            key
        ]

        put = puts[
            key
        ]

        strike = (
            call.strike
        )

        maturity = (
            call.maturity
        )

        observed_difference = (
            call.market_price
            - put.market_price
        )

        theoretical_difference = (
            spot
            * exp(
                -dividend_yield
                * maturity
            )
            - strike
            * exp(
                -rate
                * maturity
            )
        )

        parity_error = (
            observed_difference
            - theoretical_difference
        )

        diagnostics.append(
            PutCallParityDiagnostic(
                strike=
                    strike,

                maturity=
                    maturity,

                call_price=
                    call.market_price,

                put_price=
                    put.market_price,

                theoretical_difference=
                    theoretical_difference,

                observed_difference=
                    observed_difference,

                parity_error=
                    parity_error,
            )
        )

    return diagnostics


def calculate_volatility_diagnostics(
    quotes: List[CalibratedQuote],
    spot: float,
    rate: float,
    dividend_yield: float,
) -> VolatilityDiagnostics:

    moneyness = (
        build_moneyness_diagnostics(
            quotes,
            spot,
        )
    )

    skew = (
        build_skew_diagnostics(
            quotes,
            spot,
        )
    )

    atm_term_structure = (
        build_atm_term_structure(
            quotes,
            spot,
        )
    )

    parity = (
        build_put_call_parity_diagnostics(
            quotes,
            spot,
            rate,
            dividend_yield,
        )
    )

    if parity:
        absolute_errors = np.array(
            [
                abs(
                    item.parity_error
                )
                for item
                in parity
            ],
            dtype=float,
        )

        mean_absolute_parity_error = (
            float(
                np.mean(
                    absolute_errors
                )
            )
        )

        max_absolute_parity_error = (
            float(
                np.max(
                    absolute_errors
                )
            )
        )

    else:
        mean_absolute_parity_error = (
            None
        )

        max_absolute_parity_error = (
            None
        )

    return VolatilityDiagnostics(
        moneyness=
            moneyness,

        skew=
            skew,

        atm_term_structure=
            atm_term_structure,

        put_call_parity=
            parity,

        mean_absolute_parity_error=
            mean_absolute_parity_error,

        max_absolute_parity_error=
            max_absolute_parity_error,
    )