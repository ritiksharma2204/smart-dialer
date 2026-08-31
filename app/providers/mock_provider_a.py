import uuid
from typing import Callable

from app.providers.base import CallProvider, ProviderCall


class MockProviderA(CallProvider):
    """
    Fast and reliable mock provider.
    """

    def initiate_call(
        self,
        call_id: int,
        phone_number: str,
        event_callback: Callable,
    ) -> ProviderCall:

        provider_call_id = f"provider-a-{uuid.uuid4()}"

        return ProviderCall(
            provider_call_id=provider_call_id,
            call_id=call_id,
        )

    def cancel_call(
        self,
        provider_call_id: str,
    ) -> None:
        return None