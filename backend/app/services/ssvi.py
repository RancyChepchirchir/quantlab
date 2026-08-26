from dataclasses import dataclass
from math import exp, log
from typing import Dict, List, Optional, Tuple

import numpy as np

from scipy.optimize import (
    least_squares,
)

from app.services.volatility_surface import (
    CalibratedQuote,
)


@dataclass(frozen=True)
class SSVIParameters:
    eta: float
    rho: float
    gamma: float

    rmse: float
    observation_count: int
    maturity_count: int


@dataclass(frozen=True)
class SSVIAtmSlice:
    maturity: float

    forward: float

    atm_strike: float
    atm_implied_volatility: float

    theta: float


@dataclass(frozen=True)
class SSVIFittedPoint:
    strike: float
    maturity: float

    forward: float

    log_forward_moneyness: float

    theta: float

    observed_iv: Optional[float]

    fitted_iv: float

    observed_total_variance: Optional[float]

    fitted_total_variance: float


@dataclass(frozen=True)
class SSVIArbitrageDiagnostic:
    maturity: float

    theta: float
    phi: float

    first_butterfly_bound: float
    second_butterfly_bound: float

    first_bound_satisfied: bool
    second_bound_satisfied: bool

    butterfly_warning: bool


@dataclass(frozen=True)
class SSVICalendarDiagnostic:
    shorter_maturity: float
    longer_maturity: float

    minimum_variance_difference: float

    violation_detected: bool
    violation_count: int

    comparison_point_count: int


@dataclass(frozen=True)
class SSVISurfaceResult:
    parameters: SSVIParameters

    atm_slices: List[
        SSVIAtmSlice
    ]

    points: List[
        SSVIFittedPoint
    ]

    arbitrage_diagnostics: List[
        SSVIArbitrageDiagnostic
    ]

    calendar_diagnostics: List[
        SSVICalendarDiagnostic
    ]

    butterfly_warning: bool
    calendar_warning: bool


def forward_price(
    spot: float,
    rate: float,
    dividend_yield: float,
    maturity: float,
) -> float:
    """
    Continuously compounded forward:

        F(T) = S exp((r - q)T)
    """

    if spot <= 0.0:
        raise ValueError(
            "spot must be positive."
        )

    if maturity <= 0.0:
        raise ValueError(
            "maturity must be positive."
        )

    return float(
        spot
        * exp(
            (
                rate
                - dividend_yield
            )
            * maturity
        )
    )


def forward_log_moneyness(
    strike: float,
    forward: float,
) -> float:
    """
    k = log(K / F)
    """

    if strike <= 0.0:
        raise ValueError(
            "strike must be positive."
        )

    if forward <= 0.0:
        raise ValueError(
            "forward must be positive."
        )

    return float(
        log(
            strike
            / forward
        )
    )


def ssvi_phi(
    theta: np.ndarray,
    eta: float,
    gamma: float,
) -> np.ndarray:
    """
    Power-law SSVI phi function:

        phi(theta)
        =
        eta /
        [
            theta^gamma
            (1 + theta)^(1-gamma)
        ]
    """

    theta_array = np.asarray(
        theta,
        dtype=float,
    )

    if eta <= 0.0:
        raise ValueError(
            "eta must be positive."
        )

    if not (
        0.0
        <= gamma
        <= 1.0
    ):
        raise ValueError(
            "gamma must lie in [0, 1]."
        )

    if np.any(
        theta_array <= 0.0
    ):
        raise ValueError(
            "theta must be positive."
        )

    return (
        eta
        / (
            np.power(
                theta_array,
                gamma,
            )
            * np.power(
                1.0
                + theta_array,
                1.0
                - gamma,
            )
        )
    )


