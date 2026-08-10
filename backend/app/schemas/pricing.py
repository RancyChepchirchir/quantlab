from typing import Literal, Optional

from pydantic import BaseModel, Field


class PricingRequest(BaseModel):
    spot: float = Field(gt=0)
    strike: float = Field(gt=0)
    rate: float
    volatility: float = Field(gt=0)
    maturity: float = Field(gt=0)
    dividend_yield: float = 0.0

    option_type: Literal[
        "call",
        "put",
    ] = "call"


class BinomialPricingRequest(
    PricingRequest
):
    steps: int = Field(
        default=500,
        gt=0,
        le=5000,
    )

    american: bool = False


class MonteCarloPricingRequest(
    PricingRequest
):
    simulations: int = Field(
        default=100_000,
        gt=1,
        le=5_000_000,
    )

    seed: Optional[int] = 42

class SpotSweepRequest(PricingRequest):
    spot_min: float = Field(default=50, gt=0)
    spot_max: float = Field(default=150, gt=0)
    points: int = Field(default=51, ge=10, le=500)

class FiniteDifferencePricingRequest(
    PricingRequest
):
    space_steps: int = Field(
        default=150,
        ge=20,
        le=500,
    )

    time_steps: int = Field(
        default=150,
        ge=20,
        le=500,
    )