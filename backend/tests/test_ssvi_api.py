from fastapi.testclient import (
    TestClient,
)

from app.main import app


client = TestClient(
    app
)


def test_surface_response_contains_ssvi():
    payload = {
        "spot": 100.0,
        "rate": 0.0,
        "dividend_yield": 0.0,

        "quotes": [
            {
                "strike": 90.0,
                "maturity": 0.5,
                "market_price": 12.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 0.5,
                "market_price": 6.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 0.5,
                "market_price": 2.5,
                "option_type": "call",
            },

            {
                "strike": 90.0,
                "maturity": 1.0,
                "market_price": 14.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 1.0,
                "market_price": 9.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 1.0,
                "market_price": 5.0,
                "option_type": "call",
            },
        ],
    }

    response = client.post(
        (
            "/calibration/"
            "volatility-surface"
        ),
        json=payload,
    )

    assert (
        response.status_code
        == 200
    )

    body = (
        response.json()
    )

    assert (
        "ssvi"
        in body
    )

    ssvi = (
        body[
            "ssvi"
        ]
    )

    assert (
        ssvi[
            "available"
        ]
        is True
    )

    assert (
        ssvi[
            "parameters"
        ]
        is not None
    )

    parameters = (
        ssvi[
            "parameters"
        ]
    )

    assert (
        parameters[
            "eta"
        ]
        > 0.0
    )

    assert (
        -1.0
        < parameters[
            "rho"
        ]
        < 1.0
    )

    assert (
        0.0
        < parameters[
            "gamma"
        ]
        < 1.0
    )

    assert (
        parameters[
            "maturity_count"
        ]
        == 2
    )

    assert (
        parameters[
            "observation_count"
        ]
        >= 6
    )


def test_ssvi_response_contains_atm_slices():
    payload = {
        "spot": 100.0,
        "rate": 0.0,
        "dividend_yield": 0.0,

        "quotes": [
            {
                "strike": 90.0,
                "maturity": 0.5,
                "market_price": 12.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 0.5,
                "market_price": 6.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 0.5,
                "market_price": 2.5,
                "option_type": "call",
            },

            {
                "strike": 90.0,
                "maturity": 1.0,
                "market_price": 14.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 1.0,
                "market_price": 9.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 1.0,
                "market_price": 5.0,
                "option_type": "call",
            },
        ],
    }

    response = client.post(
        (
            "/calibration/"
            "volatility-surface"
        ),
        json=payload,
    )

    assert (
        response.status_code
        == 200
    )

    ssvi = (
        response
        .json()[
            "ssvi"
        ]
    )

    assert (
        ssvi[
            "available"
        ]
        is True
    )

    assert (
        len(
            ssvi[
                "atm_slices"
            ]
        )
        == 2
    )

    for item in (
        ssvi[
            "atm_slices"
        ]
    ):
        assert (
            item[
                "maturity"
            ]
            > 0.0
        )

        assert (
            item[
                "forward"
            ]
            > 0.0
        )

        assert (
            item[
                "theta"
            ]
            > 0.0
        )


def test_ssvi_response_contains_fitted_points():
    payload = {
        "spot": 100.0,
        "rate": 0.0,
        "dividend_yield": 0.0,

        "quotes": [
            {
                "strike": 90.0,
                "maturity": 0.5,
                "market_price": 12.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 0.5,
                "market_price": 6.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 0.5,
                "market_price": 2.5,
                "option_type": "call",
            },

            {
                "strike": 90.0,
                "maturity": 1.0,
                "market_price": 14.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 1.0,
                "market_price": 9.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 1.0,
                "market_price": 5.0,
                "option_type": "call",
            },
        ],
    }

    response = client.post(
        (
            "/calibration/"
            "volatility-surface"
        ),
        json=payload,
    )

    assert (
        response.status_code
        == 200
    )

    ssvi = (
        response
        .json()[
            "ssvi"
        ]
    )

    assert (
        ssvi[
            "available"
        ]
        is True
    )

    points = (
        ssvi[
            "points"
        ]
    )

    assert (
        len(
            points
        )
        > 0
    )

    for point in points:
        assert (
            point[
                "strike"
            ]
            > 0.0
        )

        assert (
            point[
                "maturity"
            ]
            > 0.0
        )

        assert (
            point[
                "forward"
            ]
            > 0.0
        )

        assert (
            point[
                "fitted_iv"
            ]
            > 0.0
        )

        assert (
            point[
                "fitted_total_variance"
            ]
            > 0.0
        )


