import os
import time

from datetime import (
    date,
    timedelta,
)

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

import requests

from app.services.market_data.provider import (
    OptionChainProvider,
)

from app.services.market_data.types import (
    OptionChainQuote,
    OptionChainSnapshot,
)


class MassiveOptionChainProvider(
    OptionChainProvider
):
    BASE_URL = (
        "https://api.massive.com"
    )

    # ---------------------------------------------------------
    # Market-chain configuration
    # ---------------------------------------------------------

    # Two genuinely different maturities
    # are required for a 2-D volatility
    # surface.
    MAX_EXPIRIES = 2

    # Start conservatively. Once provider
    # usage is stable this can be raised
    # from 2 to 3.
    STRIKES_PER_EXPIRY = 3

    # Ignore pathological ultra-short
    # and very long expiries.
    MIN_DAYS_TO_EXPIRY = 7
    MAX_DAYS_TO_EXPIRY = 90

    # Prefer expiries reasonably close
    # to these maturity horizons.
    TARGET_EXPIRY_DAYS = (
        14,
        45,
    )

    # Keep selected strikes reasonably
    # close to ATM.
    MIN_MONEYNESS = 0.95
    MAX_MONEYNESS = 1.05

    # Cached EOD prices do not require
    # another provider request.
    PRICE_CACHE_TTL_SECONDS = 900

    # Delay before an uncached option-
    # price request.
    #
    # This remains deliberately explicit
    # so it can be adjusted to the account
    # rate limit without touching the
    # pricing logic.
    REQUEST_DELAY_SECONDS = 1.05

    # Limit reference-data pagination.
    MAX_CONTRACT_PAGES = 6

    _price_cache: Dict[
        Tuple[str, str],
        Tuple[
            float,
            Optional[float],
        ],
    ] = {}

    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or os.getenv(
                "MASSIVE_API_KEY"
            )
        )

        if self.api_key:
            self.api_key = (
                self.api_key.strip()
            )

        if not self.api_key:
            raise ValueError(
                "MASSIVE_API_KEY "
                "is not configured."
            )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    @property
    def headers(
        self,
    ) -> Dict[str, str]:
        return {
            "Authorization":
                f"Bearer {self.api_key}",
        }

    # ---------------------------------------------------------
    # Parsing helpers
    # ---------------------------------------------------------

    @staticmethod
    def _float_or_none(
        value: Any,
    ) -> Optional[float]:
        if value in (
            None,
            "",
            "None",
            "null",
        ):
            return None

        try:
            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _int_or_none(
        value: Any,
    ) -> Optional[int]:
        if value in (
            None,
            "",
            "None",
            "null",
        ):
            return None

        try:
            return int(
                float(
                    value
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    # ---------------------------------------------------------
    # HTTP helper
    # ---------------------------------------------------------

    def _get_json(
        self,
        url: str,
        params: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:

        from app.services.market_data.errors import (
            MarketDataAuthorizationError,
            MarketDataRateLimitError,
            MarketDataUpstreamError,
        )

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30,
            )

        except requests.RequestException as error:
            raise MarketDataUpstreamError(
                message=(
                    "Massive market-data request "
                    "failed before a response "
                    "was received."
                ),
                provider=
                    "massive",
                retryable=
                    True,
            ) from error

        try:
            payload = (
                response.json()
            )

        except ValueError:
            payload = {
                "message":
                    response.text
                    or (
                        "Massive returned "
                        "an invalid response."
                    )
            }

        if response.status_code == 401:
            raise MarketDataAuthorizationError(
                message=(
                    payload.get(
                        "message"
                    )
                    or (
                        "Massive API key "
                        "was rejected."
                    )
                ),
                provider=
                    "massive",
                upstream_status=
                    response.status_code,
            )

        if response.status_code == 403:
            raise MarketDataAuthorizationError(
                message=(
                    payload.get(
                        "message"
                    )
                    or (
                        "The Massive account "
                        "is not entitled to "
                        "this market data."
                    )
                ),
                provider=
                    "massive",
                upstream_status=
                    response.status_code,
            )

        if response.status_code == 429:
            raise MarketDataRateLimitError(
                message=(
                    payload.get(
                        "message"
                    )
                    or (
                        "Massive API rate "
                        "limit reached."
                    )
                ),
                provider=
                    "massive",
                upstream_status=
                    response.status_code,
            )

        if not response.ok:
            raise MarketDataUpstreamError(
                message=(
                    payload.get(
                        "message"
                    )
                    or payload.get(
                        "error"
                    )
                    or (
                        "Massive API request "
                        "failed."
                    )
                ),
                provider=
                    "massive",
                upstream_status=
                    response.status_code,
                retryable=(
                    response.status_code
                    >= 500
                ),
            )

        if not isinstance(
            payload,
            dict,
        ):
            raise MarketDataUpstreamError(
                message=(
                    "Massive returned an "
                    "unexpected payload."
                ),
                provider=
                    "massive",
                upstream_status=
                    response.status_code,
                retryable=
                    False,
            )

        return payload

    # ---------------------------------------------------------
    # Cached EOD close
    # ---------------------------------------------------------

    def _latest_daily_close(
        self,
        ticker: str,
        end_date: date,
    ) -> Optional[float]:

        cache_key = (
            ticker,
            end_date.isoformat(),
        )

        cached = (
            self._price_cache.get(
                cache_key
            )
        )

        if cached is not None:
            (
                cached_at,
                cached_price,
            ) = cached

            if (
                time.time()
                - cached_at
                < self
                .PRICE_CACHE_TTL_SECONDS
            ):
                return cached_price

        start_date = (
            end_date
            - timedelta(
                days=10
            )
        )

        url = (
            f"{self.BASE_URL}"
            f"/v2/aggs/ticker/"
            f"{ticker}"
            f"/range/1/day/"
            f"{start_date.isoformat()}"
            f"/{end_date.isoformat()}"
        )

        payload = self._get_json(
            url,
            params={
                "adjusted":
                    "true",

                "sort":
                    "desc",

                "limit":
                    10,
            },
        )

        results = (
            payload.get(
                "results"
            )
            or []
        )

        if not results:
            self._price_cache[
                cache_key
            ] = (
                time.time(),
                None,
            )

            return None

        price = (
            self._float_or_none(
                results[0].get(
                    "c"
                )
            )
        )

        self._price_cache[
            cache_key
        ] = (
            time.time(),
            price,
        )

        return price

    # ---------------------------------------------------------
    # Throttled EOD close
    # ---------------------------------------------------------

    def _throttled_daily_close(
        self,
        ticker: str,
        end_date: date,
    ) -> Optional[float]:

        cache_key = (
            ticker,
            end_date.isoformat(),
        )

        cached = (
            self._price_cache.get(
                cache_key
            )
        )

        if cached is not None:
            (
                cached_at,
                cached_price,
            ) = cached

            if (
                time.time()
                - cached_at
                < self
                .PRICE_CACHE_TTL_SECONDS
            ):
                return cached_price

        # Delay only when we really need
        # to contact the upstream API.
        time.sleep(
            self.REQUEST_DELAY_SECONDS
        )

        return (
            self._latest_daily_close(
                ticker,
                end_date,
            )
        )

    # ---------------------------------------------------------
    # Contract discovery
    # ---------------------------------------------------------

    def _get_contracts(
        self,
        symbol: str,
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Retrieve active contracts.

        Massive may paginate reference
        contracts, so collect a bounded
        number of pages rather than silently
        assuming the first 250 contracts
        contain enough strikes/expiries.
        """

        url = (
            f"{self.BASE_URL}"
            f"/v3/reference/"
            f"options/contracts"
        )

        params: Optional[
            Dict[str, Any]
        ] = {
            "underlying_ticker":
                symbol,

            "expired":
                "false",

            "order":
                "asc",

            "sort":
                "expiration_date",

            "limit":
                250,
        }

        contracts: List[
            Dict[str, Any]
        ] = []

        pages = 0

        while (
            url
            and pages
            < self.MAX_CONTRACT_PAGES
        ):
            payload = (
                self._get_json(
                    url,
                    params=params,
                )
            )

            contracts.extend(
                payload.get(
                    "results"
                )
                or []
            )

            pages += 1

            next_url = (
                payload.get(
                    "next_url"
                )
            )

            if not next_url:
                break

            # next_url already contains
            # its cursor/query string.
            url = next_url
            params = None

        return contracts

    # ---------------------------------------------------------
    # Representative expiry selection
    # ---------------------------------------------------------

    def _select_representative_expiries(
        self,
        expiries: List[str],
        today: date,
    ) -> List[str]:

        eligible: List[
            Tuple[str, int]
        ] = []

        for expiry in expiries:
            try:
                expiry_date = (
                    date.fromisoformat(
                        expiry
                    )
                )

            except ValueError:
                continue

            days_to_expiry = (
                expiry_date
                - today
            ).days

            if (
                days_to_expiry
                < self.MIN_DAYS_TO_EXPIRY
            ):
                continue

            if (
                days_to_expiry
                > self.MAX_DAYS_TO_EXPIRY
            ):
                continue

            eligible.append(
                (
                    expiry,
                    days_to_expiry,
                )
            )

        if not eligible:
            raise ValueError(
                "No suitable option expiries "
                "were found within the configured "
                "maturity window."
            )

        selected: List[
            str
        ] = []

        for target_days in (
            self.TARGET_EXPIRY_DAYS
        ):
            candidates = [
                item
                for item
                in eligible
                if item[0]
                not in selected
            ]

            if not candidates:
                break

            (
                best_expiry,
                _,
            ) = min(
                candidates,
                key=lambda item:
                    abs(
                        item[1]
                        - target_days
                    ),
            )

            selected.append(
                best_expiry
            )

            if (
                len(selected)
                >= self.MAX_EXPIRIES
            ):
                break

        return sorted(
            selected
        )

    # ---------------------------------------------------------
    # Matched call/put selection
    # ---------------------------------------------------------

    def _select_matched_pairs(
        self,
        contracts: List[
            Dict[str, Any]
        ],
        spot: float,
    ) -> List[
        Tuple[
            Dict[str, Any],
            Dict[str, Any],
        ]
    ]:
        """
        Select matched call/put pairs at
        the same strike.

        Strike levels nearest spot are
        preferred.
        """

        calls: Dict[
            float,
            Dict[str, Any],
        ] = {}

        puts: Dict[
            float,
            Dict[str, Any],
        ] = {}

        for contract in contracts:
            strike = (
                self._float_or_none(
                    contract.get(
                        "strike_price"
                    )
                )
            )

            ticker = (
                contract.get(
                    "ticker"
                )
            )

            option_type = (
                contract.get(
                    "contract_type"
                )
            )

            if (
                strike is None
                or not ticker
            ):
                continue

            moneyness = (
                strike
                / spot
            )

            if (
                moneyness
                < self.MIN_MONEYNESS
                or moneyness
                > self.MAX_MONEYNESS
            ):
                continue

            if option_type == "call":
                calls[
                    strike
                ] = contract

            elif option_type == "put":
                puts[
                    strike
                ] = contract

        matched_strikes = list(
            calls.keys()
            & puts.keys()
        )

        matched_strikes.sort(
            key=lambda strike:
                abs(
                    strike
                    - spot
                )
        )

        selected_strikes = (
            matched_strikes[
                : self
                .STRIKES_PER_EXPIRY
            ]
        )

        return [
            (
                calls[
                    strike
                ],
                puts[
                    strike
                ],
            )
            for strike
            in selected_strikes
        ]

    # ---------------------------------------------------------
    # Convert provider contract to QuantLab quote
    # ---------------------------------------------------------

    def _contract_to_quote(
        self,
        contract: Dict[
            str,
            Any,
        ],
        symbol: str,
        expiry: str,
        today: date,
    ) -> Optional[
        OptionChainQuote
    ]:

        ticker = (
            contract.get(
                "ticker"
            )
        )

        strike = (
            self._float_or_none(
                contract.get(
                    "strike_price"
                )
            )
        )

        option_type = (
            contract.get(
                "contract_type"
            )
        )

        if (
            not ticker
            or strike is None
            or option_type
            not in {
                "call",
                "put",
            }
        ):
            return None

        option_close = (
            self._throttled_daily_close(
                ticker,
                today,
            )
        )

        if (
            option_close is None
            or option_close <= 0
        ):
            return None

        return OptionChainQuote(
            symbol=
                symbol,

            expiry=
                expiry,

            option_type=
                option_type,

            strike=
                strike,

            bid=
                None,

            ask=
                None,

            last=
                option_close,

            volume=
                None,

            open_interest=
                None,

            implied_volatility=
                None,

            source=
                "massive_eod",
        )

    # ---------------------------------------------------------
    # Public provider method
    # ---------------------------------------------------------

    def get_option_chain(
        self,
        symbol: str,
    ) -> OptionChainSnapshot:
        symbol = (
            symbol
            .strip()
            .upper()
        )

        if not symbol:
            raise ValueError(
                "Symbol must not be empty."
            )

        today = (
            date.today()
        )

        # -----------------------------------------------------
        # 1. Underlying EOD spot
        # -----------------------------------------------------

        spot = (
            self._latest_daily_close(
                symbol,
                today,
            )
        )

        if spot is None:
            raise ValueError(
                "Unable to obtain "
                f"EOD spot for {symbol}."
            )

        # -----------------------------------------------------
        # 2. Discover active contracts
        # -----------------------------------------------------

        contracts = (
            self._get_contracts(
                symbol
            )
        )

        if not contracts:
            raise ValueError(
                f"No active {symbol} "
                "option contracts found."
            )

        # -----------------------------------------------------
        # 3. Extract available expiries
        # -----------------------------------------------------

        expiries = sorted(
            {
                str(
                    contract.get(
                        "expiration_date"
                    )
                )
                for contract
                in contracts
                if contract.get(
                    "expiration_date"
                )
            }
        )

        if not expiries:
            raise ValueError(
                "No valid option "
                "expiries returned."
            )

        # -----------------------------------------------------
        # 4. Select representative maturities
        # -----------------------------------------------------

        target_expiries = (
            self
            ._select_representative_expiries(
                expiries,
                today,
            )
        )

        quotes: List[
            OptionChainQuote
        ] = []

        # -----------------------------------------------------
        # 5. Select matched call/put pairs for each expiry
        # -----------------------------------------------------

        for expiry in (
            target_expiries
        ):
            expiry_contracts = [
                contract
                for contract
                in contracts
                if str(
                    contract.get(
                        "expiration_date"
                    )
                )
                == expiry
            ]

            matched_pairs = (
                self
                ._select_matched_pairs(
                    expiry_contracts,
                    spot,
                )
            )

            for (
                call_contract,
                put_contract,
            ) in matched_pairs:

                call_quote = (
                    self
                    ._contract_to_quote(
                        call_contract,
                        symbol,
                        expiry,
                        today,
                    )
                )

                put_quote = (
                    self
                    ._contract_to_quote(
                        put_contract,
                        symbol,
                        expiry,
                        today,
                    )
                )

                # Keep parity observations
                # matched. If either side has no
                # valid EOD close, skip the pair.
                if (
                    call_quote is None
                    or put_quote is None
                ):
                    continue

                quotes.append(
                    call_quote
                )

                quotes.append(
                    put_quote
                )

        # -----------------------------------------------------
        # 6. Validate resulting chain
        # -----------------------------------------------------

        if not quotes:
            raise ValueError(
                "Contracts were found, "
                "but no matched call/put "
                "pairs with usable EOD "
                "prices were returned."
            )

        actual_expiries = sorted(
            {
                quote.expiry
                for quote
                in quotes
            }
        )

        returned_quote_count = len(
            quotes
        )

        return (
            OptionChainSnapshot(
                symbol=
                    symbol,

                spot=
                    spot,

                currency=
                    "USD",

                expiries=
                    actual_expiries,

                quotes=
                    quotes,

                source=
                    "massive_eod",

                selected_expiries=
                    target_expiries,

                requested_strikes_per_expiry=
                    self.STRIKES_PER_EXPIRY,

                returned_quote_count=
                    returned_quote_count,
            )
        )