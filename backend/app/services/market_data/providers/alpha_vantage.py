import os
import time
from typing import Any, Dict, List

import requests

from app.services.market_data.provider import (
    OptionChainProvider,
)

from app.services.market_data.types import (
    OptionChainQuote,
    OptionChainSnapshot,
)


class AlphaVantageOptionChainProvider(
    OptionChainProvider
):
    BASE_URL = (
        "https://www.alphavantage.co/query"
    )

    def __init__(
        self,
        api_key: str = None,
    ):
        self.api_key = (
            api_key
            or os.getenv(
                "ALPHA_VANTAGE_API_KEY"
            )
        )

        if not self.api_key:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY "
                "is not configured."
            )

    @staticmethod
    def _float_or_none(
        value: Any,
    ):
        if value in (
            None,
            "",
            "None",
            "null",
        ):
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _int_or_none(
        value: Any,
    ):
        if value in (
            None,
            "",
            "None",
            "null",
        ):
            return None

        try:
            return int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    def get_option_chain(
        self,
        symbol: str,
    ) -> OptionChainSnapshot:

        symbol = (
            symbol
            .strip()
            .upper()
        )

        response = requests.get(
            self.BASE_URL,
            params={
                "function":
                    "REALTIME_OPTIONS",
                "symbol":
                    symbol,
                "require_greeks":
                    "true",
                "apikey":
                    self.api_key,
            },
            timeout=30,
        )

        response.raise_for_status()

        payload: Dict[
            str,
            Any,
        ] = response.json()

        if "Information" in payload:
            raise ValueError(
                payload["Information"]
            )

        if "Note" in payload:
            raise ValueError(
                payload["Note"]
            )

        if "Error Message" in payload:
            raise ValueError(
                payload[
                    "Error Message"
                ]
            )

        raw_quotes: List[
            Dict[str, Any]
        ] = (
            payload.get("data")
            or []
        )

        if not raw_quotes:
            raise ValueError(
                "Alpha Vantage returned "
                "no option-chain data."
            )

        @staticmethod
        def _looks_like_demo_options(
            raw_quotes,
        ) -> bool:
            if not raw_quotes:
                return False

            expiries = {
                str(
                    item.get("expiration")
                    or item.get("expiration_date")
                    or ""
                )
                for item in raw_quotes
            }

            if "2099-99-99" in expiries:
                return True

            return False

        quotes = []

        expiries = set()

        for item in raw_quotes:
            expiry = (
                item.get(
                    "expiration"
                )
                or item.get(
                    "expiration_date"
                )
            )

            strike = (
                self._float_or_none(
                    item.get("strike")
                )
            )

            option_type = (
                item.get("type")
                or item.get(
                    "option_type"
                )
            )

            if (
                expiry is None
                or strike is None
                or option_type is None
            ):
                continue

            option_type = (
                str(option_type)
                .lower()
            )

            expiries.add(
                str(expiry)
            )

            quotes.append(
                OptionChainQuote(
                    symbol=symbol,
                    expiry=str(
                        expiry
                    ),
                    option_type=
                        option_type,
                    strike=strike,

                    bid=
                        self._float_or_none(
                            item.get(
                                "bid"
                            )
                        ),

                    ask=
                        self._float_or_none(
                            item.get(
                                "ask"
                            )
                        ),

                    last=
                        self._float_or_none(
                            item.get(
                                "last"
                            )
                            or item.get(
                                "last_price"
                            )
                        ),

                    volume=
                        self._int_or_none(
                            item.get(
                                "volume"
                            )
                        ),

                    open_interest=
                        self._int_or_none(
                            item.get(
                                "open_interest"
                            )
                        ),

                    implied_volatility=
                        self._float_or_none(
                            item.get(
                                "implied_volatility"
                            )
                        ),

                    source=
                        "alpha_vantage",
                )
            )

        if not quotes:
            raise ValueError(
                "No usable option "
                "contracts were returned."
            )

        # Realtime options payloads may not
        # provide underlying spot directly.
        # Fetch the equity quote separately.

        time.sleep(1.1) # Avoid Alpha Vantage free-tier burst throttling.

        quote_response = requests.get(
            self.BASE_URL,
            params={
                "function":
                    "GLOBAL_QUOTE",
                "symbol":
                    symbol,
                # "entitlement":
                #     "delayed",
                "apikey":
                    self.api_key,
            },
            timeout=15,
        )

        quote_response.raise_for_status()

        quote_payload = quote_response.json()

        if "Information" in quote_payload:
            raise ValueError(
                "Alpha Vantage GLOBAL_QUOTE: "
                + str(
                    quote_payload[
                        "Information"
                    ]
                )
            )

        if "Note" in quote_payload:
            raise ValueError(
                "Alpha Vantage GLOBAL_QUOTE: "
                + str(
                    quote_payload[
                        "Note"
                    ]
                )
            )

        if "Error Message" in quote_payload:
            raise ValueError(
                "Alpha Vantage GLOBAL_QUOTE: "
                + str(
                    quote_payload[
                        "Error Message"
                    ]
                )
            )

        global_quote = (
            quote_payload.get(
                "Global Quote"
            )
            or {}
        )

        spot = self._float_or_none(
            global_quote.get(
                "05. price"
            )
        )

        if spot is None:
            raise ValueError(
                "Alpha Vantage GLOBAL_QUOTE "
                "returned no usable spot price. "
                f"Response keys: "
                f"{list(quote_payload.keys())}"
            )

        return OptionChainSnapshot(
            symbol=symbol,
            spot=spot,
            currency="USD",
            expiries=sorted(
                expiries
            ),
            quotes=quotes,
            source="alpha_vantage",
        )