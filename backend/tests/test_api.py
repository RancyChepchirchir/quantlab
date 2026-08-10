from fastapi.testclient import (
    TestClient,
)

from app.main import app


client = TestClient(app)


BASE_REQUEST = {
    "spot": 100,
    "strike": 100,
    "rate": 0.05,
    "volatility": 0.20,
    "maturity": 1.0,
    "dividend_yield": 0.0,
    "option_type": "call",
}


def test_health():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "ok"
    )


def test_black_scholes_endpoint():
    response = client.post(
        "/price/black-scholes",
        json=BASE_REQUEST,
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["method"]
        == "black-scholes"
    )

    assert data["price"] > 0


def test_compare_endpoint():
    response = client.post(
        "/compare",
        json=BASE_REQUEST,
    )

    assert response.status_code == 200

    data = response.json()

    assert "black_scholes" in data
    assert "binomial" in data
    assert "monte_carlo" in data

    assert (
        data["binomial"][
            "absolute_error"
        ]
        < 0.01
    )


def test_invalid_volatility_rejected():
    request = {
        **BASE_REQUEST,
        "volatility": -0.2,
    }

    response = client.post(
        "/price/black-scholes",
        json=request,
    )

    assert response.status_code == 422