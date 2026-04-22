"""
gmail_reader.py — Extract verification codes sent by ATS platforms via Gmail.

Uses the Gmail API (OAuth2 service account or user credentials) to search
recent emails from known ATS senders and extract numeric codes via regex.

Setup:
  1. Enable the Gmail API in Google Cloud Console.
  2. Download credentials.json (OAuth2 desktop app) to this project root.
  3. On first run, a browser window opens to authorise access.
  4. Subsequent runs use the cached token in token.json.
"""

from __future__ import annotations

import base64
import logging
import os
import re
import time
from email import message_from_bytes
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")

# ATS senders that typically send verification emails.
ATS_SENDERS = [
    "no-reply@greenhouse.io",
    "notifications@greenhouse.io",
    "no-reply@lever.co",
    "noreply@lever.co",
    "no-reply@ashbyhq.com",
    "notifications@ashbyhq.com",
]

# Patterns for 4-8 digit verification codes.
CODE_PATTERNS = [
    re.compile(r"\b(\d{6})\b"),   # 6-digit (most common)
    re.compile(r"\b(\d{4})\b"),   # 4-digit
    re.compile(r"\b(\d{8})\b"),   # 8-digit
]


def _get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "Gmail API libraries not installed. Run:\n"
            "  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Gmail credentials not found at {CREDENTIALS_FILE}.\n"
                    "Download credentials.json from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())

    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    if mime_type.startswith("multipart/"):
        for part in payload.get("parts", []):
            text = _decode_body(part)
            if text:
                return text
    return ""


def _extract_code(text: str) -> Optional[str]:
    for pattern in CODE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def fetch_verification_code(
    sender_hint: Optional[str] = None,
    max_wait_seconds: int = 120,
    poll_interval: int = 5,
) -> Optional[str]:
    """
    Poll Gmail for a recent verification code email.

    Args:
        sender_hint: Narrow the search to emails from this sender address.
        max_wait_seconds: How long to keep polling before giving up.
        poll_interval: Seconds between each Gmail API call.

    Returns the extracted code string, or None if not found in time.
    """
    service = _get_gmail_service()
    senders = [sender_hint] if sender_hint else ATS_SENDERS
    query = " OR ".join(f"from:{s}" for s in senders) + " newer_than:5m"

    logger.info("Polling Gmail for verification code (up to %ds)…", max_wait_seconds)
    deadline = time.time() + max_wait_seconds

    while time.time() < deadline:
        results = service.users().messages().list(
            userId="me", q=query, maxResults=5
        ).execute()

        messages = results.get("messages", [])
        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me",
                id=msg_ref["id"],
                format="full",
            ).execute()

            body = _decode_body(msg.get("payload", {}))
            code = _extract_code(body)
            if code:
                logger.info("Verification code found: %s", code)
                return code

        logger.debug("No code yet — retrying in %ds…", poll_interval)
        time.sleep(poll_interval)

    logger.warning("Timed out waiting for verification code from Gmail.")
    return None
