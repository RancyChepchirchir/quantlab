from app.services.market_data.provider import (
    OptionChainProvider,
)

from app.services.market_data.types import (
    OptionChainQuote,
    OptionChainSnapshot,
)


class MockOptionChainProvider(
    OptionChainProvider
):

    def get_option_chain(
        self,
        symbol: str,
    ) -> OptionChainSnapshot:

        normalized = (
            symbol
            .strip()
            .upper()
        )

        spot = 100.0

        expiries = [
            "2026-09-18",
            "2026-12-18",
        ]

        quotes = []

        for expiry in expiries:

            for strike in [
                80.0,
                90.0,
                100.0,
                110.0,
                120.0,
            ]:

                distance = abs(
                    strike - spot
                )

                mid = max(
                    0.50,
                    10.0
                    - 0.18
                    * distance,
                )

                quotes.append(
                    OptionChainQuote(
                        symbol=
                            normalized,

                        expiry=
                            expiry,

                        option_type=
                            "call",

                        strike=
                            strike,

                        bid=
                            max(
                                0.01,
                                mid - 0.10,
                            ),

                        ask=
                            mid + 0.10,

                        last=
                            mid,

                        volume=
                            100,

                        open_interest=
                            500,

                        implied_volatility=
                            None,

                        source=
                            "mock",
                    )
                )

        return OptionChainSnapshot(
            symbol=normalized,
            spot=spot,
            currency="USD",
            expiries=expiries,
            quotes=quotes,
            source="mock",
        )