def ssvi_total_variance(
    log_moneyness: np.ndarray,
    theta: np.ndarray,
    eta: float,
    rho: float,
    gamma: float,
) -> np.ndarray:
    """
    SSVI total variance:

        w(k, theta)
        =
        theta / 2
        [
            1
            + rho phi(theta) k
            + sqrt(
                (
                    phi(theta) k
                    + rho
                )^2
                + 1
                - rho^2
            )
        ]
    """

    if not (
        -1.0
        < rho
        < 1.0
    ):
        raise ValueError(
            "rho must lie in (-1, 1)."
        )

    k = np.asarray(
        log_moneyness,
        dtype=float,
    )

    theta_array = np.asarray(
        theta,
        dtype=float,
    )

    phi = ssvi_phi(
        theta=
            theta_array,

        eta=
            eta,

        gamma=
            gamma,
    )

    inside = (
        np.square(
            phi
            * k
            + rho
        )
        + 1.0
        - rho
        ** 2
    )

    return (
        0.5
        * theta_array
        * (
            1.0
            + rho
            * phi
            * k
            + np.sqrt(
                inside
            )
        )
    )


def _group_quotes_by_maturity(
    quotes: List[
        CalibratedQuote
    ],
) -> Dict[
    float,
    List[
        CalibratedQuote
    ],
]:
    grouped: Dict[
        float,
        List[
            CalibratedQuote
        ],
    ] = {}

    for quote in quotes:
        maturity = round(
            float(
                quote.maturity
            ),
            8,
        )

        grouped.setdefault(
            maturity,
            [],
        ).append(
            quote
        )

    return grouped


def _collapse_duplicate_strikes(
    quotes: List[
        CalibratedQuote
    ],
) -> List[
    Tuple[
        float,
        float,
    ]
]:
    grouped: Dict[
        float,
        List[float],
    ] = {}

    for quote in quotes:
        grouped.setdefault(
            float(
                quote.strike
            ),
            [],
        ).append(
            float(
                quote
                .implied_volatility
            )
        )

    observations: List[
        Tuple[
            float,
            float,
        ]
    ] = []

    for strike in sorted(
        grouped
    ):
        ivs = grouped[
            strike
        ]

        observations.append(
            (
                strike,
                float(
                    np.mean(
                        ivs
                    )
                ),
            )
        )

    return observations


def build_atm_slices(
    quotes: List[
        CalibratedQuote
    ],
    spot: float,
    rate: float,
    dividend_yield: float,
    minimum_strikes: int = 3,
) -> List[
    SSVIAtmSlice
]:
    """
    Estimate ATM total variance theta(T)
    using the observed strike closest to
    the model forward F(T).
    """

    if minimum_strikes < 1:
        raise ValueError(
            "minimum_strikes must be positive."
        )

    grouped = (
        _group_quotes_by_maturity(
            quotes
        )
    )

    slices: List[
        SSVIAtmSlice
    ] = []

    for maturity in sorted(
        grouped
    ):
        observations = (
            _collapse_duplicate_strikes(
                grouped[
                    maturity
                ]
            )
        )

        if (
            len(
                observations
            )
            < minimum_strikes
        ):
            continue

        forward = forward_price(
            spot=
                spot,

            rate=
                rate,

            dividend_yield=
                dividend_yield,

            maturity=
                maturity,
        )

        atm_strike, atm_iv = min(
            observations,
            key=lambda item:
                abs(
                    log(
                        item[0]
                        / forward
                    )
                ),
        )

        theta = (
            atm_iv
            ** 2
            * maturity
        )

        if theta <= 0.0:
            continue

        slices.append(
            SSVIAtmSlice(
                maturity=
                    maturity,

                forward=
                    forward,

                atm_strike=
                    atm_strike,

                atm_implied_volatility=
                    atm_iv,

                theta=
                    theta,
            )
        )

    return slices


def _decode_parameters(
    raw: np.ndarray,
) -> Tuple[
    float,
    float,
    float,
]:
    """
    Transform unconstrained optimisation
    variables into valid SSVI parameters.

    eta   > 0
    |rho| < 1
    gamma in (0, 1)
    """

    eta = float(
        np.exp(
            raw[0]
        )
    )

    rho = float(
        0.999
        * np.tanh(
            raw[1]
        )
    )

    gamma = float(
        1.0
        / (
            1.0
            + np.exp(
                -raw[2]
            )
        )
    )

    return (
        eta,
        rho,
        gamma,
    )


