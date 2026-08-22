import pytest
import requests

from app.services.market_data.errors import (
    MarketDataAuthorizationError,
    MarketDataRateLimitError,
    MarketDataUpstreamError,
)

from app.services.market_data.providers.massive import (
    MassiveOptionChainProvider,
)


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload,
    ):
        self.status_code = (
            status_code
        )

        self._payload = (
            payload
        )

        self.text = (
            str(
                payload
            )
        )

    @property
    def ok(
        self,
    ) -> bool:
        return (
            200
            <= self.status_code
            < 300
        )

    def json(
        self,
    ):
        return self._payload


def test_massive_403_becomes_authorization_error(
    monkeypatch,
):
    provider = (
        MassiveOptionChainProvider(
            api_key="test"
        )
    )

    def fake_get(
        *args,
        **kwargs,
    ):
        return FakeResponse(
            403,
            {
                "message":
                    "Not entitled",
            },
        )

    monkeypatch.setattr(
        requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        MarketDataAuthorizationError
    ) as error:
        provider._get_json(
            "https://example.test"
        )

    assert (
        error.value
        .status_code
        == 403
    )

    assert (
        error.value
        .provider
        == "massive"
    )

    assert (
        error.value
        .retryable
        is False
    )


def test_massive_429_becomes_rate_limit_error(
    monkeypatch,
):
    provider = (
        MassiveOptionChainProvider(
            api_key="test"
        )
    )

    def fake_get(
        *args,
        **kwargs,
    ):
        return FakeResponse(
            429,
            {
                "message":
                    "Too many requests",
            },
        )

    monkeypatch.setattr(
        requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        MarketDataRateLimitError
    ) as error:
        provider._get_json(
            "https://example.test"
        )

    assert (
        error.value
        .status_code
        == 429
    )

    assert (
        error.value
        .retryable
        is True
    )


def test_massive_500_becomes_upstream_error(
    monkeypatch,
):
    provider = (
        MassiveOptionChainProvider(
            api_key="test"
        )
    )

    def fake_get(
        *args,
        **kwargs,
    ):
        return FakeResponse(
            500,
            {
                "message":
                    "Provider unavailable",
            },
        )

    monkeypatch.setattr(
        requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        MarketDataUpstreamError
    ) as error:
        provider._get_json(
            "https://example.test"
        )

    assert (
        error.value
        .status_code
        == 502
    )

    assert (
        error.value
        .upstream_status
        == 500
    )

    assert (
        error.value
        .retryable
        is True
    )


def test_massive_network_failure_becomes_upstream_error(
    monkeypatch,
):
    provider = (
        MassiveOptionChainProvider(
            api_key="test"
        )
    )

    def fake_get(
        *args,
        **kwargs,
    ):
        raise (
            requests
            .ConnectionError(
                "offline"
            )
        )

    monkeypatch.setattr(
        requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        MarketDataUpstreamError
    ) as error:
        provider._get_json(
            "https://example.test"
        )

    assert (
        error.value
        .status_code
        == 502
    )

    assert (
        error.value
        .retryable
        is True
    )


def test_massive_success_returns_payload(
    monkeypatch,
):
    provider = (
        MassiveOptionChainProvider(
            api_key="test"
        )
    )

    payload = {
        "status":
            "OK",

        "results":
            [
                {
                    "c":
                        100.0,
                }
            ],
    }

    def fake_get(
        *args,
        **kwargs,
    ):
        return FakeResponse(
            200,
            payload,
        )

    monkeypatch.setattr(
        requests,
        "get",
        fake_get,
    )

    result = (
        provider._get_json(
            "https://example.test"
        )
    )

    assert result == payload