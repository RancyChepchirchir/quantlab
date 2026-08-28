from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from app.models.black_scholes import (
    OptionInputs,
    european_call,
)

from app.services.svi import (
    SVISurfaceResult,
)

from app.services.ssvi import (
    SSVISurfaceResult,
    ssvi_total_variance,
)

from app.services.volatility_arbitrage import (
    VolatilityArbitrageDiagnostics,
    diagnose_volatility_arbitrage,
)

from app.services.volatility_surface import (
    CalibratedQuote,
)


@dataclass(frozen=True)
class ArbitrageLayerResult:
    name: str
    diagnostics: VolatilityArbitrageDiagnostics


@dataclass(frozen=True)
class VolatilityArbitrageLayerComparison:
    market: ArbitrageLayerResult
    svi: ArbitrageLayerResult
    ssvi: ArbitrageLayerResult


def _collapse_calibrated_quotes(
    quotes: List[CalibratedQuote],
) -> List[Dict[str, float]]:
    """
    Collapse duplicate calibrated observations while preserving
    option type.

    Call and put market prices must never be averaged together
    because butterfly convexity is defined across prices belonging
    to the same option type.
    """
    grouped = {}

    for quote in quotes:
        option_type = str(
            quote.option_type
        ).lower()

        key = (
            round(
                float(quote.maturity),
                8,
            ),
            float(quote.strike),
            option_type,
        )

        grouped.setdefault(
            key,
            [],
        ).append(
            quote
        )

    collapsed: List[
        Dict[str, float]
    ] = []

    for (
        maturity,
        strike,
        option_type,
    ), observations in sorted(
        grouped.items()
    ):
        ivs = [
            float(
                item.implied_volatility
            )
            for item in observations
        ]

        prices = [
            float(
                item.market_price
            )
            for item in observations
        ]

        collapsed.append(
            {
                "strike": strike,
                "maturity": maturity,
                "option_type": option_type,
                "implied_volatility": float(
                    np.mean(ivs)
                ),
                "market_price": float(
                    np.mean(prices)
                ),
            }
        )

    return collapsed


