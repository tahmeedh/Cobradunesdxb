"""
browser.py — Launch Playwright connected to the user's real Chrome profile.

Uses launch_persistent_context() so Chrome extensions (Simplify, etc.) and
existing session cookies are available. Chrome must be fully closed before
running this — Playwright takes exclusive lock on the profile directory.
"""

import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import Playwright, sync_playwright


def get_default_chrome_user_data_dir() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    elif system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        return Path(local_app_data) / "Google" / "Chrome" / "User Data"
    else:
        # Linux
        return Path.home() / ".config" / "google-chrome"


def is_chrome_running() -> bool:
    system = platform.system()
    try:
        if system == "Windows":
            output = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
                stderr=subprocess.DEVNULL,
            ).decode()
            return "chrome.exe" in output.lower()
        else:
            output = subprocess.check_output(
                ["pgrep", "-x", "Google Chrome" if system == "Darwin" else "google-chrome"],
                stderr=subprocess.DEVNULL,
            ).decode()
            return bool(output.strip())
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        # pgrep/tasklist not available — skip the check
        return False


def launch_chrome_with_profile(
    playwright: Playwright,
    user_data_dir: Path,
    profile_directory: str = "Default",
    headless: bool = False,
) -> tuple:
    """
    Launch Chrome using launch_persistent_context() so the real profile,
    cookies, extensions, and local storage are all available.

    Returns (context, page).
    """
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        channel="chrome",
        headless=headless,
        args=[
            f"--profile-directory={profile_directory}",
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        ignore_default_args=["--enable-automation"],
    )

    # Re-use an existing page if Chrome opened one, otherwise create one.
    page = context.pages[0] if context.pages else context.new_page()
    return context, page


def run_smoke_test(profile_dir: Path | None = None, profile_directory: str = "Default") -> None:
    """
    Smoke-test: open example.com with the user's real Chrome profile and
    print the page title. Keeps the browser open for 10 s so you can see it.
    """
    user_data_dir = profile_dir or get_default_chrome_user_data_dir()

    print(f"[browser] Chrome user data dir : {user_data_dir}")
    print(f"[browser] Profile               : {profile_directory}")

    if not user_data_dir.exists():
        print(
            f"[browser] WARNING: Chrome user data directory not found: {user_data_dir}\n"
            "          Make sure Google Chrome is installed and has been launched at least once."
        )
        sys.exit(1)

    if is_chrome_running():
        print(
            "[browser] ERROR: Chrome is currently running.\n"
            "          Please quit Chrome completely before launching jobapply.\n"
            "          Playwright needs exclusive access to the profile directory."
        )
        sys.exit(1)

    print("[browser] Launching Chrome with your profile…")

    with sync_playwright() as pw:
        context, page = launch_chrome_with_profile(
            pw,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory,
        )

        print("[browser] Navigating to https://example.com …")
        page.goto("https://example.com", wait_until="domcontentloaded")
        title = page.title()
        print(f"[browser] Page title: {title!r}  ✓")

        print("[browser] Keeping browser open for 10 s — close this window to exit early.")
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            pass

        context.close()
        print("[browser] Browser closed cleanly.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Chrome profile smoke test")
    parser.add_argument(
        "--profile-dir",
        type=Path,
        default=None,
        help="Override Chrome user data directory (parent of Default/, Profile 1/, …)",
    )
    parser.add_argument(
        "--profile-directory",
        default="Default",
        help="Which Chrome profile sub-directory to use (default: 'Default')",
    )
    args = parser.parse_args()

    run_smoke_test(profile_dir=args.profile_dir, profile_directory=args.profile_directory)
