from app.services.market_data.service import (
    get_option_chain,
)


def test_mock_option_chain():
    snapshot = get_option_chain(
        "SPY",
        provider="mock",
    )

    assert snapshot.symbol == "SPY"
    assert snapshot.spot > 0
    assert len(
        snapshot.expiries
    ) == 2
    assert len(
        snapshot.quotes
    ) > 0


def test_mock_quotes_have_spreads():
    snapshot = get_option_chain(
        "AAPL",
        provider="mock",
    )

    for quote in snapshot.quotes:
        assert quote.bid is not None
        assert quote.ask is not None
        assert (
            quote.ask
            >= quote.bid
        )