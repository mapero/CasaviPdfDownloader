---
spike: "001"
name: playwright-install-verify
type: standard
validates: "Given this Linux machine, when installing playwright + running playwright install chromium, then headless Chromium launches and navigates a URL without any manual browser binary management"
verdict: VALIDATED
related: ["002"]
tags: [playwright, python, headless, chromium, linux]
---

# Spike 001: Playwright Install Verify

## What This Validates

Given this Linux machine with pip available, when installing `playwright` and running `playwright install chromium`, then a headless Chromium browser launches and navigates a real URL — no manual ChromeDriver download, no version matching.

## Research

| Approach | Tool | Pros | Cons | Status |
|----------|------|------|------|--------|
| Selenium + ChromeDriver | selenium + chromedriver binary | Established | Manual binary management, version fragility | Current (fragile) |
| Playwright | playwright sync_api | Auto-manages browser, built-in waits, context.request shares auth session | Heavier download (~170MB once) | **Chosen** |

**Chosen:** Playwright — the browser is managed by `playwright install`, never needs manual updates.

## How to Run

```bash
source myenv/bin/activate
pip install playwright
playwright install chromium
python .planning/spikes/001-playwright-install-verify/verify.py
```

## What to Expect

```
Launching headless Chromium via Playwright...
Page title: 'Example Domain'
PASS — Playwright + headless Chromium working.
```

## Investigation Trail

- Installed via `pip install playwright` in `myenv` virtualenv — clean install, no conflicts
- `playwright install chromium` downloads ~170MB to `~/.cache/ms-playwright/` (one-time, cached per machine)
- Added `--no-sandbox --disable-dev-shm-usage` launch args — required for Linux environments without full X server setup
- Navigated `example.com`, got title `'Example Domain'`, assertion passed
- No ChromeDriver zip, no `.deb` file, no path config needed

## Results

**Verdict: VALIDATED**

Playwright installs cleanly and headless Chromium runs on this Linux machine. The `--no-sandbox` flag is needed (standard for Linux headless automation). Browser is auto-managed — future `pip install playwright --upgrade` + `playwright install chromium` is the entire maintenance story.

Impact on Spike 002: proceed with confidence. The runtime works.
