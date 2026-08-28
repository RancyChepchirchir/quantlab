from fastapi.testclient import (
    TestClient,
)

from app.main import app


client = TestClient(
    app
)


def arbitrage_payload():
    return {
        "spot": 100.0,
        "rate": 0.0,
        "dividend_yield": 0.0,

        "quotes": [
            {
                "strike": 80.0,
                "maturity": 0.5,
                "market_price": 21.0,
                "option_type": "call",
            },
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
                "strike": 120.0,
                "maturity": 0.5,
                "market_price": 0.9,
                "option_type": "call",
            },

            {
                "strike": 80.0,
                "maturity": 1.0,
                "market_price": 23.0,
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
            {
                "strike": 120.0,
                "maturity": 1.0,
                "market_price": 2.5,
                "option_type": "call",
            },

            {
                "strike": 80.0,
                "maturity": 2.0,
                "market_price": 27.0,
                "option_type": "call",
            },
            {
                "strike": 90.0,
                "maturity": 2.0,
                "market_price": 19.0,
                "option_type": "call",
            },
            {
                "strike": 100.0,
                "maturity": 2.0,
                "market_price": 13.5,
                "option_type": "call",
            },
            {
                "strike": 110.0,
                "maturity": 2.0,
                "market_price": 9.0,
                "option_type": "call",
            },
            {
                "strike": 120.0,
                "maturity": 2.0,
                "market_price": 5.8,
                "option_type": "call",
            },
        ],
    }


def test_api_returns_arbitrage_layers():
    response = client.post(
        "/calibration/volatility-surface",
        json=arbitrage_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    body = response.json()

    assert (
        "arbitrage_layers"
        in body
    )

    assert (
        body[
            "arbitrage_layers"
        ]
        is not None
    )


def test_arbitrage_layers_contains_three_layers():
    response = client.post(
        "/calibration/volatility-surface",
        json=arbitrage_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    layers = (
        response
        .json()[
            "arbitrage_layers"
        ]
    )

    assert set(
        layers.keys()
    ) == {
        "market",
        "svi",
        "ssvi",
    }


def test_arbitrage_layer_names():
    response = client.post(
        "/calibration/volatility-surface",
        json=arbitrage_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    layers = (
        response
        .json()[
            "arbitrage_layers"
        ]
    )

    assert (
        layers[
            "market"
        ][
            "name"
        ]
        == "market"
    )

    assert (
        layers[
            "svi"
        ][
            "name"
        ]
        == "svi"
    )

    assert (
        layers[
            "ssvi"
        ][
            "name"
        ]
        == "ssvi"
    )


def test_each_layer_contains_diagnostics():
    response = client.post(
        "/calibration/volatility-surface",
        json=arbitrage_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    layers = (
        response
        .json()[
            "arbitrage_layers"
        ]
    )

    for layer_name in [
        "market",
        "svi",
        "ssvi",
    ]:
        diagnostics = (
            layers[
                layer_name
            ][
                "diagnostics"
            ]
        )

        assert (
            "calendar_arbitrage_free"
            in diagnostics
        )

        assert (
            "butterfly_arbitrage_free"
            in diagnostics
        )

        assert (
            "arbitrage_free"
            in diagnostics
        )

        assert (
            "calendar_violation_count"
            in diagnostics
        )

        assert (
            "butterfly_violation_count"
            in diagnostics
        )

        assert (
            "total_violation_count"
            in diagnostics
        )

        assert (
            "calendar_violations"
            in diagnostics
        )

        assert (
            "butterfly_violations"
            in diagnostics
        )


def test_arbitrage_counts_are_consistent():
    response = client.post(
        "/calibration/volatility-surface",
        json=arbitrage_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    layers = (
        response
        .json()[
            "arbitrage_layers"
        ]
    )

    for layer_name in [
        "market",
        "svi",
        "ssvi",
    ]:
        diagnostics = (
            layers[
                layer_name
            ][
                "diagnostics"
            ]
        )

        assert (
            diagnostics[
                "total_violation_count"
            ]
            ==
            diagnostics[
                "calendar_violation_count"
            ]
            +
            diagnostics[
                "butterfly_violation_count"
            ]
        )


def test_arbitrage_flags_are_boolean():
    response = client.post(
        "/calibration/volatility-surface",
        json=arbitrage_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    layers = (
        response
        .json()[
            "arbitrage_layers"
        ]
    )

    for layer_name in [
        "market",
        "svi",
        "ssvi",
    ]:
        diagnostics = (
            layers[
                layer_name
            ][
                "diagnostics"
            ]
        )

        assert isinstance(
            diagnostics[
                "calendar_arbitrage_free"
            ],
            bool,
        )

        assert isinstance(
            diagnostics[
                "butterfly_arbitrage_free"
            ],
            bool,
        )

        assert isinstance(
            diagnostics[
                "arbitrage_free"
            ],
            bool,
        )


def test_one_maturity_returns_no_three_layer_comparison():
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
        "/calibration/volatility-surface",
        json=payload,
    )

    assert (
        response.status_code
        == 200
    )

    body = response.json()

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
            "arbitrage_layers"
        ]
        is None
    )