"""
GMS OPRAMachine Scraper — JCBOE OPRA Request History
=====================================================
Scrapes all OPRA requests filed against the Jersey City Board of Education
from opramachine.com using Playwright to bypass Cloudflare.

Outputs:
- jcboe_opra_requests.csv — all requests with status, dates, subjects
- Cross-reference summary against contract gaps (printed to stdout)
"""

import csv
import re
import time
import json
from datetime import datetime

from playwright.sync_api import sync_playwright


JCBOE_URL = "https://opramachine.com/body/jersey_city_board_of_education"
OUTPUT_CSV = "jcboe_opra_requests.csv"


def scrape_opra_requests():
    print("=" * 90)
    print("GMS OPRAMachine SCRAPER — Jersey City Board of Education")
    print("=" * 90)
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    all_requests = []

    with sync_playwright() as p:
        # Use headed browser — Cloudflare blocks headless
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        # Remove webdriver flag that Cloudflare detects
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        page = context.new_page()

        print(f"Loading {JCBOE_URL} ...")
        page.goto(JCBOE_URL, wait_until="domcontentloaded", timeout=60000)

        # Wait for Cloudflare challenge to auto-resolve
        print("Waiting for Cloudflare challenge to resolve...")
        print("(If a CAPTCHA appears, please solve it in the browser window)")
        for attempt in range(24):  # Up to ~2 minutes
            time.sleep(5)
            title = page.title()
            if "just a moment" not in title.lower() and "attention" not in title.lower():
                break
            print(f"  [{attempt+1}] Still on challenge page: {title}")

        title = page.title()
        print(f"Page title: {title}")

        # Get page content for debugging
        content = page.content()
        print(f"Page content length: {len(content)} chars")

        # Try to find the requests listing
        # OPRAMachine typically lists requests in a table or list format
        page_num = 1
        while True:
            print(f"\n--- Page {page_num} ---")

            # Extract requests from current page
            requests_on_page = extract_requests_from_page(page)
            if not requests_on_page:
                # Try scrolling to load more
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                requests_on_page = extract_requests_from_page(page)

            if not requests_on_page:
                print("  No requests found on this page")
                # Save page HTML for debugging
                with open("opramachine_debug.html", "w") as f:
                    f.write(page.content())
                print("  Debug HTML saved to opramachine_debug.html")
                break

            print(f"  Found {len(requests_on_page)} requests")
            all_requests.extend(requests_on_page)

            # Look for "next page" link
            next_link = page.query_selector('a[rel="next"], .next a, a:has-text("Next"), .pagination a:has-text("›"), .pagination a:has-text("next")')
            if next_link:
                print("  Navigating to next page...")
                next_link.click()
                page.wait_for_load_state("domcontentloaded")
                time.sleep(3)
                page_num += 1
            else:
                print("  No more pages")
                break

        # Also try to get individual request details for recent ones
        print(f"\nTotal requests collected: {len(all_requests)}")

        # Try fetching details for each request
        detailed_requests = []
        for i, req in enumerate(all_requests):
            if req.get("url"):
                print(f"  [{i+1}/{len(all_requests)}] Fetching details: {req['title'][:60]}...")
                try:
                    page.goto(req["url"], wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)
                    details = extract_request_details(page)
                    req.update(details)
                except Exception as e:
                    print(f"    Error: {e}")
            detailed_requests.append(req)

        browser.close()

    all_requests = detailed_requests if detailed_requests else all_requests

    # Export CSV
    if all_requests:
        fieldnames = sorted(set().union(*[r.keys() for r in all_requests]))
        # Reorder for readability
        priority_fields = ["title", "status", "date_submitted", "date_updated", "url", "body_text"]
        ordered = [f for f in priority_fields if f in fieldnames]
        ordered += [f for f in fieldnames if f not in ordered]

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ordered)
            writer.writeheader()
            writer.writerows(all_requests)
        print(f"\nCSV exported: {OUTPUT_CSV}")
    else:
        print("\nNo requests to export")

    # Print summary
    print(f"\n{'=' * 90}")
    print("OPRA REQUEST SUMMARY")
    print(f"{'=' * 90}")
    print(f"Total requests found: {len(all_requests)}")

    if all_requests:
        # Status breakdown
        statuses = {}
        for r in all_requests:
            s = r.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        print(f"\nBy status:")
        for s, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
            print(f"  {s}: {count}")

        # Contract-related requests
        contract_keywords = ["contract", "agreement", "vendor", "purchase order",
                             "bid", "rfp", "procurement", "gl group", "edmentum",
                             "white rock", "spending", "expenditure"]
        contract_requests = [
            r for r in all_requests
            if any(kw in (r.get("title", "") + " " + r.get("body_text", "")).lower() for kw in contract_keywords)
        ]
        print(f"\nContract-related OPRA requests: {len(contract_requests)}")
        for r in contract_requests:
            print(f"  [{r.get('status', '?')}] {r.get('date_submitted', '?')} — {r.get('title', '?')[:80]}")

    return all_requests


