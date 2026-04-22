"""
utils/helpers.py — Shared utilities: logging setup, wait helpers, DOM helpers.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Callable, Optional, TypeVar

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

T = TypeVar("T")


def configure_logging(level: int = logging.INFO) -> None:
    """Set up a clean console logger for the entire jobapply package."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    )
    root = logging.getLogger("jobapply")
    root.setLevel(level)
    root.handlers = [handler]
    root.propagate = False


def wait_for_any(page: Page, selectors: list[str], timeout_ms: int = 10_000) -> Optional[str]:
    """
    Wait until any of the given CSS selectors appears in the DOM.

    Returns the first matching selector, or None if none appeared within the timeout.
    """
    deadline = time.time() + timeout_ms / 1_000
    while time.time() < deadline:
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    return sel
            except Exception:
                pass
        time.sleep(0.25)
    return None


def retry(fn: Callable[[], T], attempts: int = 3, delay: float = 1.0) -> T:
    """Call fn up to `attempts` times, sleeping `delay` seconds between retries."""
    last_exc: Exception = RuntimeError("retry called with attempts < 1")
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if i < attempts - 1:
                time.sleep(delay)
    raise last_exc


def scroll_to_bottom(page: Page) -> None:
    """Scroll the page to the bottom to trigger lazy-loaded content."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)


def get_visible_text(page: Page, selector: str) -> str:
    """Return the inner text of the first visible element matching selector."""
    el = page.query_selector(selector)
    if el and el.is_visible():
        return (el.inner_text() or "").strip()
    return ""


def human_delay(page: Page, min_ms: int = 300, max_ms: int = 900) -> None:
    """Introduce a short randomised pause to appear more human."""
    import random
    page.wait_for_timeout(random.randint(min_ms, max_ms))
