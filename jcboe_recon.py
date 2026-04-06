"""
GMS Recon Script — Jersey City Board of Education (BoardDocs)
=============================================================
Phase 0: Discover rate limits, enumerate meetings, catalog PDF links.

Endpoints (reverse-engineered from LlamaIndex BoardDocs reader):
  1. BD-GetMeetingsList  — returns JSON list of all meetings
  2. PRINT-AgendaDetailed — returns HTML of full agenda with PDF links

Target: https://go.boarddocs.com/nj/jcps/Board.nsf/Public
Committee: A9QM9A5A1F6C (Main Governing Board)
"""

import json
import time
import sys
from datetime import datetime
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

# ─── Configuration ───────────────────────────────────────────────
SITE = "nj/jcps/Board.nsf"
BASE_URL = f"https://go.boarddocs.com/{SITE}"
COMMITTEE_ID = "A9QM9A5A1F6C"

# Headers required by Lotus-Domino to serve XHR responses
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "sec-ch-ua": '"Google Chrome";v="124", "Chromium";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest",
    "referer": f"https://go.boarddocs.com/{SITE}/Public",
    "origin": "https://go.boarddocs.com",
}

# Rate limiting: start conservative
REQUEST_DELAY = 2.0  # seconds between requests


# ─── Helper ──────────────────────────────────────────────────────
def make_request(url, data=None, method="POST"):
    """Make a request with timing info for rate limit discovery."""
    start = time.time()
    try:
        if method == "POST":
            resp = requests.post(url, headers=HEADERS, data=data, timeout=30)
        else:
            resp = requests.get(url, headers=HEADERS, timeout=30)
        elapsed = time.time() - start
        return resp, elapsed
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start
        print(f"  [ERROR] {e} (after {elapsed:.2f}s)")
        return None, elapsed


# ─── Phase 0A: Get Meeting List ─────────────────────────────────
def get_meetings():
    """Fetch all meetings from the Main Governing Board committee."""
    print("=" * 70)
    print("PHASE 0A: Fetching meeting list")
    print("=" * 70)

    url = BASE_URL + "/BD-GetMeetingsList?open"
    data = f"current_committee_id={COMMITTEE_ID}"

    resp, elapsed = make_request(url, data)
    if not resp:
        print("FATAL: Could not reach BoardDocs server.")
        sys.exit(1)

    print(f"  Status: {resp.status_code}")
    print(f"  Response time: {elapsed:.2f}s")
    print(f"  Content-Type: {resp.headers.get('content-type', 'unknown')}")
    print(f"  Content-Length: {len(resp.content)} bytes")

    # Check for rate limiting headers
    rate_headers = {k: v for k, v in resp.headers.items()
                    if any(x in k.lower() for x in ['rate', 'limit', 'retry', 'throttle'])}
    if rate_headers:
        print(f"  Rate limit headers found: {rate_headers}")
    else:
        print("  No explicit rate limit headers detected.")

    if resp.status_code == 429:
        print("  WARNING: Rate limited on first request!")
        return []

    if resp.status_code != 200:
        print(f"  WARNING: Unexpected status code. Body preview: {resp.text[:500]}")
        return []

    try:
        meetings = json.loads(resp.text)
    except json.JSONDecodeError:
        print(f"  ERROR: Response is not JSON. Preview: {resp.text[:500]}")
        return []

    print(f"\n  Total meetings found: {len(meetings)}")

    if meetings:
        # Show sample meeting structure
        print(f"\n  Sample meeting keys: {list(meetings[0].keys())}")
        print(f"  Sample meeting: {json.dumps(meetings[0], indent=2)[:500]}")

    # Analyze meeting date range
    dates = []
    for m in meetings:
        nd = m.get("numberdate")
        if nd:
            try:
                dates.append(str(nd))
            except Exception:
                pass

    if dates:
        dates_sorted = sorted(dates)
        print(f"\n  Date range: {dates_sorted[0]} to {dates_sorted[-1]}")

    # Count meetings by year
    year_counts = defaultdict(int)
    for m in meetings:
        nd = str(m.get("numberdate", ""))
        if len(nd) >= 4:
            year_counts[nd[:4]] += 1

    if year_counts:
        print("\n  Meetings by year:")
        for year in sorted(year_counts.keys()):
            print(f"    {year}: {year_counts[year]} meetings")

    return meetings


