from app.providers.base import CallProvider
from app.providers.mock_provider_a import MockProviderA
from app.providers.mock_provider_b import MockProviderB


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, CallProvider] = {
            "provider_a": MockProviderA(),
            "provider_b": MockProviderB(),
        }

    def get(self, provider: str) -> CallProvider:
        try:
            return self._providers[provider]
        except KeyError:
            raise ValueError(f"Unknown provider: {provider}")