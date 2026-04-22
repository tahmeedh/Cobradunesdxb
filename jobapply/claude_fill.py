"""
claude_fill.py — Use Claude (claude-sonnet-4-5) to fill empty application fields.

For each FieldGap, we build a focused prompt that includes:
  - The field's label, type, placeholder, and surrounding context
  - The user's profile YAML (name, contact, work history, skills, …)
Claude returns the best value to type into that field.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import anthropic

from jobapply.gaps import FieldGap
from jobapply.profile import UserProfile

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 256


def _build_prompt(gap: FieldGap, profile: UserProfile, page_context: str = "") -> str:
    profile_block = profile.to_prompt_block()
    return f"""You are filling out a job application form on behalf of the user.

USER PROFILE:
{profile_block}

FIELD TO FILL:
  Tag:         {gap.tag}
  Type:        {gap.field_type}
  Name attr:   {gap.name}
  Label:       {gap.label}
  Placeholder: {gap.placeholder}
{f"  Page context snippet: {page_context}" if page_context else ""}

INSTRUCTIONS:
- Return ONLY the exact value to type into this field. No explanation.
- If the field is a select (dropdown), return the exact option text to choose.
- If you cannot determine an appropriate value, return the empty string.
- Never fabricate information not present in the user profile.
- Keep your response to a single line.

VALUE:"""


def fill_gaps_with_claude(
    gaps: list[FieldGap],
    profile: UserProfile,
    page_context: str = "",
) -> dict[str, str]:
    """
    Ask Claude to suggest a value for each gap.

    Returns a dict mapping each gap's selector to the suggested value.
    """
    if not gaps:
        return {}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    results: dict[str, str] = {}

    for gap in gaps:
        logger.info("Asking Claude to fill: label=%r name=%r", gap.label, gap.name)
        prompt = _build_prompt(gap, profile, page_context)

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            value = message.content[0].text.strip()
            logger.info("  → Claude suggests: %r", value)
            results[gap.selector] = value
        except anthropic.APIError as exc:
            logger.error("Claude API error for field %r: %s", gap.name, exc)
            results[gap.selector] = ""

    return results


def apply_values_to_page(page: Any, fill_map: dict[str, str]) -> None:
    """
    Type or select the Claude-suggested values into the corresponding page elements.
    """
    for selector, value in fill_map.items():
        if not value:
            continue
        try:
            el = page.query_selector(selector)
            if el is None:
                logger.warning("Element not found for selector: %s", selector)
                continue

            tag = el.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                el.select_option(label=value)
                logger.info("Selected option %r for selector %s", value, selector)
            else:
                el.triple_click()
                el.type(value, delay=40)
                logger.info("Typed %r into selector %s", value, selector)
        except Exception as exc:
            logger.error("Failed to fill selector %s: %s", selector, exc)
