"""
Casavi PDF Downloader — Playwright-based, multi-tenant.

Reads tenant list from credentials.py. Each tenant is a separate Casavi instance
with its own session; login is performed once per tenant.

Downloads are saved to: <download_dir>/<tenant_name>/<filename>.pdf
Already-downloaded doc IDs are tracked in downloaded.yaml so files can be moved
(e.g. to Paperless) without being re-downloaded.
"""

import os
import re
import sys
from urllib.parse import urlparse

import yaml
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import credentials

def state_file(download_dir: str) -> str:
    return os.path.join(download_dir, "downloaded.yaml")


def extract_community_id(url: str) -> str:
    match = re.search(r'/c/(\d+)/', url)
    if not match:
        raise ValueError(f"Cannot extract community ID from URL: {url}")
    return match.group(1)


def get_tenants():
    """Return list of (name, documents_url) tuples from credentials."""
    if hasattr(credentials, 'tenants'):
        return [(t['name'], t['url']) for t in credentials.tenants]
    url = credentials.documents_url
    name = urlparse(url).netloc.split('.')[0]
    return [(name, url)]


def load_state(download_dir: str) -> dict:
    """Load downloaded doc IDs from YAML. Returns {tenant: set(doc_ids)}."""
    path = state_file(download_dir)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return {tenant: set(ids) for tenant, ids in data.items()}


def save_state(state: dict, download_dir: str):
    """Persist state to YAML. Converts sets to sorted lists for readability."""
    with open(state_file(download_dir), "w") as f:
        yaml.dump({tenant: sorted(ids) for tenant, ids in state.items()},
                  f, default_flow_style=False, allow_unicode=True)


def download_tenant(page, context, name: str, documents_url: str,
                    download_dir: str, state: dict):
    origin = f"{urlparse(documents_url).scheme}://{urlparse(documents_url).netloc}"
    community_id = extract_community_id(documents_url)
    folder_selector = "div.clickable.box-subhead--title.dashboard-tile-company-background"
    pdf_selector = f'a[href*="/api/v1/communities/{community_id}/documents/"]'
    tenant_dir = os.path.join(download_dir, "files", name)
    os.makedirs(tenant_dir, exist_ok=True)
    downloaded = state.setdefault(name, set())

    # Navigate to documents first so the SSO redirect carries ?next= back correctly
    print(f"\n[{name}] Navigating to documents: {documents_url}")
    try:
        page.goto(documents_url, timeout=20000, wait_until="domcontentloaded")
    except Exception:
        pass

    # Wait for either the login form or the folder elements
    login_input = page.locator('input[name="username"]')
    folder_el = page.locator(folder_selector)
    try:
        page.locator(f'input[name="username"], {folder_selector}').first.wait_for(timeout=15000)
    except PlaywrightTimeoutError:
        print(f"[{name}] ERROR: Neither login form nor documents loaded.", file=sys.stderr)
        return

    if login_input.is_visible():
        print(f"[{name}] Login form detected, authenticating...")
        page.fill('input[name="username"]', credentials.username)
        page.fill('input[name="password"]', credentials.password)
        page.click('button[data-testid="login-in"]')
        try:
            page.wait_for_selector(folder_selector, timeout=15000)
        except PlaywrightTimeoutError:
            pass

    # Some portals redirect to home after login rather than back to documents
    if not folder_el.first.is_visible():
        try:
            page.goto(documents_url, timeout=20000, wait_until="domcontentloaded")
        except Exception:
            pass

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
        doc_id = urlparse(pdf_url).path.rstrip("/").split("/")[-1]

        if doc_id in downloaded:
            print(f"  [{name}] Skipped (already downloaded): {doc_id}")
            continue

        base = text.replace(" ", "_") if text else doc_id
        if not base.endswith(".pdf"):
            base += ".pdf"
        filename = f"{doc_id}_{base}"
        dest = os.path.join(tenant_dir, filename)

        response = context.request.get(pdf_url)
        if response.status == 200:
            with open(dest, "wb") as f:
                f.write(response.body())
            downloaded.add(doc_id)
            save_state(state, download_dir)
            print(f"  [{name}] Downloaded: {filename}")
        else:
            print(f"  [{name}] FAILED ({response.status}): {pdf_url}", file=sys.stderr)


def main():
    tenants = get_tenants()
    download_dir = credentials.download_dir
    os.makedirs(download_dir, exist_ok=True)
    state = load_state(download_dir)

    print(f"Tenants: {[name for name, _ in tenants]}")

    record_video = "--video" in sys.argv
    video_dir = "./debug-videos"
    if record_video:
        os.makedirs(video_dir, exist_ok=True)

    with sync_playwright() as p:
        for name, documents_url in tenants:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            ctx_args = dict(ignore_https_errors=True)
            if record_video:
                ctx_args["record_video_dir"] = os.path.join(video_dir, name)
                ctx_args["record_video_size"] = {"width": 1280, "height": 720}
            context = browser.new_context(**ctx_args)
            page = context.new_page()
            try:
                download_tenant(page, context, name, documents_url, download_dir, state)
            finally:
                context.close()
                if record_video and page.video:
                    print(f"[{name}] Video saved: {page.video.path()}")
                browser.close()

    print("\nAll tenants done.")


if __name__ == "__main__":
    main()
