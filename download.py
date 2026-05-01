"""
Casavi PDF Downloader — Playwright-based, multi-tenant.

Reads tenant list from credentials.py. Each tenant is a separate Casavi instance
with its own session; login is performed once per tenant.

Downloads are saved to: <download_dir>/<tenant_name>/<filename>.pdf
"""

import os
import re
import sys
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import credentials


def extract_community_id(url: str) -> str:
    match = re.search(r'/c/(\d+)/', url)
    if not match:
        raise ValueError(f"Cannot extract community ID from URL: {url}")
    return match.group(1)


def get_tenants():
    """Return list of (name, documents_url) tuples from credentials."""
    if hasattr(credentials, 'tenants'):
        return [(t['name'], t['url']) for t in credentials.tenants]
    # Backward-compatible: single documents_url
    url = credentials.documents_url
    name = urlparse(url).netloc.split('.')[0]
    return [(name, url)]


def download_tenant(page, context, name: str, documents_url: str, download_dir: str):
    origin = f"{urlparse(documents_url).scheme}://{urlparse(documents_url).netloc}"
    login_url = f"{origin}/app/login"
    community_id = extract_community_id(documents_url)
    folder_selector = "div.clickable.box-subhead--title.dashboard-tile-company-background"
    pdf_selector = f'a[href*="/api/v1/communities/{community_id}/documents/"]'
    tenant_dir = os.path.join(download_dir, name)
    os.makedirs(tenant_dir, exist_ok=True)

    print(f"\n[{name}] Logging in at {login_url}")
    page.goto(login_url, timeout=20000)
    page.wait_for_selector('input[name="username"]', timeout=10000)
    page.fill('input[name="username"]', credentials.username)
    page.fill('input[name="password"]', credentials.password)
    page.click('button[data-testid="login-in"]')

    try:
        page.wait_for_url(lambda url: "login" not in url, timeout=15000)
    except PlaywrightTimeoutError:
        print(f"[{name}] ERROR: Login failed — check credentials.", file=sys.stderr)
        return

    print(f"[{name}] Login successful. Navigating to documents...")
    page.goto(documents_url, timeout=20000, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=10000)

    try:
        page.wait_for_selector(folder_selector, timeout=15000)
    except PlaywrightTimeoutError:
        print(f"[{name}] ERROR: Documents page did not load — selector not found.", file=sys.stderr)
        return

    folders = page.query_selector_all(folder_selector)
    print(f"[{name}] Found {len(folders)} folder(s). Expanding...")
    for folder in folders:
        folder.click()
        try:
            page.wait_for_selector(pdf_selector, timeout=5000)
        except PlaywrightTimeoutError:
            pass

    pdf_links = page.query_selector_all(pdf_selector)
    seen = set()
    unique_links = []
    for link in pdf_links:
        href = link.get_attribute("href")
        if href and href not in seen:
            seen.add(href)
            unique_links.append((href, link.inner_text().strip()))

    print(f"[{name}] Found {len(unique_links)} PDF(s). Downloading...")
    for pdf_url, text in unique_links:
        if pdf_url.startswith("/"):
            pdf_url = origin + pdf_url
        filename = text.replace(" ", "_") if text else pdf_url.split("/")[-1]
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        dest = os.path.join(tenant_dir, filename)

        response = context.request.get(pdf_url)
        if response.status == 200:
            with open(dest, "wb") as f:
                f.write(response.body())
            print(f"  [{name}] Downloaded: {filename}")
        else:
            print(f"  [{name}] FAILED ({response.status}): {pdf_url}", file=sys.stderr)


def main():
    tenants = get_tenants()
    download_dir = credentials.download_dir

    print(f"Tenants: {[name for name, _ in tenants]}")

    with sync_playwright() as p:
        for name, documents_url in tenants:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            try:
                download_tenant(page, context, name, documents_url, download_dir)
            finally:
                browser.close()

    print("\nAll tenants done.")


if __name__ == "__main__":
    main()
