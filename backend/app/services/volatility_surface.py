from dataclasses import dataclass
from typing import List, Optional

from app.models.black_scholes import (
    OptionInputs,
)

from app.models.implied_volatility import (
    implied_volatility,
)

from app.models.american_implied_volatility import (
    american_implied_volatility,
)


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
    option_type: str

    implied_volatility: float

    american_implied_volatility: Optional[
        float
    ]

    american_iv_difference: Optional[
        float
    ]

    american_iv_converged: Optional[
        bool
    ]


@dataclass(frozen=True)
class RejectedQuote:
    strike: float
    maturity: float
    market_price: float
    option_type: str
    reason: str


@dataclass(frozen=True)
class CalibrationResult:
    calibrated: List[
        CalibratedQuote
    ]

    rejected: List[
        RejectedQuote
    ]

    input_count: int
    calibrated_count: int
    rejected_count: int
    success_rate: float


def calibrate_option_chain(
    spot: float,
    rate: float,
    dividend_yield: float,
    quotes: List[
        OptionQuote
    ],
    american_steps: int = 300,
) -> CalibrationResult:

    calibrated: List[
        CalibratedQuote
    ] = []

    rejected: List[
        RejectedQuote
    ] = []

    for quote in quotes:

        # -------------------------------------------------
        # Basic validation
        # -------------------------------------------------

        if quote.strike <= 0:
            rejected.append(
                RejectedQuote(
                    strike=
                        quote.strike,

                    maturity=
                        quote.maturity,

                    market_price=
                        quote.market_price,

                    option_type=
                        quote.option_type,

                    reason=
                        "strike must be positive",
                )
            )

            continue

        if quote.maturity <= 0:
            rejected.append(
                RejectedQuote(
                    strike=
                        quote.strike,

                    maturity=
                        quote.maturity,

                    market_price=
                        quote.market_price,

                    option_type=
                        quote.option_type,

                    reason=
                        "maturity must be positive",
                )
            )

            continue

        if quote.market_price <= 0:
            rejected.append(
                RejectedQuote(
                    strike=
                        quote.strike,

                    maturity=
                        quote.maturity,

                    market_price=
                        quote.market_price,

                    option_type=
                        quote.option_type,

                    reason=
                        "market price must be positive",
                )
            )

            continue

        if quote.option_type not in {
            "call",
            "put",
        }:
            rejected.append(
                RejectedQuote(
                    strike=
                        quote.strike,

                    maturity=
                        quote.maturity,

                    market_price=
                        quote.market_price,

                    option_type=
                        quote.option_type,

                    reason=
                        "unsupported option type",
                )
            )

            continue

        # -------------------------------------------------
        # Build common model inputs
        # -------------------------------------------------

        inputs = OptionInputs(
            spot=
                spot,

            strike=
                quote.strike,

            rate=
                rate,

            volatility=
                0.20,

            maturity=
                quote.maturity,

            dividend_yield=
                dividend_yield,
        )

        # -------------------------------------------------
        # European / Black-Scholes implied volatility
        # -------------------------------------------------

        try:
            bs_iv = (
                implied_volatility(
                    inputs,
                    market_price=
                        quote.market_price,
                    option_type=
                        quote.option_type,
                )
            )

        except ValueError as error:
            rejected.append(
                RejectedQuote(
                    strike=
                        quote.strike,

                    maturity=
                        quote.maturity,

                    market_price=
                        quote.market_price,

                    option_type=
                        quote.option_type,

                    reason=
                        str(error),
                )
            )

            continue

        # -------------------------------------------------
        # American / CRR implied volatility
        #
        # This is an additional diagnostic.
        # Failure here must not discard an otherwise
        # successful BS calibration.
        # -------------------------------------------------

        american_iv: Optional[
            float
        ] = None

        american_iv_difference: Optional[
            float
        ] = None

        american_iv_converged: Optional[
            bool
        ] = None

        try:
            american_result = (
                american_implied_volatility(
                    inputs,
                    market_price=
                        quote.market_price,
                    option_type=
                        quote.option_type,
                    steps=
                        american_steps,
                )
            )

            american_iv = (
                american_result
                .implied_volatility
            )

            american_iv_difference = (
                american_iv
                - bs_iv
            )

            american_iv_converged = (
                american_result
                .converged
            )

        except ValueError:
            american_iv = (
                None
            )

            american_iv_difference = (
                None
            )

            american_iv_converged = (
                False
            )

        # -------------------------------------------------
        # Store successful calibration
        # -------------------------------------------------

        calibrated.append(
            CalibratedQuote(
                strike=
                    quote.strike,

                maturity=
                    quote.maturity,

                market_price=
                    quote.market_price,

                option_type=
                    quote.option_type,

                implied_volatility=
                    bs_iv,

                american_implied_volatility=
                    american_iv,

                american_iv_difference=
                    american_iv_difference,

                american_iv_converged=
                    american_iv_converged,
            )
        )

    # -------------------------------------------------
    # Calibration summary
    # -------------------------------------------------

    input_count = len(
        quotes
    )

    calibrated_count = len(
        calibrated
    )

    rejected_count = len(
        rejected
    )

    success_rate = (
        calibrated_count
        / input_count
        if input_count
        else 0.0
    )

    if (
        input_count > 0
        and calibrated_count == 0
    ):
        raise ValueError(
            "No option quotes could "
            "be successfully calibrated."
        )

    return CalibrationResult(
        calibrated=
            calibrated,

        rejected=
            rejected,

        input_count=
            input_count,

        calibrated_count=
            calibrated_count,

        rejected_count=
            rejected_count,

        success_rate=
            success_rate,
    )