# ─── Phase 0B: Rate Limit Test ──────────────────────────────────
def test_rate_limits(meetings):
    """Send a burst of requests to discover rate limiting behavior."""
    print("\n" + "=" * 70)
    print("PHASE 0B: Rate limit discovery")
    print("=" * 70)

    if len(meetings) < 5:
        print("  Not enough meetings to test rate limits.")
        return

    # Test with 5 rapid requests (no delay)
    print("\n  Test 1: 5 rapid requests (no delay)...")
    url = BASE_URL + "/PRINT-AgendaDetailed"
    results = []

    for i, meeting in enumerate(meetings[:5]):
        mid = meeting.get("unique", "")
        data = f"id={mid}&current_committee_id={COMMITTEE_ID}"
        resp, elapsed = make_request(url, data)
        status = resp.status_code if resp else "FAILED"
        size = len(resp.content) if resp else 0
        results.append({"index": i, "status": status, "time": elapsed, "size": size})
        print(f"    Request {i+1}: status={status}, time={elapsed:.2f}s, size={size} bytes")

    blocked = [r for r in results if r["status"] in [429, 403, "FAILED"]]
    if blocked:
        print(f"\n  WARNING: {len(blocked)}/5 requests were blocked/rate-limited!")
        print("  Recommendation: Use delays of 3-5 seconds between requests.")
    else:
        print(f"\n  All 5 rapid requests succeeded.")

    # Test with 5 polite requests (2s delay)
    print(f"\n  Test 2: 5 polite requests ({REQUEST_DELAY}s delay)...")
    results2 = []

    for i, meeting in enumerate(meetings[5:10]):
        mid = meeting.get("unique", "")
        data = f"id={mid}&current_committee_id={COMMITTEE_ID}"
        resp, elapsed = make_request(url, data)
        status = resp.status_code if resp else "FAILED"
        size = len(resp.content) if resp else 0
        results2.append({"index": i, "status": status, "time": elapsed, "size": size})
        print(f"    Request {i+1}: status={status}, time={elapsed:.2f}s, size={size} bytes")
        if i < 4:
            time.sleep(REQUEST_DELAY)

    blocked2 = [r for r in results2 if r["status"] in [429, 403, "FAILED"]]
    if blocked2:
        print(f"\n  WARNING: {len(blocked2)}/5 polite requests were blocked!")
    else:
        print(f"\n  All 5 polite requests succeeded.")

    avg_time = sum(r["time"] for r in results + results2) / len(results + results2)
    print(f"\n  Average response time: {avg_time:.2f}s")


