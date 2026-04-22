"""
profile.py — Load and expose the user's profile YAML for field-filling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class UserProfile:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    @property
    def full_name(self) -> str:
        return self._data.get("name", {}).get("full", "")

    @property
    def first_name(self) -> str:
        return self._data.get("name", {}).get("first", "")

    @property
    def last_name(self) -> str:
        return self._data.get("name", {}).get("last", "")

    @property
    def email(self) -> str:
        return self._data.get("contact", {}).get("email", "")

    @property
    def phone(self) -> str:
        return self._data.get("contact", {}).get("phone", "")

    @property
    def linkedin(self) -> str:
        return self._data.get("contact", {}).get("linkedin", "")

    @property
    def github(self) -> str:
        return self._data.get("contact", {}).get("github", "")

    @property
    def website(self) -> str:
        return self._data.get("contact", {}).get("website", "")

    @property
    def location(self) -> dict[str, str]:
        return self._data.get("location", {})

    @property
    def work_authorization(self) -> str:
        return self._data.get("work_authorization", "")

    @property
    def raw(self) -> dict[str, Any]:
        return self._data

    # ------------------------------------------------------------------
    # Prompt serialisation
    # ------------------------------------------------------------------

    def to_prompt_block(self) -> str:
        """
        Flatten the profile to a readable key: value block for inclusion
        in Claude prompts.
        """
        lines: list[str] = []

        def _flatten(obj: Any, prefix: str = "") -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _flatten(v, f"{prefix}{k}." if prefix else f"{k}.")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    _flatten(item, f"{prefix}{i}.")
            else:
                key = prefix.rstrip(".")
                lines.append(f"  {key}: {obj}")

        _flatten(self._data)
        return "\n".join(lines)


def load_profile(path: Path | str) -> UserProfile:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Profile YAML not found: {path}\n"
            "Copy profile.example.yaml to profile.yaml and fill it in."
        )
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    logger.info("Loaded profile from %s (%d top-level keys)", path, len(data))
    return UserProfile(data)
