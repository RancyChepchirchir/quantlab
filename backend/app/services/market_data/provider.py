from abc import ABC, abstractmethod

from app.services.market_data.types import (
    OptionChainSnapshot,
)


class OptionChainProvider(ABC):

    @abstractmethod
    def get_option_chain(
        self,
        symbol: str,
    ) -> OptionChainSnapshot:
        raise NotImplementedError