def extract_requests_from_page(page):
    """Extract OPRA request listings from the current page."""
    requests = []

    # Strategy 1: Look for request links in a list/table
    # OPRAMachine uses <div class="request_listing"> or similar
    request_elements = page.query_selector_all(
        '.request_listing a, '
        'table.body_listing a, '
        '#authority_requests a, '
        '.request_short_listing a, '
        'a[href*="/request/"]'
    )

    seen_urls = set()
    for el in request_elements:
        href = el.get_attribute("href") or ""
        text = el.inner_text().strip()

        # Only interested in actual request links
        if "/request/" not in href:
            continue
        if not text or len(text) < 5:
            continue

        # Build full URL
        if href.startswith("/"):
            href = f"https://opramachine.com{href}"

        if href in seen_urls:
            continue
        seen_urls.add(href)

        # Try to get surrounding context (status, date)
        parent = el.evaluate_handle("el => el.closest('tr, li, div.request_short_listing, div.request_listing, .list-item')")
        parent_text = ""
        try:
            parent_text = parent.inner_text()
        except Exception:
            pass

        # Extract status from parent text
        status = "unknown"
        status_patterns = [
            (r'successful', 'successful'),
            (r'partially successful', 'partially_successful'),
            (r'awaiting', 'awaiting_response'),
            (r'overdue', 'overdue'),
            (r'refused', 'refused'),
            (r'not held', 'not_held'),
            (r'withdrawn', 'withdrawn'),
            (r'gone postal', 'gone_postal'),
            (r'long overdue', 'long_overdue'),
        ]
        for pattern, label in status_patterns:
            if re.search(pattern, parent_text, re.IGNORECASE):
                status = label
                break

        # Extract date
        date_match = re.search(r'(\w+ \d{1,2},?\s*\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})', parent_text)
        date_str = date_match.group(1) if date_match else ""

        requests.append({
            "title": text,
            "url": href,
            "status": status,
            "date_submitted": date_str,
            "date_updated": "",
            "body_text": "",
        })

    # Strategy 2: If no request links found, try parsing the full page text
    if not requests:
        # Look for any links at all
        all_links = page.query_selector_all("a")
        for el in all_links:
            href = el.get_attribute("href") or ""
            text = el.inner_text().strip()
            if "/request/" in href and text and len(text) > 10:
                if href.startswith("/"):
                    href = f"https://opramachine.com{href}"
                if href not in seen_urls:
                    seen_urls.add(href)
                    requests.append({
                        "title": text,
                        "url": href,
                        "status": "unknown",
                        "date_submitted": "",
                        "date_updated": "",
                        "body_text": "",
                    })

    return requests


def extract_request_details(page):
    """Extract details from an individual OPRA request page."""
    details = {}

    # Get the main request body text
    body_el = page.query_selector(".request_body, .correspondence, #request_details, .describe_state_form, main")
    if body_el:
        details["body_text"] = body_el.inner_text()[:2000]

    # Get status
    status_el = page.query_selector(".request_status, .state, .status, h1 .status")
    if status_el:
        details["status"] = status_el.inner_text().strip().lower()

    # Get dates
    date_els = page.query_selector_all("time, .date, .created_at")
    dates = []
    for el in date_els:
        dt = el.get_attribute("datetime") or el.inner_text().strip()
        if dt:
            dates.append(dt)
    if dates:
        details["date_submitted"] = dates[0]
        if len(dates) > 1:
            details["date_updated"] = dates[-1]

    # Get any response/attachment info
    attachments = page.query_selector_all(".attachment a, a[href*='attach'], a[href*='.pdf']")
    att_texts = []
    for a in attachments:
        att_texts.append(a.inner_text().strip())
    if att_texts:
        details["attachments"] = "; ".join(att_texts[:10])

    return details


if __name__ == "__main__":
    scrape_opra_requests()
