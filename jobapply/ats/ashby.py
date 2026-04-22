"""
ats/ashby.py — Ashby ATS handler.

Ashby domains:
  - jobs.ashbyhq.com/<company>/<job-id>
  - app.ashbyhq.com/…
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from jobapply.ats.base import BaseATSHandler

logger = logging.getLogger(__name__)

ASHBY_PATTERN = re.compile(r"(jobs\.ashbyhq\.com|app\.ashbyhq\.com)", re.IGNORECASE)
ASHBY_SENDER = "no-reply@ashbyhq.com"

FORM_SELECTOR = "form.ashby-application-form, [data-testid='application-form'], form"
VERIFICATION_FORM = "[data-testid='verification'], .verification-container"
VERIFICATION_INPUT = "input[name='code'], input[data-testid='verification-code-input']"


class AshbyHandler(BaseATSHandler):
    name = "ashby"

    @classmethod
    def matches(cls, url: str) -> bool:
        return bool(ASHBY_PATTERN.search(url))

    def wait_for_form(self, timeout_ms: int = 15_000) -> None:
        logger.info("[ashby] Waiting for application form…")
        try:
            self.page.wait_for_selector(FORM_SELECTOR, timeout=timeout_ms, state="visible")
            logger.info("[ashby] Form is ready.")
        except PlaywrightTimeoutError:
            logger.warning("[ashby] Form not found within %dms — proceeding anyway.", timeout_ms)

    def before_fill(self) -> None:
        self.dismiss_cookie_banner()

    def verification_code_sender(self) -> Optional[str]:
        return ASHBY_SENDER

    def needs_verification_code(self) -> bool:
        return self.page.query_selector(VERIFICATION_FORM) is not None

    def enter_verification_code(self, code: str) -> None:
        inp = self.page.query_selector(VERIFICATION_INPUT)
        if inp is None:
            logger.error("[ashby] Verification input not found.")
            return
        inp.triple_click()
        inp.type(code, delay=40)
        logger.info("[ashby] Entered verification code.")
        submit = self.page.query_selector("button[type='submit']")
        if submit:
            submit.click()
            self.page.wait_for_load_state("networkidle", timeout=10_000)
