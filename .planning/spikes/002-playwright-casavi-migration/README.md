---
spike: "002"
name: playwright-casavi-migration
type: standard
validates: "Given Casavi credentials, when running the Playwright script, then PDFs download correctly without any manual ChromeDriver management or cookie transfer"
verdict: PENDING
related: ["001"]
tags: [playwright, python, casavi, pdf-download, migration]
---

# Spike 002: Playwright Casavi Migration

## What This Validates

Given valid credentials in `credentials.py`, when running `download_playwright.py`, then:
- All PDF links are discovered (using the community ID extracted from `documents_url`, not hardcoded)
- PDFs download successfully via `context.request.get()` — same authenticated session as the browser, no cookie transfer
- No ChromeDriver path required in credentials

## Research

### Stability problems in original Selenium script

| Problem | Root Cause | Playwright Fix |
|---------|-----------|---------------|
| ChromeDriver version mismatch | Must manually match ChromeDriver to Chrome version | `playwright install chromium` manages browser automatically |
| `time.sleep(1)` after login | No reliable wait condition | `page.wait_for_url(lambda url: "login" not in url)` |
| Cookie transfer to `requests.Session` | Selenium doesn't share session with HTTP client | `context.request.get()` shares browser auth session directly |
| Hardcoded community ID `213519` in CSS selector | Never parameterized | Extracted dynamically from `documents_url` via regex |

### Bug discovered: hardcoded community ID

The original `download.py` uses selector `'a[href*="/api/v1/communities/213519/documents/"]'`
but the current `credentials.py` uses community `618711` at `portal.mpv-verwaltung.de`.
**The original script finds zero PDFs with this configuration.**

The Playwright version fixes this by extracting the community ID from `documents_url`:
```python
community_id = re.search(r'/c/(\d+)/', documents_url).group(1)
pdf_selector = f'a[href*="/api/v1/communities/{community_id}/documents/"]'
```

## How to Run

```bash
source myenv/bin/activate
# make sure credentials.py has valid username and password
python .planning/spikes/002-playwright-casavi-migration/download_playwright.py
```

## What to Expect

```
Navigating to login page: https://my.casavi.com/app/login
Login successful.
Navigating to documents: https://portal.mpv-verwaltung.de/app/c/618711/info/documents
Found N folder(s). Expanding...
Found M PDF link(s).
  Downloaded: document_name.pdf
  ...
Done.
```

PDFs appear in `./DownloadedFiles/`.

## Investigation Trail

- Syntax and imports verified: clean
- Community ID extraction tested against all known URL variants (213519, 87346, 618711) — all pass
- Discovered hardcoded community ID bug in original script — current config would return 0 PDFs
- `context.request.get()` confirmed to share browser session — no cookie transfer code needed
- `--no-sandbox --disable-dev-shm-usage` args inherited from Spike 001 (required for Linux)
- Login wait uses `wait_for_url` predicate instead of `time.sleep(1)`
- Deduplication added: original script would download duplicates if a PDF link appears in multiple folders

## Results

Pending human verification with real credentials.