def _market_diagnostics(
    quotes: List[CalibratedQuote],
) -> VolatilityArbitrageDiagnostics:
    collapsed = (
        _collapse_calibrated_quotes(
            quotes
        )
    )

    if not collapsed:
        return diagnose_volatility_arbitrage(
            strikes=[],
            maturities=[],
            volatilities=[],
            option_prices=[],
        )

    # Calendar diagnostics use implied volatility.
    #
    # Prefer calls where available so that we do not mix
    # call- and put-derived observations at the same
    # strike/maturity point.
    calendar_points = {}

    for item in collapsed:
        key = (
            item["maturity"],
            item["strike"],
        )

        existing = (
            calendar_points.get(
                key
            )
        )

        if (
            existing is None
            or (
                item["option_type"]
                == "call"
                and existing[
                    "option_type"
                ]
                != "call"
            )
        ):
            calendar_points[
                key
            ] = item

    calendar_quotes = list(
        calendar_points.values()
    )

    calendar_diagnostics = (
        diagnose_volatility_arbitrage(
            strikes=[
                item["strike"]
                for item in calendar_quotes
            ],
            maturities=[
                item["maturity"]
                for item in calendar_quotes
            ],
            volatilities=[
                item[
                    "implied_volatility"
                ]
                for item in calendar_quotes
            ],
            option_prices=[
                item["market_price"]
                for item in calendar_quotes
            ],
        )
    )

    #
    # Butterfly convexity MUST be checked separately
    # for calls and puts.
    #
    butterfly_violations = []

    for option_type in (
        "call",
        "put",
    ):
        subset = [
            item
            for item in collapsed
            if item[
                "option_type"
            ]
            == option_type
        ]

        if not subset:
            continue

        diagnostics = (
            diagnose_volatility_arbitrage(
                strikes=[
                    item["strike"]
                    for item in subset
                ],
                maturities=[
                    item["maturity"]
                    for item in subset
                ],
                volatilities=[
                    item[
                        "implied_volatility"
                    ]
                    for item in subset
                ],
                option_prices=[
                    item["market_price"]
                    for item in subset
                ],
            )
        )

        butterfly_violations.extend(
            diagnostics
            .butterfly_violations
        )

    calendar_violations = (
        calendar_diagnostics
        .calendar_violations
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

    return VolatilityArbitrageDiagnostics(
        calendar_arbitrage_free=(
            calendar_count == 0
        ),
        butterfly_arbitrage_free=(
            butterfly_count == 0
        ),
        arbitrage_free=(
            total_count == 0
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


def _svi_diagnostics(
    svi_surface: SVISurfaceResult,
    spot: float,
    rate: float,
    dividend_yield: float,
) -> VolatilityArbitrageDiagnostics:
    strikes: List[float] = []
    maturities: List[float] = []
    volatilities: List[float] = []
    option_prices: List[float] = []

    for smile in svi_surface.smiles:
        maturity = float(
            smile.parameters.maturity
        )

        for point in smile.points:
            strike = float(
                point.strike
            )

            fitted_iv = float(
                point.fitted_iv
            )

            inputs = OptionInputs(
                spot=spot,
                strike=strike,
                rate=rate,
                volatility=fitted_iv,
                maturity=maturity,
                dividend_yield=dividend_yield,
            )

            price = european_call(
                inputs
            )

            strikes.append(
                strike
            )

            maturities.append(
                maturity
            )

            volatilities.append(
                fitted_iv
            )

            option_prices.append(
                float(price)
            )

    return diagnose_volatility_arbitrage(
        strikes=strikes,
        maturities=maturities,
        volatilities=volatilities,
        option_prices=option_prices,
    )


def _ssvi_diagnostics(
    ssvi_surface: SSVISurfaceResult,
    spot: float,
    rate: float,
    dividend_yield: float,
) -> VolatilityArbitrageDiagnostics:
    strikes: List[float] = []
    maturities: List[float] = []
    volatilities: List[float] = []
    option_prices: List[float] = []

    eta = float(
        ssvi_surface.parameters.eta
    )

    rho = float(
        ssvi_surface.parameters.rho
    )

    gamma = float(
        ssvi_surface.parameters.gamma
    )

    for atm_slice in (
        ssvi_surface.atm_slices
    ):
        maturity = float(
            atm_slice.maturity
        )

        forward = float(
            atm_slice.forward
        )

        theta_value = float(
            atm_slice.theta
        )

        k_grid = np.linspace(
            -0.35,
            0.35,
            51,
        )

        theta_grid = np.full_like(
            k_grid,
            theta_value,
            dtype=float,
        )

        total_variances = (
            ssvi_total_variance(
                log_moneyness=k_grid,
                theta=theta_grid,
                eta=eta,
                rho=rho,
                gamma=gamma,
            )
        )

        for (
            k,
            total_variance_value,
        ) in zip(
            k_grid,
            total_variances,
        ):
            strike = float(
                forward
                * np.exp(k)
            )

            fitted_iv = float(
                np.sqrt(
                    max(
                        float(
                            total_variance_value
                        ),
                        1e-16,
                    )
                    / maturity
                )
            )

            inputs = OptionInputs(
                spot=spot,
                strike=strike,
                rate=rate,
                volatility=fitted_iv,
                maturity=maturity,
                dividend_yield=dividend_yield,
            )

            price = european_call(
                inputs
            )

            strikes.append(
                strike
            )

            maturities.append(
                maturity
            )

            volatilities.append(
                fitted_iv
            )

            option_prices.append(
                float(price)
            )

    return diagnose_volatility_arbitrage(
        strikes=strikes,
        maturities=maturities,
        volatilities=volatilities,
        option_prices=option_prices,
    )


def compare_arbitrage_layers(
    quotes: List[CalibratedQuote],
    svi_surface: SVISurfaceResult,
    ssvi_surface: SSVISurfaceResult,
    spot: float,
    rate: float,
    dividend_yield: float,
) -> VolatilityArbitrageLayerComparison:
    market = (
        _market_diagnostics(
            quotes
        )
    )

    svi = (
        _svi_diagnostics(
            svi_surface=svi_surface,
            spot=spot,
            rate=rate,
            dividend_yield=dividend_yield,
        )
    )

    ssvi = (
        _ssvi_diagnostics(
            ssvi_surface=ssvi_surface,
            spot=spot,
            rate=rate,
            dividend_yield=dividend_yield,
        )
    )

    return VolatilityArbitrageLayerComparison(
        market=ArbitrageLayerResult(
            name="market",
            diagnostics=market,
        ),
        svi=ArbitrageLayerResult(
            name="svi",
            diagnostics=svi,
        ),
        ssvi=ArbitrageLayerResult(
            name="ssvi",
            diagnostics=ssvi,
        ),
    )