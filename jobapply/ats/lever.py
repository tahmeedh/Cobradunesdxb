"""
ats/lever.py — Lever ATS handler.

Lever domains:
  - jobs.lever.co/<company>/<job-id>
  - jobs.lever.co/<company>/<job-id>/apply
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from jobapply.ats.base import BaseATSHandler

logger = logging.getLogger(__name__)

LEVER_PATTERN = re.compile(r"jobs\.lever\.co", re.IGNORECASE)
LEVER_SENDER = "no-reply@lever.co"

FORM_SELECTOR = ".application-form, form.application, #application-form"
RESUME_UPLOAD = "input[type='file'][name='resume'], input[type='file'][accept*='pdf']"
VERIFICATION_FORM = ".verification-page, #verification-form"
VERIFICATION_INPUT = "input[name='code'], input[placeholder*='code' i]"


class LeverHandler(BaseATSHandler):
    name = "lever"

    @classmethod
    def matches(cls, url: str) -> bool:
        return bool(LEVER_PATTERN.search(url))

    def wait_for_form(self, timeout_ms: int = 15_000) -> None:
        logger.info("[lever] Waiting for application form…")
        try:
            self.page.wait_for_selector(FORM_SELECTOR, timeout=timeout_ms, state="visible")
            logger.info("[lever] Form is ready.")
        except PlaywrightTimeoutError:
            logger.warning("[lever] Form not found within %dms — proceeding anyway.", timeout_ms)

    def before_fill(self) -> None:
        self.dismiss_cookie_banner()
        # Lever sometimes shows a "Continue with email" prompt before the form.
        self._dismiss_email_prompt()

    def _dismiss_email_prompt(self) -> None:
        try:
            btn = self.page.wait_for_selector(
                "button:has-text('Continue'), button:has-text('Apply')",
                timeout=3_000,
                state="visible",
            )
            if btn:
                btn.click()
                self.page.wait_for_load_state("networkidle", timeout=5_000)
        except PlaywrightTimeoutError:
            pass

    def verification_code_sender(self) -> Optional[str]:
        return LEVER_SENDER

    def needs_verification_code(self) -> bool:
        return self.page.query_selector(VERIFICATION_FORM) is not None

    def enter_verification_code(self, code: str) -> None:
        inp = self.page.query_selector(VERIFICATION_INPUT)
        if inp is None:
            logger.error("[lever] Verification input not found.")
            return
        inp.triple_click()
        inp.type(code, delay=40)
        logger.info("[lever] Entered verification code.")
        submit = self.page.query_selector("button[type='submit']")
        if submit:
            submit.click()
            self.page.wait_for_load_state("networkidle", timeout=10_000)
