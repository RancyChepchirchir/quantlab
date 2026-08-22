from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Dict, Optional, Tuple

from app.services.market_data.types import (
    OptionChainSnapshot,
)


@dataclass(frozen=True)
class CachedOptionChain:
    snapshot: OptionChainSnapshot
    stored_at: float


class OptionChainCache:
    """
    Small process-local TTL cache for
    complete option-chain snapshots.

    This sits above individual provider
    price caches so repeated frontend
    requests do not reconstruct the whole
    chain unnecessarily.
    """

    def __init__(
        self,
        ttl_seconds: int = 300,
    ):
        if ttl_seconds <= 0:
            raise ValueError(
                "ttl_seconds must be positive."
            )

        self.ttl_seconds = (
            ttl_seconds
        )

        self._items: Dict[
            Tuple[str, str],
            CachedOptionChain,
        ] = {}

        self._lock = Lock()

    @staticmethod
    def _key(
        provider: str,
        symbol: str,
    ) -> Tuple[str, str]:
        return (
            provider
            .strip()
            .lower(),

            symbol
            .strip()
            .upper(),
        )

    def get(
        self,
        provider: str,
        symbol: str,
    ) -> Optional[
        Tuple[
            OptionChainSnapshot,
            float,
        ]
    ]:
        key = self._key(
            provider,
            symbol,
        )

        now = time()

        with self._lock:
            cached = (
                self._items.get(
                    key
                )
            )

            if cached is None:
                return None

            age_seconds = (
                now
                - cached.stored_at
            )

            if (
                age_seconds
                >= self.ttl_seconds
            ):
                self._items.pop(
                    key,
                    None,
                )

                return None

            return (
                cached.snapshot,
                age_seconds,
            )

    def set(
        self,
        provider: str,
        symbol: str,
        snapshot: OptionChainSnapshot,
    ) -> None:
        key = self._key(
            provider,
            symbol,
        )

        with self._lock:
            self._items[
                key
            ] = (
                CachedOptionChain(
                    snapshot=snapshot,
                    stored_at=time(),
                )
            )

    def clear(
        self,
    ) -> None:
        with self._lock:
            self._items.clear()

    def invalidate(
        self,
        provider: str,
        symbol: str,
    ) -> None:
        key = self._key(
            provider,
            symbol,
        )

        with self._lock:
            self._items.pop(
                key,
                None,
            )

    def size(
        self,
    ) -> int:
        with self._lock:
            return len(
                self._items
            )