"""
ats/base.py — Abstract base class for ATS-specific handlers.

Each concrete handler knows:
  - Which URL patterns identify this ATS
  - How to wait for the form to be fully loaded
  - Any platform-specific pre/post-fill steps (e.g. dismissing cookie banners)
  - How to detect and request a verification code
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class BaseATSHandler(ABC):
    name: str = "base"

    def __init__(self, page: Page) -> None:
        self.page = page

    # ------------------------------------------------------------------
    # URL matching
    # ------------------------------------------------------------------

    @classmethod
    @abstractmethod
    def matches(cls, url: str) -> bool:
        """Return True if the given URL belongs to this ATS."""

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def before_fill(self) -> None:
        """Called before Simplify autofill and gap-filling. Override to handle
        cookie banners, login walls, or other preambles."""

    def after_fill(self) -> None:
        """Called after all fields have been filled. Override to handle
        multi-page forms, CAPTCHA prompts, or pre-submit validation."""

    @abstractmethod
    def wait_for_form(self, timeout_ms: int = 15_000) -> None:
        """Block until the application form is interactive."""

    # ------------------------------------------------------------------
    # Verification code support
    # ------------------------------------------------------------------

    def verification_code_sender(self) -> Optional[str]:
        """Return the known sender email for this ATS's verification emails,
        or None to search all known ATS senders."""
        return None

    def needs_verification_code(self) -> bool:
        """Return True if the current page state requires a verification code."""
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def dismiss_cookie_banner(self) -> None:
        selectors = [
            "button#onetrust-accept-btn-handler",
            "[aria-label='Accept cookies']",
            "button:has-text('Accept')",
            "button:has-text('Got it')",
        ]
        for sel in selectors:
            try:
                btn = self.page.query_selector(sel)
                if btn and btn.is_visible():
                    btn.click()
                    logger.info("Dismissed cookie banner via: %s", sel)
                    return
            except Exception:
                continue
