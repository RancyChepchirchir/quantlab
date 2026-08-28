from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass(frozen=True)
class CalendarArbitrageViolation:
    strike: float
    earlier_maturity: float
    later_maturity: float
    earlier_total_variance: float
    later_total_variance: float
    difference: float


@dataclass(frozen=True)
class ButterflyArbitrageViolation:
    maturity: float
    left_strike: float
    center_strike: float
    right_strike: float
    curvature: float


@dataclass(frozen=True)
class VolatilityArbitrageDiagnostics:
    calendar_arbitrage_free: bool
    butterfly_arbitrage_free: bool
    arbitrage_free: bool

    calendar_violation_count: int
    butterfly_violation_count: int
    total_violation_count: int

    calendar_violations: List[
        CalendarArbitrageViolation
    ]

    butterfly_violations: List[
        ButterflyArbitrageViolation
    ]


def total_variance(
    volatility: float,
    maturity: float,
) -> float:
    if volatility < 0.0:
        raise ValueError(
            "volatility must be non-negative"
        )

    if maturity <= 0.0:
        raise ValueError(
            "maturity must be positive"
        )

    return (
        volatility
        * volatility
        * maturity
    )


def detect_calendar_arbitrage(
    strikes: List[float],
    maturities: List[float],
    volatilities: List[float],
    tolerance: float = 1e-10,
) -> List[CalendarArbitrageViolation]:
    if not (
        len(strikes)
        == len(maturities)
        == len(volatilities)
    ):
        raise ValueError(
            "strikes, maturities and volatilities "
            "must have equal lengths"
        )

    grouped = {}

    for strike, maturity, volatility in zip(
        strikes,
        maturities,
        volatilities,
    ):
        grouped.setdefault(
            float(strike),
            [],
        ).append(
            (
                float(maturity),
                total_variance(
                    float(volatility),
                    float(maturity),
                ),
            )
        )

    violations: List[
        CalendarArbitrageViolation
    ] = []

    for strike, observations in grouped.items():
        ordered = sorted(
            observations,
            key=lambda item: item[0],
        )

        for earlier, later in zip(
            ordered[:-1],
            ordered[1:],
        ):
            earlier_maturity = earlier[0]
            earlier_variance = earlier[1]

            later_maturity = later[0]
            later_variance = later[1]

            difference = (
                later_variance
                - earlier_variance
            )

            if difference < -tolerance:
                violations.append(
                    CalendarArbitrageViolation(
                        strike=strike,
                        earlier_maturity=(
                            earlier_maturity
                        ),
                        later_maturity=(
                            later_maturity
                        ),
                        earlier_total_variance=(
                            earlier_variance
                        ),
                        later_total_variance=(
                            later_variance
                        ),
                        difference=difference,
                    )
                )

    return violations


def detect_butterfly_arbitrage(
    strikes: List[float],
    maturities: List[float],
    option_prices: List[float],
    tolerance: float = 1e-10,
) -> List[ButterflyArbitrageViolation]:
    if not (
        len(strikes)
        == len(maturities)
        == len(option_prices)
    ):
        raise ValueError(
            "strikes, maturities and option_prices "
            "must have equal lengths"
        )

    grouped = {}

    for strike, maturity, price in zip(
        strikes,
        maturities,
        option_prices,
    ):
        grouped.setdefault(
            float(maturity),
            [],
        ).append(
            (
                float(strike),
                float(price),
            )
        )

    violations: List[
        ButterflyArbitrageViolation
    ] = []

    for maturity, observations in grouped.items():
        ordered = sorted(
            observations,
            key=lambda item: item[0],
        )

        if len(ordered) < 3:
            continue

        for index in range(
            1,
            len(ordered) - 1,
        ):
            left_strike, left_price = (
                ordered[index - 1]
            )

            center_strike, center_price = (
                ordered[index]
            )

            right_strike, right_price = (
                ordered[index + 1]
            )

            left_width = (
                center_strike
                - left_strike
            )

            right_width = (
                right_strike
                - center_strike
            )

            if (
                left_width <= 0.0
                or right_width <= 0.0
            ):
                continue

            left_slope = (
                center_price
                - left_price
            ) / left_width

            right_slope = (
                right_price
                - center_price
            ) / right_width

            curvature = (
                right_slope
                - left_slope
            )

            if curvature < -tolerance:
                violations.append(
                    ButterflyArbitrageViolation(
                        maturity=maturity,
                        left_strike=left_strike,
                        center_strike=(
                            center_strike
                        ),
                        right_strike=(
                            right_strike
                        ),
                        curvature=curvature,
                    )
                )

    return violations


def diagnose_volatility_arbitrage(
    strikes: List[float],
    maturities: List[float],
    volatilities: List[float],
    option_prices: Optional[
        List[float]
    ] = None,
    tolerance: float = 1e-10,
) -> VolatilityArbitrageDiagnostics:
    calendar_violations = (
        detect_calendar_arbitrage(
            strikes=strikes,
            maturities=maturities,
            volatilities=volatilities,
            tolerance=tolerance,
        )
    )

    butterfly_violations: List[
        ButterflyArbitrageViolation
    ] = []

    if option_prices is not None:
        butterfly_violations = (
            detect_butterfly_arbitrage(
                strikes=strikes,
                maturities=maturities,
                option_prices=option_prices,
                tolerance=tolerance,
            )
        )

    calendar_count = len(
        calendar_violations
    )

    butterfly_count = len(
        butterfly_violations
    )

    total_count = (
        calendar_count
        + butterfly_count
    )

    calendar_free = (
        calendar_count == 0
    )

    butterfly_free = (
        butterfly_count == 0
    )

    return VolatilityArbitrageDiagnostics(
        calendar_arbitrage_free=(
            calendar_free
        ),
        butterfly_arbitrage_free=(
            butterfly_free
        ),
        arbitrage_free=(
            calendar_free
            and butterfly_free
        ),
        calendar_violation_count=(
            calendar_count
        ),
        butterfly_violation_count=(
            butterfly_count
        ),
        total_violation_count=(
            total_count
        ),
        calendar_violations=(
            calendar_violations
        ),
        butterfly_violations=(
            butterfly_violations
        ),
    )