from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from app.services.volatility_surface import (
    CalibratedQuote,
)


@dataclass(frozen=True)
class SVIParameters:
    maturity: float

    a: float
    b: float
    rho: float
    m: float
    sigma: float

    rmse: float
    observation_count: int


@dataclass(frozen=True)
class SVIFittedPoint:
    strike: float
    maturity: float
    log_moneyness: float

    observed_iv: Optional[float]
    fitted_iv: float

    total_variance: float


@dataclass(frozen=True)
class SVIArbitrageDiagnostic:
    maturity: float

    minimum_total_variance: float

    negative_variance_detected: bool
    invalid_parameter_region: bool
    butterfly_warning: bool


@dataclass(frozen=True)
class SVICalendarDiagnostic:
    shorter_maturity: float
    longer_maturity: float

    minimum_variance_difference: float

    violation_detected: bool
    violation_count: int

    comparison_point_count: int


@dataclass(frozen=True)
class SVISmileResult:
    parameters: SVIParameters

    points: List[
        SVIFittedPoint
    ]

    arbitrage: SVIArbitrageDiagnostic


@dataclass(frozen=True)
class SVISurfaceResult:
    smiles: List[
        SVISmileResult
    ]

    fitted_maturity_count: int

    calendar_diagnostics: List[
        SVICalendarDiagnostic
    ]

    calendar_warning: bool


def svi_total_variance(
    log_moneyness: np.ndarray,
    a: float,
    b: float,
    rho: float,
    m: float,
    sigma: float,
) -> np.ndarray:
    """
    Raw SVI total-variance parameterisation.

        w(k)
        =
        a
        +
        b [
            rho (k - m)
            +
            sqrt(
                (k - m)^2
                + sigma^2
            )
        ]

    where:

        k = log(K / S)

    and:

        w(k, T) = sigma_IV(k, T)^2 * T
    """

    shifted = (
        log_moneyness
        - m
    )

    return (
        a
        + b
        * (
            rho
            * shifted
            + np.sqrt(
                shifted
                ** 2
                + sigma
                ** 2
            )
        )
    )


def svi_total_variance_from_parameters(
    log_moneyness: np.ndarray,
    parameters: SVIParameters,
) -> np.ndarray:
    """
    Convenience wrapper for evaluating an
    already-fitted SVI smile.
    """

    return svi_total_variance(
        log_moneyness=
            log_moneyness,

        a=
            parameters.a,

        b=
            parameters.b,

        rho=
            parameters.rho,

        m=
            parameters.m,

        sigma=
            parameters.sigma,
    )


def _parameter_valid(
    params: np.ndarray,
) -> bool:
    (
        _,
        b,
        rho,
        _,
        sigma,
    ) = params

    return bool(
        b >= 0.0
        and -0.999
        < rho
        < 0.999
        and sigma > 0.0
    )


def _objective(
    params: np.ndarray,
    x: np.ndarray,
    target: np.ndarray,
) -> float:

    if not _parameter_valid(
        params
    ):
        return float(
            "inf"
        )

    (
        a,
        b,
        rho,
        m,
        sigma,
    ) = params

    predicted = (
        svi_total_variance(
            log_moneyness=x,
            a=a,
            b=b,
            rho=rho,
            m=m,
            sigma=sigma,
        )
    )

    if np.any(
        ~np.isfinite(
            predicted
        )
    ):
        return float(
            "inf"
        )

    if np.any(
        predicted <= 0.0
    ):
        invalid_values = (
            predicted[
                predicted <= 0.0
            ]
        )

        return (
            1e6
            + float(
                np.sum(
                    np.abs(
                        invalid_values
                    )
                )
            )
        )

    error = (
        predicted
        - target
    )

    return float(
        np.mean(
            error
            ** 2
        )
    )