def test_ssvi_response_contains_arbitrage_diagnostics():
    payload = {
        "spot": 100.0,
        "rate": 0.0,
        "dividend_yield": 0.0,

        "quotes": [
            {
                "strike": 90.0,
                "maturity": 0.5,
                "market_price": 12.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 0.5,
                "market_price": 6.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 0.5,
                "market_price": 2.5,
                "option_type": "call",
            },

            {
                "strike": 90.0,
                "maturity": 1.0,
                "market_price": 14.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 1.0,
                "market_price": 9.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 1.0,
                "market_price": 5.0,
                "option_type": "call",
            },
        ],
    }

    response = client.post(
        (
            "/calibration/"
            "volatility-surface"
        ),
        json=payload,
    )

    assert (
        response.status_code
        == 200
    )

    ssvi = (
        response
        .json()[
            "ssvi"
        ]
    )

    diagnostics = (
        ssvi[
            "arbitrage_diagnostics"
        ]
    )

    assert (
        len(
            diagnostics
        )
        == 2
    )

    for diagnostic in (
        diagnostics
    ):
        assert (
            "butterfly_warning"
            in diagnostic
        )

        assert (
            "first_bound_satisfied"
            in diagnostic
        )

        assert (
            "second_bound_satisfied"
            in diagnostic
        )


def test_ssvi_response_contains_calendar_diagnostics():
    payload = {
        "spot": 100.0,
        "rate": 0.0,
        "dividend_yield": 0.0,

        "quotes": [
            {
                "strike": 90.0,
                "maturity": 0.5,
                "market_price": 12.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 0.5,
                "market_price": 6.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 0.5,
                "market_price": 2.5,
                "option_type": "call",
            },

            {
                "strike": 90.0,
                "maturity": 1.0,
                "market_price": 14.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 1.0,
                "market_price": 9.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 1.0,
                "market_price": 5.0,
                "option_type": "call",
            },
        ],
    }

    response = client.post(
        (
            "/calibration/"
            "volatility-surface"
        ),
        json=payload,
    )

    assert (
        response.status_code
        == 200
    )

    ssvi = (
        response
        .json()[
            "ssvi"
        ]
    )

    diagnostics = (
        ssvi[
            "calendar_diagnostics"
        ]
    )

    assert (
        len(
            diagnostics
        )
        == 1
    )

    diagnostic = (
        diagnostics[
            0
        ]
    )

    assert (
        diagnostic[
            "shorter_maturity"
        ]
        < diagnostic[
            "longer_maturity"
        ]
    )

    assert (
        diagnostic[
            "comparison_point_count"
        ]
        == 201
    )

    assert isinstance(
        diagnostic[
            "violation_detected"
        ],
        bool,
    )


def test_ssvi_unavailable_does_not_fail_surface():
    payload = {
        "spot": 100.0,
        "rate": 0.0,
        "dividend_yield": 0.0,

        "quotes": [
            {
                "strike": 90.0,
                "maturity": 1.0,
                "market_price": 14.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 1.0,
                "market_price": 9.0,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 1.0,
                "market_price": 5.0,
                "option_type": "call",
            },
        ],
    }

    response = client.post(
        (
            "/calibration/"
            "volatility-surface"
        ),
        json=payload,
    )

    # Ordinary IV + raw SVI calibration
    # must remain usable.
    assert (
        response.status_code
        == 200
    )

    body = (
        response.json()
    )

    assert (
        "ssvi"
        in body
    )

    assert (
        body[
            "ssvi"
        ][
            "available"
        ]
        is False
    )

    assert (
        body[
            "ssvi"
        ][
            "message"
        ]
        is not None
    )