"""
Unit tests for CurrencyConversionTool.

All tests use FakeCurrencyService — no network calls required.
"""

import json

import pytest

from agent.domain.ports.currency_service import CurrencyService
from agent.infrastructure.tools.currency_tool import CurrencyConversionTool
from tests.conftest import FakeCurrencyService

_TOOL_INPUT = json.dumps({
    "amount": 100.0,
    "from_currency": "CHF",
    "to_currency": "EUR",
})


@pytest.fixture
def tool() -> CurrencyConversionTool:
    return CurrencyConversionTool(currency_service=FakeCurrencyService(rate=0.95))


class TestCurrencyConversionTool:
    def test_returns_formatted_string(self, tool: CurrencyConversionTool) -> None:
        result = tool._run(_TOOL_INPUT)
        # FakeCurrencyService(rate=0.95): 100.0 * 0.95 = 95.0
        assert result == "100.0 CHF = 95.0 EUR"

    def test_delegates_to_currency_service(self) -> None:
        class CapturingService(CurrencyService):
            def __init__(self) -> None:
                self.calls: list[tuple[float, str, str]] = []

            def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
                self.calls.append((amount, from_currency, to_currency))
                return 42.0

        service = CapturingService()
        t = CurrencyConversionTool(currency_service=service)
        t._run(_TOOL_INPUT)

        assert len(service.calls) == 1
        amount, from_cur, to_cur = service.calls[0]
        assert amount == 100.0
        assert from_cur == "CHF"
        assert to_cur == "EUR"

    def test_unknown_currency_propagates_error(self) -> None:
        class RaisingService(CurrencyService):
            def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
                raise ValueError(f"Currency {to_currency} not found in exchange rates.")

        t = CurrencyConversionTool(currency_service=RaisingService())
        with pytest.raises(ValueError, match="XYZ"):
            t._run(json.dumps({"amount": 10.0, "from_currency": "USD", "to_currency": "XYZ"}))
