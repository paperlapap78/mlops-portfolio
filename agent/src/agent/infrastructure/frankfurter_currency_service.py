"""
Infrastructure adapter: FrankfurterCurrencyService

Implements CurrencyService using the Frankfurter API (free, EU-hosted, no API key).
httpx calls here are auto-instrumented by OTel (HTTPXClientInstrumentor),
so they appear as child spans in X-Ray traces.
"""

import httpx

from agent.domain.ports.currency_service import CurrencyService

_FRANKFURTER_URL = "https://api.frankfurter.app/latest"


class FrankfurterCurrencyService(CurrencyService):
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        response = httpx.get(
            _FRANKFURTER_URL,
            params={
                "base": from_currency.upper(),
                "symbols": to_currency.upper(),
            },
            timeout=10.0,
        )
        response.raise_for_status()
        rates = response.json()["rates"]
        target = to_currency.upper()
        if target not in rates:
            raise ValueError(f"Currency {target} not found in exchange rates.")
        return round(amount * float(rates[target]), 2)
