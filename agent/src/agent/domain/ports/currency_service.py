"""
Port: CurrencyService

Converts a monetary amount between two currency codes.
The concrete adapter calls the Frankfurter API (free, EU-hosted, no API key).
"""

from abc import ABC, abstractmethod


class CurrencyService(ABC):
    @abstractmethod
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert `amount` from `from_currency` to `to_currency`.
        Currency codes follow ISO 4217 (e.g. "CHF", "EUR", "USD").
        """
