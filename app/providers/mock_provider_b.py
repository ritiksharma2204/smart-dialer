import uuid
from typing import Callable

from app.providers.base import CallProvider, ProviderCall


class MockProviderB(CallProvider):
    """
    Unreliable mock provider.

    Used to simulate provider failures and
    abnormal event behaviour.
    """

    def __init__(
        self,
        failure_rate: float = 0.2,
    ):
        self.failure_rate = failure_rate

    def initiate_call(
        self,
        call_id: int,
        phone_number: str,
        event_callback: Callable,
    ) -> ProviderCall:

        provider_call_id = f"provider-b-{uuid.uuid4()}"

        return ProviderCall(
            provider_call_id=provider_call_id,
            call_id=call_id,
        )

    def cancel_call(
        self,
        provider_call_id: str,
    ) -> None:
        return None