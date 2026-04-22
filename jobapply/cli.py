"""
cli.py — Typer-based CLI entry point for jobapply.
"""

from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="jobapply",
    help="Automate job applications using Chrome, Simplify, and Claude AI.",
    add_completion=False,
)


@app.command("smoke-test")
def smoke_test(
    profile_dir: Optional[Path] = typer.Option(
        None,
        "--profile-dir",
        help="Chrome user data directory (parent of Default/, Profile 1/, …).",
    ),
    profile_directory: str = typer.Option(
        "Default",
        "--profile-directory",
        help="Chrome profile sub-directory name.",
    ),
) -> None:
    """Launch Chrome with your real profile and navigate to example.com as a smoke test."""
    from jobapply.browser import run_smoke_test

    run_smoke_test(profile_dir=profile_dir, profile_directory=profile_directory)


@app.command("apply")
def apply(
    url: str = typer.Argument(..., help="Job application URL to open."),
    profile_dir: Optional[Path] = typer.Option(
        None,
        "--profile-dir",
        help="Chrome user data directory.",
    ),
    profile_directory: str = typer.Option(
        "Default",
        "--profile-directory",
        help="Chrome profile sub-directory name.",
    ),
    profile_yaml: Path = typer.Option(
        Path("profile.yaml"),
        "--profile",
        help="Path to your user profile YAML.",
    ),
) -> None:
    """Open a job application URL, trigger Simplify autofill, then fill remaining gaps with Claude."""
    typer.echo(f"[jobapply] Opening: {url}")
    typer.echo("[jobapply] apply command coming soon — scaffold is ready.")


if __name__ == "__main__":
    app()
