"""
ats/greenhouse.py — Greenhouse ATS handler.

Greenhouse domains:
  - boards.greenhouse.io/<company>/jobs/<id>
  - <company>.greenhouse.io/…
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from jobapply.ats.base import BaseATSHandler

logger = logging.getLogger(__name__)

GREENHOUSE_PATTERN = re.compile(
    r"(boards\.greenhouse\.io|[\w-]+\.greenhouse\.io)", re.IGNORECASE
)

# Greenhouse uses Lever-style email verification for some flows.
GREENHOUSE_SENDER = "no-reply@greenhouse.io"

# Key Greenhouse form selectors
FORM_SELECTOR = "form#application_form, form.application-form, #application"
SUBMIT_SELECTOR = "input[type='submit'], button[type='submit']"
VERIFICATION_INPUT = "input#verification_code, input[name='verification_code']"
VERIFICATION_FORM = "form#verification_form, .verification-form"


class GreenhouseHandler(BaseATSHandler):
    name = "greenhouse"

    @classmethod
    def matches(cls, url: str) -> bool:
        return bool(GREENHOUSE_PATTERN.search(url))

    def wait_for_form(self, timeout_ms: int = 15_000) -> None:
        logger.info("[greenhouse] Waiting for application form…")
        try:
            self.page.wait_for_selector(FORM_SELECTOR, timeout=timeout_ms, state="visible")
            logger.info("[greenhouse] Form is ready.")
        except PlaywrightTimeoutError:
            logger.warning("[greenhouse] Form not found within %dms — proceeding anyway.", timeout_ms)

    def before_fill(self) -> None:
        self.dismiss_cookie_banner()

    def verification_code_sender(self) -> Optional[str]:
        return GREENHOUSE_SENDER

    def needs_verification_code(self) -> bool:
        return self.page.query_selector(VERIFICATION_FORM) is not None

    def enter_verification_code(self, code: str) -> None:
        """Type the verification code into Greenhouse's verification input."""
        inp = self.page.query_selector(VERIFICATION_INPUT)
        if inp is None:
            logger.error("[greenhouse] Verification input not found.")
            return
        inp.triple_click()
        inp.type(code, delay=40)
        logger.info("[greenhouse] Entered verification code.")
        # Submit the code form
        submit = self.page.query_selector("button[type='submit'], input[type='submit']")
        if submit:
            submit.click()
            self.page.wait_for_load_state("networkidle", timeout=10_000)
