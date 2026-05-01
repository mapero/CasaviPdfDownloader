"""
Spike 001: Verify Playwright installs and headless Chromium runs on this Linux machine.
Run: python verify.py
Expected: prints page title and "PASS" — no ChromeDriver, no manual browser setup.
"""

from playwright.sync_api import sync_playwright

def main():
    print("Launching headless Chromium via Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page()
        page.goto("https://example.com", timeout=15000)
        title = page.title()
        browser.close()

    print(f"Page title: {title!r}")
    assert "Example" in title, f"Unexpected title: {title}"
    print("PASS — Playwright + headless Chromium working.")

if __name__ == "__main__":
    main()
