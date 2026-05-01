"""
Spike 002: Playwright-based replacement for download.py

Key improvements over the Selenium version:
- No ChromeDriver path needed — playwright manages its own browser
- context.request.get() shares the authenticated session (no cookie transfer)
- page.wait_for_selector() with proper timeouts replaces time.sleep() and WebDriverWait
- Community ID extracted from documents_url (fixes hardcoded 213519 bug)
"""

import os
import re
import sys
from urllib.parse import urlparse

# credentials.py lives in the project root, three levels above this spike
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import credentials

def extract_community_id(url: str) -> str:
    match = re.search(r'/c/(\d+)/', url)
    if not match:
        raise ValueError(f"Cannot extract community ID from URL: {url}")
    return match.group(1)

def download_pdfs():
    documents_url = credentials.documents_url
    download_dir = credentials.download_dir
    # Derive login URL from the same origin as documents_url — each Casavi tenant has its own /app/login
    origin = f"{urlparse(documents_url).scheme}://{urlparse(documents_url).netloc}"
    login_url = f"{origin}/app/login"

    community_id = extract_community_id(documents_url)
    folder_selector = "div.clickable.box-subhead--title.dashboard-tile-company-background"
    pdf_selector = f'a[href*="/api/v1/communities/{community_id}/documents/"]'

    os.makedirs(download_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        print(f"Navigating to login page: {login_url}")
        page.goto(login_url, timeout=20000)
        page.wait_for_selector('input[name="username"]', timeout=10000)
        page.fill('input[name="username"]', credentials.username)
        page.fill('input[name="password"]', credentials.password)
        page.click('button[data-testid="login-in"]')

        # Wait for SSO redirect back to documents (not login)
        try:
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
        except PlaywrightTimeoutError:
            print("ERROR: Login did not redirect. Check credentials.", file=sys.stderr)
            browser.close()
            return

        print(f"Login successful. Landed at: {page.url}")

        # Navigate to documents page after login
        print(f"Navigating to documents: {documents_url}")
        page.goto(documents_url, timeout=20000, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=10000)

        page.wait_for_selector(folder_selector, timeout=15000)

        # Click each folder to expand PDF links
        folders = page.query_selector_all(folder_selector)
        print(f"Found {len(folders)} folder(s). Expanding...")
        for i, folder in enumerate(folders):
            folder.click()
            try:
                page.wait_for_selector(pdf_selector, timeout=5000)
            except PlaywrightTimeoutError:
                print(f"  Folder {i+1}: no PDFs appeared within 5s, continuing.")

        # Collect all PDF links (deduplicate by href)
        pdf_links = page.query_selector_all(pdf_selector)
        seen = set()
        unique_links = []
        for link in pdf_links:
            href = link.get_attribute("href")
            if href and href not in seen:
                seen.add(href)
                unique_links.append((href, link.inner_text().strip()))

        print(f"Found {len(unique_links)} PDF link(s).")

        # Download each PDF using the authenticated browser context
        for pdf_url, text in unique_links:
            if pdf_url.startswith("/"):
                pdf_url = origin + pdf_url
            filename = text.replace(" ", "_") if text else pdf_url.split("/")[-1]
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            dest = os.path.join(download_dir, filename)

            response = context.request.get(pdf_url)
            if response.status == 200:
                with open(dest, "wb") as f:
                    f.write(response.body())
                print(f"  Downloaded: {filename}")
            else:
                print(f"  FAILED ({response.status}): {pdf_url}", file=sys.stderr)

        browser.close()

    print("Done.")

if __name__ == "__main__":
    download_pdfs()