def _initial_parameters(
    x: np.ndarray,
    target: np.ndarray,
) -> np.ndarray:

    minimum_variance = float(
        np.min(
            target
        )
    )

    variance_range = float(
        np.max(
            target
        )
        - minimum_variance
    )

    a = max(
        minimum_variance
        * 0.8,
        1e-8,
    )

    x_range = max(
        float(
            np.ptp(
                x
            )
        ),
        0.05,
    )

    b = max(
        variance_range
        / x_range,
        0.01,
    )

    rho = -0.25

    minimum_index = int(
        np.argmin(
            target
        )
    )

    m = float(
        x[
            minimum_index
        ]
    )

    sigma = max(
        x_range
        / 3.0,
        0.05,
    )

    return np.array(
        [
            a,
            b,
            rho,
            m,
            sigma,
        ],
        dtype=float,
    )


def _coordinate_search(
    initial: np.ndarray,
    x: np.ndarray,
    target: np.ndarray,
    max_iterations: int = 600,
) -> np.ndarray:
    """
    Dependency-light coordinate-search
    optimiser for raw SVI.

    SciPy can replace this later without
    changing the public SVI API.
    """

    current = (
        initial.copy()
    )

    current_loss = (
        _objective(
            current,
            x,
            target,
        )
    )

    steps = np.array(
        [
            max(
                abs(
                    current[0]
                )
                * 0.30,
                0.005,
            ),

            max(
                abs(
                    current[1]
                )
                * 0.30,
                0.01,
            ),

            0.15,

            max(
                float(
                    np.ptp(
                        x
                    )
                )
                * 0.25,
                0.025,
            ),

            max(
                current[4]
                * 0.25,
                0.025,
            ),
        ],
        dtype=float,
    )

    for _ in range(
        max_iterations
    ):
        improved = False

        for index in range(
            len(
                current
            )
        ):
            for direction in (
                -1.0,
                1.0,
            ):
                candidate = (
                    current.copy()
                )

                candidate[
                    index
                ] += (
                    direction
                    * steps[
                        index
                    ]
                )

                candidate_loss = (
                    _objective(
                        candidate,
                        x,
                        target,
                    )
                )

                if (
                    candidate_loss
                    < current_loss
                ):
                    current = (
                        candidate
                    )

                    current_loss = (
                        candidate_loss
                    )

                    improved = True

        if not improved:
            steps *= 0.65

        if (
            float(
                np.max(
                    steps
                )
            )
            < 1e-7
        ):
            break

    return current


