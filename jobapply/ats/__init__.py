"""
ats/ — ATS handler registry.

Call `get_handler(url, page)` to get the right handler for a given job URL.
"""

from __future__ import annotations

from playwright.sync_api import Page

from jobapply.ats.ashby import AshbyHandler
from jobapply.ats.base import BaseATSHandler
from jobapply.ats.greenhouse import GreenhouseHandler
from jobapply.ats.lever import LeverHandler

_HANDLERS: list[type[BaseATSHandler]] = [
    GreenhouseHandler,
    LeverHandler,
    AshbyHandler,
]


def get_handler(url: str, page: Page) -> BaseATSHandler | None:
    """Return the matching ATS handler for the given URL, or None if unknown."""
    for cls in _HANDLERS:
        if cls.matches(url):
            return cls(page)
    return None
