#!/usr/bin/env python3

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

from typing import (
    Any,
    Dict,
    Optional,
)


DEFAULT_TIMEOUT = 30.0


class SmokeTestFailure(
    RuntimeError
):
    pass


def heading(
    title: str,
) -> None:
    print()
    print(
        "=" * 72
    )
    print(
        title
    )
    print(
        "=" * 72
    )


def success(
    message: str,
) -> None:
    print(
        f"✓ {message}"
    )


def failure(
    message: str,
) -> None:
    print(
        f"✗ {message}"
    )


def info(
    message: str,
) -> None:
    print(
        f"  {message}"
    )


def normalize_url(
    url: str,
) -> str:
    return (
        url
        .strip()
        .rstrip("/")
    )


def request_json(
    url: str,
    method: str = "GET",
    payload: Optional[
        Dict[str, Any]
    ] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:

    data = None

    headers = {
        "Accept":
            "application/json",
    }

    if payload is not None:
        data = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

        headers[
            "Content-Type"
        ] = (
            "application/json"
        )

    request = (
        urllib.request.Request(
            url=url,
            data=data,
            headers=headers,
            method=method,
        )
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            status = (
                response.status
            )

            raw = (
                response
                .read()
                .decode(
                    "utf-8"
                )
            )

    except urllib.error.HTTPError as error:
        raw = (
            error
            .read()
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        raise SmokeTestFailure(
            f"{method} {url} "
            f"returned HTTP "
            f"{error.code}: {raw}"
        ) from error

    except urllib.error.URLError as error:
        raise SmokeTestFailure(
            f"{method} {url} failed: "
            f"{error.reason}"
        ) from error

    if (
        status < 200
        or status >= 300
    ):
        raise SmokeTestFailure(
            f"{method} {url} "
            f"returned HTTP {status}."
        )

    try:
        payload_json = (
            json.loads(
                raw
            )
        )

    except json.JSONDecodeError as error:
        raise SmokeTestFailure(
            f"{method} {url} "
            "did not return valid JSON."
        ) from error

    if not isinstance(
        payload_json,
        dict,
    ):
        raise SmokeTestFailure(
            f"{method} {url} "
            "returned JSON that was "
            "not an object."
        )

    return payload_json


def request_text(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:

    request = (
        urllib.request.Request(
            url=url,
            method="GET",
            headers={
                "Accept":
                    "text/html,"
                    "application/xhtml+xml",
            },
        )
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            status = (
                response.status
            )

            body = (
                response
                .read()
                .decode(
                    "utf-8",
                    errors="replace",
                )
            )

    except urllib.error.HTTPError as error:
        raise SmokeTestFailure(
            f"GET {url} returned "
            f"HTTP {error.code}."
        ) from error

    except urllib.error.URLError as error:
        raise SmokeTestFailure(
            f"GET {url} failed: "
            f"{error.reason}"
        ) from error

    if (
        status < 200
        or status >= 400
    ):
        raise SmokeTestFailure(
            f"GET {url} returned "
            f"HTTP {status}."
        )

    return body


def require_fields(
    payload: Dict[
        str,
        Any,
    ],
    fields,
    context: str,
) -> None:

    missing = [
        field
        for field in fields
        if field not in payload
    ]

    if missing:
        raise SmokeTestFailure(
            f"{context} is missing "
            f"required fields: "
            f"{missing}"
        )


def test_backend_health(
    backend_url: str,
    timeout: float,
) -> None:
    """
    Use FastAPI's OpenAPI document as a
    framework-level health check.

    QuantLab intentionally does not require
    a GET / route.
    """

    heading(
        "1. Backend health"
    )

    url = (
        f"{backend_url}"
        "/openapi.json"
    )

    started = (
        time.perf_counter()
    )

    payload = (
        request_json(
            url=url,
            timeout=timeout,
        )
    )

    elapsed = (
        time.perf_counter()
        - started
    )

    require_fields(
        payload,
        [
            "openapi",
            "info",
            "paths",
        ],
        "FastAPI OpenAPI response",
    )

    paths = (
        payload.get(
            "paths"
        )
    )

    if not isinstance(
        paths,
        dict,
    ):
        raise SmokeTestFailure(
            "OpenAPI paths field "
            "is invalid."
        )

    required_paths = [
        (
            "/market-data/"
            "options/{symbol}"
        ),
        (
            "/calibration/"
            "volatility-surface"
        ),
    ]

    missing_paths = [
        path
        for path
        in required_paths
        if path not in paths
    ]

    if missing_paths:
        raise SmokeTestFailure(
            "Required QuantLab API "
            "routes are missing: "
            f"{missing_paths}"
        )

    success(
        "FastAPI is reachable."
    )

    info(
        f"OpenAPI version: "
        f"{payload.get('openapi')}"
    )

    info(
        f"Registered paths: "
        f"{len(paths)}"
    )

    info(
        f"Latency: "
        f"{elapsed:.3f}s"
    )


def test_mock_market_data(
    backend_url: str,
    timeout: float,
) -> None:

    heading(
        "2. Mock market-data endpoint"
    )

    url = (
        f"{backend_url}"
        "/market-data/options/SPY"
        "?provider=mock"
        "&refresh=true"
    )

    started = (
        time.perf_counter()
    )

    payload = (
        request_json(
            url=url,
            timeout=timeout,
        )
    )

    elapsed = (
        time.perf_counter()
        - started
    )

    require_fields(
        payload,
        [
            "symbol",
            "spot",
            "expiries",
            "quotes",
            "source",
            "cache_hit",
            "cache_ttl_seconds",
        ],
        "Mock option-chain response",
    )

    if (
        payload[
            "symbol"
        ]
        != "SPY"
    ):
        raise SmokeTestFailure(
            "Mock market-data endpoint "
            "returned the wrong symbol."
        )

    quotes = (
        payload[
            "quotes"
        ]
    )

    if (
        not isinstance(
            quotes,
            list,
        )
        or len(
            quotes
        ) == 0
    ):
        raise SmokeTestFailure(
            "Mock option chain contains "
            "no quotes."
        )

    success(
        "Mock option chain loaded."
    )

    info(
        f"Quotes: "
        f"{len(quotes)}"
    )

    info(
        f"Source: "
        f"{payload['source']}"
    )

    info(
        f"Latency: "
        f"{elapsed:.3f}s"
    )


def test_option_chain_cache(
    backend_url: str,
    timeout: float,
) -> None:

    heading(
        "3. Service-level option-chain cache"
    )

    # First normal request populates
    # service-level cache.
    url = (
        f"{backend_url}"
        "/market-data/options/SPY"
        "?provider=mock"
    )

    first = (
        request_json(
            url=url,
            timeout=timeout,
        )
    )

    second = (
        request_json(
            url=url,
            timeout=timeout,
        )
    )

    if not second.get(
        "cache_hit",
        False,
    ):
        raise SmokeTestFailure(
            "Repeated mock request did "
            "not produce a cache hit."
        )

    age = (
        second.get(
            "cache_age_seconds"
        )
    )

    ttl = (
        second.get(
            "cache_ttl_seconds"
        )
    )

    success(
        "Option-chain cache is active."
    )

    info(
        "First request cache hit: "
        f"{first.get('cache_hit')}"
    )

    info(
        f"Second request cache hit: "
        f"{second.get('cache_hit')}"
    )

    info(
        f"Cache age: {age}"
    )

    info(
        f"Cache TTL: {ttl}"
    )


def calibration_payload() -> Dict[
    str,
    Any,
]:
    return {
        "spot":
            100.0,

        "rate":
            0.05,

        "dividend_yield":
            0.0,

        "quotes": [
            {
                "strike":
                    90.0,

                "maturity":
                    0.5,

                "market_price":
                    13.50,

                "option_type":
                    "call",
            },

            {
                "strike":
                    100.0,

                "maturity":
                    0.5,

                "market_price":
                    6.90,

                "option_type":
                    "call",
            },

            {
                "strike":
                    110.0,

                "maturity":
                    0.5,

                "market_price":
                    2.90,

                "option_type":
                    "call",
            },

            {
                "strike":
                    90.0,

                "maturity":
                    1.0,

                "market_price":
                    17.10,

                "option_type":
                    "call",
            },

            {
                "strike":
                    100.0,

                "maturity":
                    1.0,

                "market_price":
                    10.80,

                "option_type":
                    "call",
            },

            {
                "strike":
                    110.0,

                "maturity":
                    1.0,

                "market_price":
                    6.30,

                "option_type":
                    "call",
            },
        ],
    }


def get_calibration_result(
    backend_url: str,
    timeout: float,
) -> Dict[str, Any]:

    url = (
        f"{backend_url}"
        "/calibration/"
        "volatility-surface"
    )

    return (
        request_json(
            url=url,
            method="POST",
            payload=(
                calibration_payload()
            ),
            timeout=timeout,
        )
    )


def test_volatility_calibration(
    backend_url: str,
    timeout: float,
) -> None:

    heading(
        "4. Volatility calibration"
    )

    started = (
        time.perf_counter()
    )

    payload = (
        get_calibration_result(
            backend_url,
            timeout,
        )
    )

    elapsed = (
        time.perf_counter()
        - started
    )

    require_fields(
        payload,
        [
            "quote_count",
            "calibrated_count",
            "rejected_count",
            "success_rate",
            "quotes",
            "diagnostics",
            "surface_grid",
            "svi",
        ],
        "Volatility calibration response",
    )

    if (
        payload[
            "calibrated_count"
        ]
        <= 0
    ):
        raise SmokeTestFailure(
            "No quotes were calibrated."
        )

    if (
        payload[
            "success_rate"
        ]
        <= 0
    ):
        raise SmokeTestFailure(
            "Volatility calibration "
            "success rate is zero."
        )

    success(
        "Volatility calibration works."
    )

    info(
        "Calibrated quotes: "
        f"{payload['calibrated_count']}"
    )

    info(
        "Rejected quotes: "
        f"{payload['rejected_count']}"
    )

    info(
        "Success rate: "
        f"{payload['success_rate']:.2%}"
    )

    info(
        f"Latency: "
        f"{elapsed:.3f}s"
    )


def test_svi(
    backend_url: str,
    timeout: float,
) -> None:

    heading(
        "5. SVI surface"
    )

    payload = (
        get_calibration_result(
            backend_url,
            timeout,
        )
    )

    svi = (
        payload.get(
            "svi"
        )
    )

    if not isinstance(
        svi,
        dict,
    ):
        raise SmokeTestFailure(
            "SVI response is missing."
        )

    require_fields(
        svi,
        [
            "fitted_maturity_count",
            "calendar_warning",
            "calendar_diagnostics",
            "smiles",
        ],
        "SVI response",
    )

    if (
        svi[
            "fitted_maturity_count"
        ]
        < 2
    ):
        raise SmokeTestFailure(
            "Expected two fitted SVI "
            "maturities."
        )

    smiles = (
        svi[
            "smiles"
        ]
    )

    if (
        not isinstance(
            smiles,
            list,
        )
        or len(
            smiles
        ) < 2
    ):
        raise SmokeTestFailure(
            "SVI smile data is incomplete."
        )

    diagnostics = (
        svi[
            "calendar_diagnostics"
        ]
    )

    if (
        not isinstance(
            diagnostics,
            list,
        )
        or len(
            diagnostics
        ) < 1
    ):
        raise SmokeTestFailure(
            "Expected a cross-maturity "
            "calendar diagnostic."
        )

    success(
        "SVI fitting works."
    )

    info(
        "Fitted maturities: "
        f"{svi['fitted_maturity_count']}"
    )

    info(
        "Calendar warning: "
        f"{svi['calendar_warning']}"
    )

    info(
        "Calendar comparisons: "
        f"{len(diagnostics)}"
    )


def test_idw_surface(
    backend_url: str,
    timeout: float,
) -> None:

    heading(
        "6. IDW surface"
    )

    payload = (
        get_calibration_result(
            backend_url,
            timeout,
        )
    )

    surface = (
        payload.get(
            "surface_grid"
        )
    )

    if not isinstance(
        surface,
        dict,
    ):
        raise SmokeTestFailure(
            "Surface grid is missing."
        )

    require_fields(
        surface,
        [
            "strikes",
            "maturities",
            "points",
            "observed_strike_count",
            "observed_maturity_count",
            "is_two_dimensional",
        ],
        "IDW surface response",
    )

    if not surface[
        "is_two_dimensional"
    ]:
        raise SmokeTestFailure(
            "Expected the smoke-test "
            "surface to be two-dimensional."
        )

    points = (
        surface[
            "points"
        ]
    )

    if (
        not isinstance(
            points,
            list,
        )
        or len(
            points
        ) == 0
    ):
        raise SmokeTestFailure(
            "IDW surface contains "
            "no grid points."
        )

    success(
        "IDW surface works."
    )

    info(
        "Observed strikes: "
        f"{surface['observed_strike_count']}"
    )

    info(
        "Observed maturities: "
        f"{surface['observed_maturity_count']}"
    )

    info(
        "Grid points: "
        f"{len(points)}"
    )


def test_frontend(
    frontend_url: str,
    timeout: float,
) -> None:

    heading(
        "7. Frontend reachability"
    )

    volatility_url = (
        f"{frontend_url}"
        "/volatility-lab"
    )

    started = (
        time.perf_counter()
    )

    body = (
        request_text(
            volatility_url,
            timeout=timeout,
        )
    )

    elapsed = (
        time.perf_counter()
        - started
    )

    if (
        len(
            body
        )
        < 100
    ):
        raise SmokeTestFailure(
            "Frontend returned an "
            "unexpectedly small response."
        )

    success(
        "Volatility Lab frontend responded."
    )

    info(
        f"Latency: "
        f"{elapsed:.3f}s"
    )


def run(
    backend_url: str,
    frontend_url: Optional[
        str
    ],
    timeout: float,
) -> None:

    backend_url = (
        normalize_url(
            backend_url
        )
    )

    if frontend_url:
        frontend_url = (
            normalize_url(
                frontend_url
            )
        )

    heading(
        "QuantLab Production Smoke Test"
    )

    info(
        f"Backend: {backend_url}"
    )

    if frontend_url:
        info(
            f"Frontend: {frontend_url}"
        )

    started = (
        time.perf_counter()
    )

    tests = [
        (
            "Backend health",
            lambda:
                test_backend_health(
                    backend_url,
                    timeout,
                ),
        ),

        (
            "Mock market data",
            lambda:
                test_mock_market_data(
                    backend_url,
                    timeout,
                ),
        ),

        (
            "Market-data cache",
            lambda:
                test_option_chain_cache(
                    backend_url,
                    timeout,
                ),
        ),

        (
            "Volatility calibration",
            lambda:
                test_volatility_calibration(
                    backend_url,
                    timeout,
                ),
        ),

        (
            "SVI",
            lambda:
                test_svi(
                    backend_url,
                    timeout,
                ),
        ),

        (
            "IDW surface",
            lambda:
                test_idw_surface(
                    backend_url,
                    timeout,
                ),
        ),
    ]

    if frontend_url:
        tests.append(
            (
                "Frontend",
                lambda:
                    test_frontend(
                        frontend_url,
                        timeout,
                    ),
            )
        )

    passed = 0

    for (
        name,
        test,
    ) in tests:
        try:
            test()

        except Exception as error:
            failure(
                name
            )

            print()
            print(
                str(
                    error
                )
            )

            print()
            print(
                "SMOKE TEST FAILED"
            )

            raise SystemExit(
                1
            ) from error

        passed += 1

    elapsed = (
        time.perf_counter()
        - started
    )

    heading(
        "Smoke Test Summary"
    )

    success(
        f"{passed}/{len(tests)} "
        "checks passed."
    )

    info(
        f"Total runtime: "
        f"{elapsed:.2f}s"
    )

    print()
    print(
        "QUANTLAB RELEASE HEALTHY"
    )


def parse_args():
    parser = (
        argparse.ArgumentParser(
            description=(
                "QuantLab deployment "
                "smoke tests."
            )
        )
    )

    parser.add_argument(
        "--backend",
        required=True,
        help=(
            "QuantLab backend "
            "base URL."
        ),
    )

    parser.add_argument(
        "--frontend",
        required=False,
        default=None,
        help=(
            "Optional QuantLab frontend "
            "base URL."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=(
            "HTTP timeout in seconds."
        ),
    )

    return (
        parser.parse_args()
    )


if __name__ == "__main__":
    arguments = (
        parse_args()
    )

    try:
        run(
            backend_url=(
                arguments.backend
            ),

            frontend_url=(
                arguments.frontend
            ),

            timeout=(
                arguments.timeout
            ),
        )

    except KeyboardInterrupt:
        print()

        failure(
            "Interrupted."
        )

        sys.exit(
            130
        )