def fit_svi_smile(
    quotes: List[
        CalibratedQuote
    ],
    spot: float,
    maturity: float,
    grid_points: int = 51,
) -> SVISmileResult:

    if spot <= 0:
        raise ValueError(
            "spot must be positive."
        )

    if maturity <= 0:
        raise ValueError(
            "maturity must be positive."
        )

    if grid_points < 2:
        raise ValueError(
            "grid_points must be >= 2."
        )

    maturity_quotes = [
        quote
        for quote
        in quotes
        if abs(
            quote.maturity
            - maturity
        )
        < 1e-8
    ]

    # -------------------------------------------------
    # Collapse call/put observations at identical K,T.
    # -------------------------------------------------

    grouped: Dict[
        float,
        List[float],
    ] = {}

    for quote in (
        maturity_quotes
    ):
        grouped.setdefault(
            quote.strike,
            [],
        ).append(
            quote
            .implied_volatility
        )

    observations: List[
        Tuple[
            float,
            float,
        ]
    ] = []

    for (
        strike,
        ivs,
    ) in sorted(
        grouped.items()
    ):
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

    if len(
        observations
    ) < 3:
        raise ValueError(
            "SVI fitting requires "
            "at least 3 distinct strikes "
            "for a maturity."
        )

    strikes = np.array(
        [
            item[0]
            for item
            in observations
        ],
        dtype=float,
    )

    observed_iv = np.array(
        [
            item[1]
            for item
            in observations
        ],
        dtype=float,
    )

    if np.any(
        observed_iv <= 0.0
    ):
        raise ValueError(
            "Observed implied volatility "
            "must be positive."
        )

    # -------------------------------------------------
    # Log-moneyness + total implied variance
    # -------------------------------------------------

    x = np.log(
        strikes
        / spot
    )

    target_variance = (
        observed_iv
        ** 2
        * maturity
    )

    # -------------------------------------------------
    # Fit raw SVI
    # -------------------------------------------------

    initial = (
        _initial_parameters(
            x,
            target_variance,
        )
    )

    fitted = (
        _coordinate_search(
            initial,
            x,
            target_variance,
        )
    )

    (
        a,
        b,
        rho,
        m,
        sigma,
    ) = [
        float(
            value
        )
        for value
        in fitted
    ]

    fitted_at_observations = (
        svi_total_variance(
            log_moneyness=x,
            a=a,
            b=b,
            rho=rho,
            m=m,
            sigma=sigma,
        )
    )

    rmse = float(
        np.sqrt(
            np.mean(
                (
                    fitted_at_observations
                    - target_variance
                )
                ** 2
            )
        )
    )

    # -------------------------------------------------
    # Dense smile grid
    # -------------------------------------------------

    log_grid = np.linspace(
        float(
            np.min(
                x
            )
        ),
        float(
            np.max(
                x
            )
        ),
        grid_points,
    )

    variance_grid = (
        svi_total_variance(
            log_moneyness=
                log_grid,

            a=
                a,

            b=
                b,

            rho=
                rho,

            m=
                m,

            sigma=
                sigma,
        )
    )

    points: List[
        SVIFittedPoint
    ] = []

    for (
        log_moneyness,
        total_variance,
    ) in zip(
        log_grid,
        variance_grid,
    ):
        positive_variance = max(
            float(
                total_variance
            ),
            1e-12,
        )

        fitted_iv = float(
            np.sqrt(
                positive_variance
                / maturity
            )
        )

        strike = float(
            spot
            * np.exp(
                log_moneyness
            )
        )

        observed = None

        nearest = int(
            np.argmin(
                np.abs(
                    strikes
                    - strike
                )
            )
        )

        if (
            abs(
                strikes[
                    nearest
                ]
                - strike
            )
            < 1e-8
        ):
            observed = float(
                observed_iv[
                    nearest
                ]
            )

        points.append(
            SVIFittedPoint(
                strike=
                    strike,

                maturity=
                    maturity,

                log_moneyness=
                    float(
                        log_moneyness
                    ),

                observed_iv=
                    observed,

                fitted_iv=
                    fitted_iv,

                total_variance=
                    positive_variance,
            )
        )

    # -------------------------------------------------
    # Within-smile diagnostics
    # -------------------------------------------------

    minimum_total_variance = float(
        np.min(
            variance_grid
        )
    )

    negative_variance_detected = bool(
        np.any(
            variance_grid <= 0.0
        )
    )

    invalid_parameter_region = bool(
        b < 0.0
        or abs(
            rho
        )
        >= 1.0
        or sigma <= 0.0
    )

    # This is a basic SVI wing warning.
    # It is NOT a complete analytical proof
    # of butterfly-arbitrage freedom.
    butterfly_warning = bool(
        invalid_parameter_region
        or negative_variance_detected
        or (
            b
            * (
                1.0
                + abs(
                    rho
                )
            )
            > 4.0
        )
    )

    parameters = (
        SVIParameters(
            maturity=
                maturity,

            a=
                a,

            b=
                b,

            rho=
                rho,

            m=
                m,

            sigma=
                sigma,

            rmse=
                rmse,

            observation_count=
                len(
                    observations
                ),
        )
    )

    arbitrage = (
        SVIArbitrageDiagnostic(
            maturity=
                maturity,

            minimum_total_variance=
                minimum_total_variance,

            negative_variance_detected=
                negative_variance_detected,

            invalid_parameter_region=
                invalid_parameter_region,

            butterfly_warning=
                butterfly_warning,
        )
    )

    return SVISmileResult(
        parameters=
            parameters,

        points=
            points,

        arbitrage=
            arbitrage,
    )


