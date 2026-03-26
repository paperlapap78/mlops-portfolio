"""
LangChain tool: Currency Conversion

Converts amounts between currencies using the Frankfurter API:
  https://api.frankfurter.app

Free, no API key, GDPR-safe (EU-hosted), updated daily with ECB exchange rates.
httpx calls here are auto-instrumented by OTel (HTTPXClientInstrumentor),
so they appear as child spans in X-Ray traces.
"""

import json

import httpx
import structlog
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = structlog.get_logger()

_FRANKFURTER_URL = "https://api.frankfurter.app/latest"


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
        "Example: {\"amount\": 100, \"from_currency\": \"CHF\", \"to_currency\": \"EUR\"}"
    )

    def _run(self, tool_input: str) -> str:
        data = json.loads(tool_input)
        validated = _CurrencyInput(**data)

        response = httpx.get(
            _FRANKFURTER_URL,
            params={
                "base": validated.from_currency.upper(),
                "symbols": validated.to_currency.upper(),
            },
            timeout=10.0,
        )
        response.raise_for_status()

        rates = response.json()["rates"]
        target = validated.to_currency.upper()

        if target not in rates:
            return f"Currency {target} not found in exchange rates."

        converted = round(validated.amount * rates[target], 2)
        result = (
            f"{validated.amount} {validated.from_currency.upper()} = "
            f"{converted} {target}"
        )

        logger.info(
            "Currency converted",
            from_currency=validated.from_currency,
            to_currency=validated.to_currency,
            amount=validated.amount,
            result=converted,
        )
        return result
