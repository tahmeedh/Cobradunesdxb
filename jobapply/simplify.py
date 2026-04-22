"""
simplify.py — Detect the Simplify Chrome extension and trigger its autofill button.

Simplify injects a floating button (or toolbar) into ATS job pages. We detect
it by looking for its shadow DOM host element or known CSS classes, then click
the autofill trigger programmatically.
"""

import asyncio
import logging
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

# Simplify renders a host element with this id or data attribute.
# Update these selectors as Simplify's DOM evolves.
SIMPLIFY_HOST_SELECTORS = [
    "#simplify-extension-root",
    "[data-simplify-autofill]",
    "simplify-autofill",          # web component tag
]

SIMPLIFY_BUTTON_SELECTORS = [
    "[data-simplify='autofill-btn']",
    ".simplify-autofill-button",
    "#simplify-autofill-trigger",
]

AUTOFILL_SETTLE_MS = 3_000   # wait after clicking for Simplify to fill fields


def detect_simplify(page: Page, timeout_ms: int = 5_000) -> bool:
    """Return True if the Simplify extension host element is present on the page."""
    for selector in SIMPLIFY_HOST_SELECTORS:
        try:
            page.wait_for_selector(selector, timeout=timeout_ms, state="attached")
            logger.info("Simplify extension detected via selector: %s", selector)
            return True
        except PlaywrightTimeoutError:
            continue
    logger.warning("Simplify extension NOT detected. Is it installed and enabled?")
    return False


def trigger_autofill(page: Page, timeout_ms: int = 5_000) -> bool:
    """
    Click Simplify's autofill button.

    Returns True if the button was found and clicked, False otherwise.
    """
    for selector in SIMPLIFY_BUTTON_SELECTORS:
        try:
            btn = page.wait_for_selector(selector, timeout=timeout_ms, state="visible")
            if btn:
                btn.click()
                logger.info("Simplify autofill button clicked (%s).", selector)
                page.wait_for_timeout(AUTOFILL_SETTLE_MS)
                return True
        except PlaywrightTimeoutError:
            continue

    # Fallback: try to call the extension's JS API directly if it exposes one.
    triggered = page.evaluate(
        """() => {
            if (window.__simplifyAutofill && typeof window.__simplifyAutofill === 'function') {
                window.__simplifyAutofill();
                return true;
            }
            return false;
        }"""
    )
    if triggered:
        logger.info("Simplify autofill triggered via window.__simplifyAutofill().")
        page.wait_for_timeout(AUTOFILL_SETTLE_MS)
        return True

    logger.warning("Could not find Simplify autofill button. Manual fill may be needed.")
    return False


def run_simplify(page: Page) -> bool:
    """Detect Simplify and trigger autofill. Returns True on success."""
    if not detect_simplify(page):
        return False
    return trigger_autofill(page)
