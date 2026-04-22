# jobapply

A Python CLI that automates job applications using your real Chrome browser (with extensions and cookies intact), the [Simplify](https://simplify.jobs) Chrome extension, and Claude AI.

**Never auto-submits** — always pauses for your review before you hit Submit.

---

## How it works

1. **Connects to your real Chrome** — uses `launch_persistent_context()` so your Simplify extension, LinkedIn session, and all cookies are available.
2. **Triggers Simplify autofill** — detects Simplify's injected button and clicks it.
3. **Detects remaining gaps** — scans for required fields still empty after Simplify runs.
4. **Fills gaps with Claude** — sends each empty field + your profile YAML to `claude-sonnet-4-5` to generate the right answer.
5. **Reads Gmail for verification codes** — if an ATS emails a code during the flow, it's fetched automatically.
6. **Pauses for your review** — you submit manually.

Supported ATS platforms: **Greenhouse**, **Lever**, **Ashby**

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chrome
```

### 2. Configure your profile

```bash
cp profile.example.yaml profile.yaml
# Edit profile.yaml with your real info
```

### 3. Set your API key

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### 4. (Optional) Gmail verification codes

Follow the [Gmail API quickstart](https://developers.google.com/gmail/api/quickstart/python) to download `credentials.json`, then place it in this directory. The first run will open a browser to authorise access.

---

## Usage

### Smoke test — verify Chrome profile connection

> **Chrome must be fully closed before running this.**

```bash
python -m jobapply.browser
# or with the CLI:
python jobapply/cli.py smoke-test
```

Expected output:
```
[browser] Chrome user data dir : /Users/you/Library/Application Support/Google/Chrome
[browser] Profile               : Default
[browser] Launching Chrome with your profile…
[browser] Navigating to https://example.com …
[browser] Page title: 'Example Domain'  ✓
[browser] Keeping browser open for 10 s — close this window to exit early.
[browser] Browser closed cleanly.
```

### Apply to a job

```bash
python jobapply/cli.py apply "https://jobs.lever.co/company/job-id/apply"
```

---

## Project structure

```
jobapply/
├── cli.py            # Typer CLI entry point
├── browser.py        # Chrome profile connection (Playwright)
├── simplify.py       # Simplify extension detection + autofill trigger
├── gaps.py           # Empty required field detection
├── claude_fill.py    # Claude API field-filling
├── gmail_reader.py   # Gmail API verification code reader
├── profile.py        # User profile YAML loader
├── ats/
│   ├── base.py       # Abstract ATS handler
│   ├── greenhouse.py
│   ├── lever.py
│   └── ashby.py
└── utils/
    └── helpers.py    # Logging, wait helpers, DOM utilities
config.yaml           # Runtime config
profile.example.yaml  # Template — copy to profile.yaml
requirements.txt
.env.example
```

---

## Important notes

- **Close Chrome before running** — Playwright needs exclusive access to the profile directory.
- **Extensions require non-headless mode** — `headless: false` is the default.
- `profile.yaml` and `token.json` are gitignored — never commit personal data.
