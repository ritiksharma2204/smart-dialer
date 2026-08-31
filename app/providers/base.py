from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class ProviderCall:
    provider_call_id: str
    call_id: int


class CallProvider(ABC):

    @abstractmethod
    def initiate_call(
        self,
        call_id: int,
        phone_number: str,
        event_callback: Callable,
    ) -> ProviderCall:
        pass

    @abstractmethod
    def cancel_call(
        self,
        provider_call_id: str,
    ) -> None:
        pass