def _build_fit_observations(
    quotes: List[
        CalibratedQuote
    ],
    slices: List[
        SSVIAtmSlice
    ],
) -> Tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    slice_map = {
        round(
            item.maturity,
            8,
        ):
            item
        for item in slices
    }

    k_values: List[
        float
    ] = []

    theta_values: List[
        float
    ] = []

    target_values: List[
        float
    ] = []

    grouped = (
        _group_quotes_by_maturity(
            quotes
        )
    )

    for maturity in sorted(
        slice_map
    ):
        observations = (
            _collapse_duplicate_strikes(
                grouped[
                    maturity
                ]
            )
        )

        atm_slice = (
            slice_map[
                maturity
            ]
        )

        for (
            strike,
            iv,
        ) in observations:
            k = (
                forward_log_moneyness(
                    strike=
                        strike,

                    forward=
                        atm_slice
                        .forward,
                )
            )

            market_total_variance = (
                iv
                ** 2
                * maturity
            )

            if (
                market_total_variance
                <= 0.0
            ):
                continue

            k_values.append(
                k
            )

            theta_values.append(
                atm_slice.theta
            )

            target_values.append(
                market_total_variance
            )

    return (
        np.asarray(
            k_values,
            dtype=float,
        ),

        np.asarray(
            theta_values,
            dtype=float,
        ),

        np.asarray(
            target_values,
            dtype=float,
        ),
    )


def _residuals(
    raw: np.ndarray,
    k: np.ndarray,
    theta: np.ndarray,
    target: np.ndarray,
) -> np.ndarray:
    (
        eta,
        rho,
        gamma,
    ) = (
        _decode_parameters(
            raw
        )
    )

    fitted = (
        ssvi_total_variance(
            log_moneyness=
                k,

            theta=
                theta,

            eta=
                eta,

            rho=
                rho,

            gamma=
                gamma,
        )
    )

    return (
        fitted
        - target
    )


def build_ssvi_arbitrage_diagnostics(
    slices: List[
        SSVIAtmSlice
    ],
    eta: float,
    rho: float,
    gamma: float,
) -> List[
    SSVIArbitrageDiagnostic
]:
    """
    Evaluate commonly used sufficient
    SSVI butterfly bounds numerically.

    These diagnostics are intentionally
    reported as warnings rather than a
    mathematical guarantee that the entire
    surface is arbitrage free.
    """

    diagnostics: List[
        SSVIArbitrageDiagnostic
    ] = []

    for item in slices:
        phi = float(
            ssvi_phi(
                theta=np.asarray(
                    [
                        item.theta
                    ]
                ),

                eta=
                    eta,

                gamma=
                    gamma,
            )[0]
        )

        first_bound = (
            item.theta
            * phi
            * (
                1.0
                + abs(
                    rho
                )
            )
        )

        second_bound = (
            item.theta
            * phi
            ** 2
            * (
                1.0
                + abs(
                    rho
                )
            )
        )

        first_ok = bool(
            first_bound
            < 4.0
        )

        second_ok = bool(
            second_bound
            <= 4.0
        )

        diagnostics.append(
            SSVIArbitrageDiagnostic(
                maturity=
                    item.maturity,

                theta=
                    item.theta,

                phi=
                    phi,

                first_butterfly_bound=
                    first_bound,

                second_butterfly_bound=
                    second_bound,

                first_bound_satisfied=
                    first_ok,

                second_bound_satisfied=
                    second_ok,

                butterfly_warning=
                    not (
                        first_ok
                        and second_ok
                    ),
            )
        )

    return diagnostics


