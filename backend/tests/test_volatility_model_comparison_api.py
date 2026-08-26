from fastapi.testclient import (
    TestClient,
)

from app.main import app


client = TestClient(
    app
)


def comparison_payload():
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


def test_api_returns_model_comparison():
    response = client.post(
        "/calibration/volatility-surface",
        json=comparison_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    body = response.json()

    assert (
        "model_comparison"
        in body
    )

    assert (
        body[
            "model_comparison"
        ]
        is not None
    )


def test_model_comparison_contains_both_models():
    response = client.post(
        "/calibration/volatility-surface",
        json=comparison_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    comparison = (
        response
        .json()[
            "model_comparison"
        ]
    )

    assert (
        "svi"
        in comparison
    )

    assert (
        "ssvi"
        in comparison
    )

    for model_name in [
        "svi",
        "ssvi",
    ]:
        metrics = (
            comparison[
                model_name
            ]
        )

        assert (
            metrics[
                "rmse"
            ]
            >= 0.0
        )

        assert (
            metrics[
                "mae"
            ]
            >= 0.0
        )

        assert (
            metrics[
                "max_absolute_error"
            ]
            >= 0.0
        )

        assert (
            metrics[
                "observation_count"
            ]
            > 0
        )


def test_model_comparison_uses_equal_samples():
    response = client.post(
        "/calibration/volatility-surface",
        json=comparison_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    comparison = (
        response
        .json()[
            "model_comparison"
        ]
    )

    assert (
        comparison[
            "svi"
        ][
            "observation_count"
        ]
        ==
        comparison[
            "ssvi"
        ][
            "observation_count"
        ]
    )

    assert (
        comparison[
            "svi"
        ][
            "observation_count"
        ]
        == 15
    )


def test_model_comparison_reports_winners():
    response = client.post(
        "/calibration/volatility-surface",
        json=comparison_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    comparison = (
        response
        .json()[
            "model_comparison"
        ]
    )

    valid_models = {
        "svi",
        "ssvi",
        "tie",
    }

    assert (
        comparison[
            "better_rmse_model"
        ]
        in valid_models
    )

    assert (
        comparison[
            "better_mae_model"
        ]
        in valid_models
    )


def test_model_comparison_contains_maturity_breakdown():
    response = client.post(
        "/calibration/volatility-surface",
        json=comparison_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    comparison = (
        response
        .json()[
            "model_comparison"
        ]
    )

    maturity_comparisons = (
        comparison[
            "maturity_comparisons"
        ]
    )

    assert (
        len(
            maturity_comparisons
        )
        == 3
    )

    maturities = [
        item[
            "maturity"
        ]
        for item
        in maturity_comparisons
    ]

    assert maturities == [
        0.5,
        1.0,
        2.0,
    ]


def test_each_maturity_uses_same_observations():
    response = client.post(
        "/calibration/volatility-surface",
        json=comparison_payload(),
    )

    assert (
        response.status_code
        == 200
    )

    maturity_comparisons = (
        response
        .json()[
            "model_comparison"
        ][
            "maturity_comparisons"
        ]
    )

    for item in (
        maturity_comparisons
    ):
        assert (
            item[
                "observation_count"
            ]
            ==
            item[
                "svi"
            ][
                "observation_count"
            ]
        )

        assert (
            item[
                "observation_count"
            ]
            ==
            item[
                "ssvi"
            ][
                "observation_count"
            ]
        )

        assert (
            item[
                "observation_count"
            ]
            == 5
        )


def test_one_maturity_has_no_model_comparison():
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
            "model_comparison"
        ]
        is None
    )