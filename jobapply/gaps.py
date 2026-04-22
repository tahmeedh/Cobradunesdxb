"""
gaps.py — Detect empty required fields that Simplify did not fill.

Scans the active page for <input>, <select>, and <textarea> elements that are:
  - marked required (required attribute or aria-required="true")
  - still empty / at their default placeholder value
  - visible to the user (not hidden, not disabled)

Returns a list of FieldGap descriptors that claude_fill.py uses to decide
what value to inject.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


@dataclass
class FieldGap:
    """A single required field that still needs a value."""

    tag: str                        # input | select | textarea
    field_type: str                 # text | email | tel | select | textarea …
    name: str                       # name attribute (or id / aria-label as fallback)
    label: str                      # visible label text, best-effort
    placeholder: str                # placeholder text if present
    selector: str                   # CSS selector to locate the element again
    current_value: str              # current value (empty or default)
    extra: dict[str, Any] = field(default_factory=dict)


# JS that runs inside the page and returns serialisable gap descriptors.
_DETECT_GAPS_JS = """
() => {
    const isVisible = el => {
        const s = window.getComputedStyle(el);
        return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0'
               && el.offsetParent !== null;
    };

    const labelFor = el => {
        // 1. <label for="id">
        if (el.id) {
            const lbl = document.querySelector(`label[for="${el.id}"]`);
            if (lbl) return lbl.innerText.trim();
        }
        // 2. wrapping <label>
        const parent = el.closest('label');
        if (parent) return parent.innerText.trim();
        // 3. aria-label / aria-labelledby
        if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
        const lblId = el.getAttribute('aria-labelledby');
        if (lblId) {
            const lbl = document.getElementById(lblId);
            if (lbl) return lbl.innerText.trim();
        }
        return '';
    };

    const uniqueSelector = el => {
        if (el.id) return `#${el.id}`;
        if (el.name) return `${el.tagName.toLowerCase()}[name="${el.name}"]`;
        // fallback: nth-of-type path — good enough for one-shot automation
        let path = [];
        let cur = el;
        while (cur && cur !== document.body) {
            let idx = 1;
            let sib = cur.previousElementSibling;
            while (sib) { if (sib.tagName === cur.tagName) idx++; sib = sib.previousElementSibling; }
            path.unshift(`${cur.tagName.toLowerCase()}:nth-of-type(${idx})`);
            cur = cur.parentElement;
        }
        return path.join(' > ');
    };

    const gaps = [];
    const candidates = document.querySelectorAll('input, select, textarea');

    for (const el of candidates) {
        const required = el.required || el.getAttribute('aria-required') === 'true';
        if (!required) continue;
        if (el.disabled || el.readOnly) continue;
        if (!isVisible(el)) continue;

        const tag = el.tagName.toLowerCase();
        const type = el.type || tag;
        const value = el.value || '';

        // Consider the field empty if value is blank or only whitespace.
        const isEmpty = value.trim() === '';

        // For selects, the first option is usually a placeholder.
        const isDefaultSelect = tag === 'select' && el.selectedIndex <= 0;

        if (!isEmpty && !isDefaultSelect) continue;

        gaps.push({
            tag,
            field_type: type,
            name: el.name || el.id || '',
            label: labelFor(el),
            placeholder: el.placeholder || '',
            selector: uniqueSelector(el),
            current_value: value,
        });
    }
    return gaps;
}
"""


def detect_gaps(page: Page) -> list[FieldGap]:
    """Scan the page and return all empty required fields."""
    raw: list[dict] = page.evaluate(_DETECT_GAPS_JS)
    gaps = [FieldGap(**item) for item in raw]
    if gaps:
        logger.info("Detected %d empty required field(s):", len(gaps))
        for g in gaps:
            logger.info("  [%s] name=%r label=%r placeholder=%r", g.tag, g.name, g.label, g.placeholder)
    else:
        logger.info("No empty required fields detected — Simplify filled everything.")
    return gaps