def build_ssvi_calendar_diagnostics(
    slices: List[
        SSVIAtmSlice
    ],
    eta: float,
    rho: float,
    gamma: float,
    grid_points: int = 201,
    tolerance: float = 1e-8,
) -> List[
    SSVICalendarDiagnostic
]:
    """
    Compare adjacent SSVI maturities on a
    common forward-log-moneyness grid.

    For T_long > T_short we require:

        w(k, T_long)
        >=
        w(k, T_short)

    numerically over the comparison grid.
    """

    if grid_points < 2:
        raise ValueError(
            "grid_points must be >= 2."
        )

    ordered = sorted(
        slices,
        key=lambda item:
            item.maturity,
    )

    diagnostics: List[
        SSVICalendarDiagnostic
    ] = []

    common_grid = (
        np.linspace(
            -0.50,
            0.50,
            grid_points,
        )
    )

    for index in range(
        len(
            ordered
        )
        - 1
    ):
        shorter = (
            ordered[
                index
            ]
        )

        longer = (
            ordered[
                index + 1
            ]
        )

        shorter_theta = (
            np.full_like(
                common_grid,
                shorter.theta,
            )
        )

        longer_theta = (
            np.full_like(
                common_grid,
                longer.theta,
            )
        )

        shorter_variance = (
            ssvi_total_variance(
                log_moneyness=
                    common_grid,

                theta=
                    shorter_theta,

                eta=
                    eta,

                rho=
                    rho,

                gamma=
                    gamma,
            )
        )

        longer_variance = (
            ssvi_total_variance(
                log_moneyness=
                    common_grid,

                theta=
                    longer_theta,

                eta=
                    eta,

                rho=
                    rho,

                gamma=
                    gamma,
            )
        )

        difference = (
            longer_variance
            - shorter_variance
        )

        violations = (
            difference
            < -tolerance
        )

        violation_count = int(
            np.sum(
                violations
            )
        )

        diagnostics.append(
            SSVICalendarDiagnostic(
                shorter_maturity=
                    shorter.maturity,

                longer_maturity=
                    longer.maturity,

                minimum_variance_difference=
                    float(
                        np.min(
                            difference
                        )
                    ),

                violation_detected=
                    violation_count
                    > 0,

                violation_count=
                    violation_count,

                comparison_point_count=
                    grid_points,
            )
        )

    return diagnostics


