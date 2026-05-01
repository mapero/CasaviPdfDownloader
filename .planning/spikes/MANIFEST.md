# Spike Manifest

## Idea

Replace the Selenium + ChromeDriver based `download.py` with a more stable Playwright-based solution. The current script requires manual ChromeDriver version management, uses `time.sleep()` instead of proper waits, and relies on a fragile cookie-transfer workaround to authenticate HTTP downloads.

## Requirements

- Must not require a `chrome_driver_path` in credentials — browser managed automatically
- Must extract community ID from `documents_url` dynamically (no hardcoded IDs)
- Must use the authenticated browser session for downloads (no separate requests.Session)
- Must use proper wait conditions instead of `time.sleep()`

## Spikes

| # | Name | Type | Validates | Verdict | Tags |
|---|------|------|-----------|---------|------|
| 001 | playwright-install-verify | standard | Given Linux machine, when installing playwright + chromium, then headless browser runs | VALIDATED ✓ | playwright, python, headless, chromium, linux |
| 002 | playwright-casavi-migration | standard | Given Casavi credentials, when running Playwright script, then PDFs download without ChromeDriver or cookie transfer | VALIDATED ✓ | playwright, python, casavi, pdf-download, migration |