# ─── Phase 0C: Catalog PDF Links from Sample Meetings ───────────
def catalog_pdfs(meetings, sample_size=3):
    """Pull detailed agendas and extract all PDF links."""
    print("\n" + "=" * 70)
    print(f"PHASE 0C: Cataloging PDF links from {sample_size} sample meetings")
    print("=" * 70)

    url = BASE_URL + "/PRINT-AgendaDetailed"
    all_pdf_info = []
    meetings_with_pdfs = 0
    meetings_without_pdfs = 0
    agenda_items_total = 0
    agenda_items_with_pdfs = 0

    for i, meeting in enumerate(meetings[:sample_size]):
        mid = meeting.get("unique", "")
        mdate = meeting.get("numberdate", "unknown")
        mname = meeting.get("name", meeting.get("title", "untitled"))
        print(f"\n  Meeting {i+1}: {mname} (date: {mdate})")

        data = f"id={mid}&current_committee_id={COMMITTEE_ID}"
        resp, elapsed = make_request(url, data)
        time.sleep(REQUEST_DELAY)

        if not resp or resp.status_code != 200:
            print(f"    SKIPPED (status: {resp.status_code if resp else 'FAILED'})")
            continue

        soup = BeautifulSoup(resp.content, "html.parser")

        # Extract meeting metadata
        date_div = soup.find("div", {"class": "print-meeting-date"})
        name_div = soup.find("div", {"class": "print-meeting-name"})
        if date_div:
            print(f"    Date: {date_div.get_text(strip=True)}")
        if name_div:
            print(f"    Title: {name_div.get_text(strip=True)}")

        # Find all agenda items (sections)
        agenda_sections = soup.find_all("div", {"class": "print-agenda-item"})
        if not agenda_sections:
            # Try alternative selectors
            agenda_sections = soup.find_all("div", {"class": "agenda-item"})
        if not agenda_sections:
            agenda_sections = soup.find_all("tr", {"class": "agenda-item"})

        print(f"    Agenda item divs found: {len(agenda_sections)}")

        # Find all PDF links anywhere in the document
        pdf_links = []

        # Method 1: div.public-file > a
        public_files = soup.find_all("div", {"class": "public-file"})
        for pf in public_files:
            link = pf.find("a")
            if link and link.get("href"):
                pdf_links.append({
                    "href": link["href"],
                    "text": link.get_text(strip=True),
                    "source": "public-file"
                })

        # Method 2: Any <a> tag with .pdf in href
        all_links = soup.find_all("a", href=True)
        for link in all_links:
            href = link["href"]
            if ".pdf" in href.lower() or "/files/" in href.lower():
                if href not in [p["href"] for p in pdf_links]:
                    pdf_links.append({
                        "href": href,
                        "text": link.get_text(strip=True),
                        "source": "general-link"
                    })

        # Method 3: Any <a> tag with "$file" in href (Lotus Domino attachment pattern)
        for link in all_links:
            href = link["href"]
            if "$file" in href.lower() or "/$file/" in href.lower():
                if href not in [p["href"] for p in pdf_links]:
                    pdf_links.append({
                        "href": href,
                        "text": link.get_text(strip=True),
                        "source": "domino-attachment"
                    })

        if pdf_links:
            meetings_with_pdfs += 1
            print(f"    PDF/document links found: {len(pdf_links)}")
            for j, pdf in enumerate(pdf_links[:10]):  # Show first 10
                print(f"      [{j+1}] {pdf['text'][:60]} ({pdf['source']})")
                print(f"          {pdf['href'][:100]}")
            if len(pdf_links) > 10:
                print(f"      ... and {len(pdf_links) - 10} more")
        else:
            meetings_without_pdfs += 1
            print(f"    NO PDF links found in this meeting.")

        all_pdf_info.extend(pdf_links)

        # Dump a snippet of raw HTML for structure analysis
        if i == 0:
            print(f"\n    [DEBUG] First 2000 chars of agenda HTML for structure analysis:")
            raw = resp.text[:2000]
            # Show class names used in the HTML
            classes_used = set()
            for tag in soup.find_all(True, {"class": True}):
                for c in tag.get("class", []):
                    classes_used.add(c)
            print(f"    CSS classes found: {sorted(classes_used)[:30]}")

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 0C SUMMARY")
    print("=" * 70)
    print(f"  Meetings sampled: {sample_size}")
    print(f"  Meetings with PDF links: {meetings_with_pdfs}")
    print(f"  Meetings without PDF links: {meetings_without_pdfs}")
    print(f"  Total PDF/doc links found: {len(all_pdf_info)}")

    # Categorize links by source
    source_counts = defaultdict(int)
    for p in all_pdf_info:
        source_counts[p["source"]] += 1
    print(f"  Link sources: {dict(source_counts)}")

    # Categorize by URL pattern
    domain_counts = defaultdict(int)
    for p in all_pdf_info:
        href = p["href"]
        if href.startswith("http"):
            domain = href.split("/")[2]
        elif href.startswith("/"):
            domain = "go.boarddocs.com (relative)"
        else:
            domain = "other"
        domain_counts[domain] += 1
    print(f"  Link domains: {dict(domain_counts)}")

    return all_pdf_info


# ─── Main ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"GMS Recon — Jersey City Board of Education")
    print(f"Target: {BASE_URL}/Public")
    print(f"Committee: {COMMITTEE_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Phase 0A: Get all meetings
    meetings = get_meetings()
    if not meetings:
        print("No meetings found. Exiting.")
        sys.exit(1)

    # Phase 0B: Rate limit testing
    if len(meetings) >= 10:
        test_rate_limits(meetings)
    else:
        print("Not enough meetings for rate limit testing.")

    # Phase 0C: PDF catalog from 3 most recent meetings
    # Sort by date descending (most recent first)
    meetings_sorted = sorted(meetings, key=lambda m: m.get("numberdate") or "0", reverse=True)
    catalog_pdfs(meetings_sorted, sample_size=3)

    print("\n" + "=" * 70)
    print("RECON COMPLETE")
    print("=" * 70)
    print(f"Total meetings available: {len(meetings)}")
    print(f"Next step: Run full PDF catalog across all meetings")
    print(f"Then: Build GMS PLM ingestion pipeline")
