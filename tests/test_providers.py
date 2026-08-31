from app.providers.base import CallProvider
from app.providers.mock_provider_a import MockProviderA
from app.providers.mock_provider_b import MockProviderB


def test_provider_a_implements_provider_interface():
    provider = MockProviderA()

    assert isinstance(provider, CallProvider)


def test_provider_b_implements_provider_interface():
    provider = MockProviderB()

    assert isinstance(provider, CallProvider)


def test_provider_a_returns_provider_call():
    provider = MockProviderA()

    result = provider.initiate_call(
        call_id=123,
        phone_number="+919999999999",
        event_callback=lambda event: None,
    )

    assert result.call_id == 123
    assert result.provider_call_id.startswith("provider-a-")


def test_provider_b_returns_provider_call():
    provider = MockProviderB()

    result = provider.initiate_call(
        call_id=456,
        phone_number="+918888888888",
        event_callback=lambda event: None,
    )

    assert result.call_id == 456
    assert result.provider_call_id.startswith("provider-b-")