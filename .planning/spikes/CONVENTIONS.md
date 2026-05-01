# Spike Conventions

Patterns and stack choices established across spike sessions.

## Stack

- **Language:** Python 3 (project language)
- **Virtualenv:** `myenv/` at project root — activate with `source myenv/bin/activate`
- **Browser automation:** Playwright sync_api (validated in Spike 001)

## Structure

- Spike scripts run from the project root (so `import credentials` resolves correctly)
- Verification scripts named `verify.py` for install/setup spikes, `download_playwright.py` for the main migration

## Patterns

- **Linux headless args:** Always include `--no-sandbox --disable-dev-shm-usage` in `p.chromium.launch(args=[...])`
- **Community ID:** Extract from `documents_url` with `re.search(r'/c/(\d+)/', url).group(1)` — never hardcode

## Tools & Libraries

- `playwright==1.x` (latest, installed via pip) — works cleanly in `myenv` virtualenv
- `playwright install chromium` — one-time per machine, cached in `~/.cache/ms-playwright/`