def build_calendar_diagnostics(
    smiles: List[
        SVISmileResult
    ],
    grid_points: int = 101,
    tolerance: float = 1e-8,
) -> List[
    SVICalendarDiagnostic
]:
    """
    Check adjacent fitted maturities for
    decreasing total implied variance.

    For calendar-arbitrage-free surfaces,
    total variance should not decrease
    as maturity increases at a common
    log-moneyness:

        w(k, T_long) >= w(k, T_short)

    This numerical diagnostic evaluates
    fitted adjacent SVI smiles on their
    overlapping log-moneyness domain.
    """

    if grid_points < 2:
        raise ValueError(
            "grid_points must be >= 2."
        )

    ordered = sorted(
        smiles,
        key=lambda smile:
            smile
            .parameters
            .maturity,
    )

    diagnostics: List[
        SVICalendarDiagnostic
    ] = []

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

        shorter_k = np.array(
            [
                point.log_moneyness
                for point
                in shorter.points
            ],
            dtype=float,
        )

        longer_k = np.array(
            [
                point.log_moneyness
                for point
                in longer.points
            ],
            dtype=float,
        )

        lower_bound = max(
            float(
                np.min(
                    shorter_k
                )
            ),
            float(
                np.min(
                    longer_k
                )
            ),
        )

        upper_bound = min(
            float(
                np.max(
                    shorter_k
                )
            ),
            float(
                np.max(
                    longer_k
                )
            ),
        )

        if (
            upper_bound
            < lower_bound
        ):
            # No common domain exists.
            # We cannot make a meaningful
            # calendar comparison.
            continue

        common_grid = np.linspace(
            lower_bound,
            upper_bound,
            grid_points,
        )

        shorter_variance = (
            svi_total_variance_from_parameters(
                common_grid,
                shorter.parameters,
            )
        )

        longer_variance = (
            svi_total_variance_from_parameters(
                common_grid,
                longer.parameters,
            )
        )

        variance_difference = (
            longer_variance
            - shorter_variance
        )

        violations = (
            variance_difference
            < -tolerance
        )

        violation_count = int(
            np.sum(
                violations
            )
        )

        minimum_difference = float(
            np.min(
                variance_difference
            )
        )

        diagnostics.append(
            SVICalendarDiagnostic(
                shorter_maturity=
                    shorter
                    .parameters
                    .maturity,

                longer_maturity=
                    longer
                    .parameters
                    .maturity,

                minimum_variance_difference=
                    minimum_difference,

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


def fit_svi_surface(
    quotes: List[
        CalibratedQuote
    ],
    spot: float,
    minimum_strikes: int = 3,
    grid_points: int = 51,
    calendar_grid_points: int = 101,
) -> SVISurfaceResult:

    if spot <= 0:
        raise ValueError(
            "spot must be positive."
        )

    if minimum_strikes < 3:
        raise ValueError(
            "minimum_strikes must be >= 3."
        )

    if grid_points < 2:
        raise ValueError(
            "grid_points must be >= 2."
        )

    if calendar_grid_points < 2:
        raise ValueError(
            "calendar_grid_points "
            "must be >= 2."
        )

    maturity_groups: Dict[
        float,
        Set[float],
    ] = {}

    for quote in quotes:
        key = round(
            quote.maturity,
            8,
        )

        maturity_groups.setdefault(
            key,
            set(),
        ).add(
            quote.strike
        )

    smiles: List[
        SVISmileResult
    ] = []

    for maturity in sorted(
        maturity_groups
    ):
        strike_count = len(
            maturity_groups[
                maturity
            ]
        )

        if (
            strike_count
            < minimum_strikes
        ):
            continue

        smiles.append(
            fit_svi_smile(
                quotes=
                    quotes,

                spot=
                    spot,

                maturity=
                    maturity,

                grid_points=
                    grid_points,
            )
        )

    calendar_diagnostics = (
        build_calendar_diagnostics(
            smiles=
                smiles,

            grid_points=
                calendar_grid_points,
        )
    )

    calendar_warning = any(
        diagnostic
        .violation_detected
        for diagnostic
        in calendar_diagnostics
    )

    return SVISurfaceResult(
        smiles=
            smiles,

        fitted_maturity_count=
            len(
                smiles
            ),

        calendar_diagnostics=
            calendar_diagnostics,

        calendar_warning=
            calendar_warning,
    )