def fit_ssvi_surface(
    quotes: List[
        CalibratedQuote
    ],
    spot: float,
    rate: float,
    dividend_yield: float,
    minimum_strikes: int = 3,
    grid_points_per_maturity: int = 101,
    calendar_grid_points: int = 201,
) -> SSVISurfaceResult:
    """
    Fit one SSVI parameter triplet
    (eta, rho, gamma) across all usable
    maturities.

    ATM total variance theta(T) is estimated
    independently from the observation
    nearest the model forward.
    """

    if spot <= 0.0:
        raise ValueError(
            "spot must be positive."
        )

    if minimum_strikes < 3:
        raise ValueError(
            "minimum_strikes must be >= 3."
        )

    if (
        grid_points_per_maturity
        < 2
    ):
        raise ValueError(
            "grid_points_per_maturity "
            "must be >= 2."
        )

    slices = build_atm_slices(
        quotes=
            quotes,

        spot=
            spot,

        rate=
            rate,

        dividend_yield=
            dividend_yield,

        minimum_strikes=
            minimum_strikes,
    )

    if len(
        slices
    ) < 2:
        raise ValueError(
            "SSVI fitting requires at least "
            "two maturities with sufficient "
            "strike observations."
        )

    (
        k,
        theta,
        target,
    ) = (
        _build_fit_observations(
            quotes=
                quotes,

            slices=
                slices,
        )
    )

    if len(
        target
    ) < 6:
        raise ValueError(
            "SSVI fitting requires at least "
            "six usable observations."
        )

    # Initial:
    #
    # eta   = 1.0
    # rho   = -0.25
    # gamma = 0.5
    initial = np.asarray(
        [
            log(
                1.0
            ),

            np.arctanh(
                -0.25
                / 0.999
            ),

            0.0,
        ],
        dtype=float,
    )

    optimisation = (
        least_squares(
            fun=
                _residuals,

            x0=
                initial,

            args=(
                k,
                theta,
                target,
            ),

            max_nfev=
                5000,

            ftol=
                1e-12,

            xtol=
                1e-12,

            gtol=
                1e-12,
        )
    )

    if not optimisation.success:
        raise ValueError(
            "SSVI optimisation failed: "
            f"{optimisation.message}"
        )

    (
        eta,
        rho,
        gamma,
    ) = (
        _decode_parameters(
            optimisation.x
        )
    )

    fitted_observations = (
        ssvi_total_variance(
            log_moneyness=
                k,

            theta=
                theta,

            eta=
                eta,

            rho=
                rho,

            gamma=
                gamma,
        )
    )

    rmse = float(
        np.sqrt(
            np.mean(
                (
                    fitted_observations
                    - target
                )
                ** 2
            )
        )
    )

    parameters = (
        SSVIParameters(
            eta=
                eta,

            rho=
                rho,

            gamma=
                gamma,

            rmse=
                rmse,

            observation_count=
                int(
                    len(
                        target
                    )
                ),

            maturity_count=
                len(
                    slices
                ),
        )
    )

    grouped = (
        _group_quotes_by_maturity(
            quotes
        )
    )

    points: List[
        SSVIFittedPoint
    ] = []

    slice_map = {
        round(
            item.maturity,
            8,
        ):
            item
        for item in slices
    }

    for maturity in sorted(
        slice_map
    ):
        item = (
            slice_map[
                maturity
            ]
        )

        observations = (
            _collapse_duplicate_strikes(
                grouped[
                    maturity
                ]
            )
        )

        observed_by_strike = {
            float(
                strike
            ):
                float(
                    iv
                )
            for (
                strike,
                iv
            ) in observations
        }

        observed_log_moneyness = [
            forward_log_moneyness(
                strike=
                    strike,

                forward=
                    item.forward,
            )
            for (
                strike,
                _
            ) in observations
        ]

        lower_k = min(
            observed_log_moneyness
        )

        upper_k = max(
            observed_log_moneyness
        )

        k_grid = np.linspace(
            lower_k,
            upper_k,
            grid_points_per_maturity,
        )

        theta_grid = np.full_like(
            k_grid,
            item.theta,
        )

        fitted_variance = (
            ssvi_total_variance(
                log_moneyness=
                    k_grid,

                theta=
                    theta_grid,

                eta=
                    eta,

                rho=
                    rho,

                gamma=
                    gamma,
            )
        )

        for (
            grid_k,
            variance,
        ) in zip(
            k_grid,
            fitted_variance,
        ):
            strike = float(
                item.forward
                * np.exp(
                    grid_k
                )
            )

            fitted_iv = float(
                np.sqrt(
                    max(
                        float(
                            variance
                        ),
                        1e-16,
                    )
                    / maturity
                )
            )

            nearest_strike = min(
                observed_by_strike,
                key=lambda observed_strike:
                    abs(
                        observed_strike
                        - strike
                    ),
            )

            observed_iv = None

            if (
                abs(
                    nearest_strike
                    - strike
                )
                < 1e-8
            ):
                observed_iv = (
                    observed_by_strike[
                        nearest_strike
                    ]
                )

            observed_variance = (
                observed_iv
                ** 2
                * maturity
                if observed_iv
                is not None
                else None
            )

            points.append(
                SSVIFittedPoint(
                    strike=
                        strike,

                    maturity=
                        maturity,

                    forward=
                        item.forward,

                    log_forward_moneyness=
                        float(
                            grid_k
                        ),

                    theta=
                        item.theta,

                    observed_iv=
                        observed_iv,

                    fitted_iv=
                        fitted_iv,

                    observed_total_variance=
                        observed_variance,

                    fitted_total_variance=
                        float(
                            variance
                        ),
                )
            )

    arbitrage_diagnostics = (
        build_ssvi_arbitrage_diagnostics(
            slices=
                slices,

            eta=
                eta,

            rho=
                rho,

            gamma=
                gamma,
        )
    )

    calendar_diagnostics = (
        build_ssvi_calendar_diagnostics(
            slices=
                slices,

            eta=
                eta,

            rho=
                rho,

            gamma=
                gamma,

            grid_points=
                calendar_grid_points,
        )
    )

    butterfly_warning = any(
        item.butterfly_warning
        for item
        in arbitrage_diagnostics
    )

    calendar_warning = any(
        item.violation_detected
        for item
        in calendar_diagnostics
    )

    return (
        SSVISurfaceResult(
            parameters=
                parameters,

            atm_slices=
                slices,

            points=
                points,

            arbitrage_diagnostics=
                arbitrage_diagnostics,

            calendar_diagnostics=
                calendar_diagnostics,

            butterfly_warning=
                butterfly_warning,

            calendar_warning=
                calendar_warning,
        )
    )