"""
LangChain tool: Currency Conversion

The LangChain agent calls this tool when the user asks to convert currencies.
The tool takes the agent's structured input, delegates to the CurrencyService port
(not httpx directly), and returns a formatted result string.

Injecting CurrencyService (rather than calling httpx inline) means this tool
can be unit-tested with FakeCurrencyService from conftest.py without any network access.
"""

import json

import structlog
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from agent.domain.ports.currency_service import CurrencyService

logger = structlog.get_logger()


class _CurrencyInput(BaseModel):
    amount: float = Field(description="The amount to convert", gt=0)
    from_currency: str = Field(description="ISO 4217 source currency code, e.g. CHF")
    to_currency: str = Field(description="ISO 4217 target currency code, e.g. EUR")


class CurrencyConversionTool(BaseTool):
    name: str = "convert_currency"
    description: str = (
        "Convert a monetary amount between two currencies using live exchange rates. "
        'Input must be JSON with keys: "amount" (float), '
        '"from_currency" (str, ISO 4217), "to_currency" (str, ISO 4217). '
        'Example: {"amount": 100, "from_currency": "CHF", "to_currency": "EUR"}'
    )

    # LangChain BaseTool uses Pydantic — private fields must bypass model validation
    _currency_service: CurrencyService

    def __init__(self, currency_service: CurrencyService) -> None:
        super().__init__()
        object.__setattr__(self, "_currency_service", currency_service)

    def _run(self, tool_input: str) -> str:
        validated = _CurrencyInput(**json.loads(tool_input))

        converted = self._currency_service.convert(
            amount=validated.amount,
            from_currency=validated.from_currency,
            to_currency=validated.to_currency,
        )

        result = (
            f"{validated.amount} {validated.from_currency.upper()} = "
            f"{converted} {validated.to_currency.upper()}"
        )

        logger.info(
            "Currency converted",
            from_currency=validated.from_currency,
            to_currency=validated.to_currency,
            amount=validated.amount,
            result=converted,
        )
        return result
