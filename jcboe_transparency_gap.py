"""
GMS Transparency Gap Analyzer — Jersey City Board of Education
===============================================================
Targeted scraper: Jan 2024 to present (current governance cycle).

Detects the pattern described by former board member:
"Contracts worth hundreds of thousands of dollars if not millions
are listed as an agenda item without the actual contract document attached."

This script:
1. Pulls all meetings from Jan 2024 onward
2. Parses every agenda item from the detailed HTML
3. Identifies items that mention dollar amounts or contract language
4. Flags which have PDFs attached and which don't
5. Produces a "transparency gap" report

Endpoints:
  BD-GetMeetingsList  -> JSON list of meetings
  PRINT-AgendaDetailed -> Full HTML agenda with items + PDF links
"""

import json
import re
import csv
import time
import sys
from datetime import datetime
from collections import defaultdict
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

# ─── Configuration ───────────────────────────────────────────────
SITE = "nj/jcps/Board.nsf"
BASE_URL = f"https://go.boarddocs.com/{SITE}"
COMMITTEE_ID = "A9QM9A5A1F6C"
CUTOFF_DATE = "20240101"  # Jan 1, 2024

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    "referer": f"https://go.boarddocs.com/{SITE}/Public",
}

REQUEST_DELAY = 1.5  # seconds between requests (server has no rate limit, but be polite)

# ─── Patterns that indicate financial/contract items ─────────────
DOLLAR_PATTERN = re.compile(r'\$[\d,]+(?:\.\d{2})?')
CONTRACT_KEYWORDS = [
    'contract', 'agreement', 'vendor', 'bid', 'rfp', 'rfi', 'rfq',
    'purchase order', 'procurement', 'consultant', 'professional service',
    'award', 'expenditure', 'appropriation', 'allocation',
    'not to exceed', 'nte', 'change order',
    'memorandum of understanding', 'mou', 'lease', 'rental',
    'insurance', 'legal services', 'architect', 'construction',
    'renovation', 'repair', 'maintenance agreement',
    'transportation', 'food service', 'technology',
    'tuition', 'stipend', 'compensation',
]

FINANCIAL_SECTIONS = [
    'finance', 'fiscal', 'budget', 'business', 'facilities',
    'personnel', 'human resources',
]


def make_request(url, data=None):
    """POST with retry logic."""
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=HEADERS, data=data, timeout=45)
            return resp
        except requests.exceptions.RequestException as e:
            print(f"    [RETRY {attempt+1}] {e}")
            time.sleep(3)
    return None


def get_meetings_since(cutoff):
    """Get all meetings on or after cutoff date string (YYYYMMDD)."""
    url = BASE_URL + "/BD-GetMeetingsList?open"
    resp = make_request(url, f"current_committee_id={COMMITTEE_ID}")
    if not resp or resp.status_code != 200:
        print("FATAL: Could not fetch meeting list.")
        sys.exit(1)

    all_meetings = json.loads(resp.text)
    filtered = [
        m for m in all_meetings
        if m.get("numberdate") and str(m["numberdate"]) >= cutoff
    ]
    filtered.sort(key=lambda m: str(m["numberdate"]))
    return filtered


def extract_dollar_amounts(text):
    """Extract all dollar amounts from text."""
    amounts = DOLLAR_PATTERN.findall(text)
    parsed = []
    for a in amounts:
        try:
            val = float(a.replace('$', '').replace(',', ''))
            parsed.append(val)
        except ValueError:
            pass
    return parsed


def has_contract_language(text):
    """Check if text contains contract/financial keywords."""
    text_lower = text.lower()
    found = [kw for kw in CONTRACT_KEYWORDS if kw in text_lower]
    return found


def parse_agenda_items(soup):
    """
    Parse individual agenda items from the detailed agenda HTML.
    BoardDocs uses a specific structure with .agendaorder containers.
    Each item has .leftcol (item number) and .rightcol (content + files).
    """
    items = []

    # Each agenda item is in a div.item inside div.agendaorder
    item_divs = soup.find_all("div", class_="item")

    for item_div in item_divs:
        item_data = {}

        # Get item number/identifier from leftcol
        leftcol = item_div.find("div", class_="leftcol")
        item_data["item_number"] = leftcol.get_text(strip=True) if leftcol else ""

        # Get content from rightcol
        rightcol = item_div.find("div", class_="rightcol")
        if not rightcol:
            rightcol = item_div

        # Get the item title/body text
        itembody = rightcol.find("div", class_="itembody")
        if itembody:
            item_data["text"] = itembody.get_text(separator=" ", strip=True)
            item_data["html"] = str(itembody)
        else:
            item_data["text"] = rightcol.get_text(separator=" ", strip=True)
            item_data["html"] = str(rightcol)

        # Find attached files specifically for this item
        files = []
        file_divs = rightcol.find_all("div", class_="public-file") if rightcol else []
        for fd in file_divs:
            link = fd.find("a")
            if link and link.get("href"):
                filename = unquote(link["href"].split("/")[-1]) if "/" in link["href"] else link.get_text(strip=True)
                files.append({
                    "href": link["href"],
                    "text": link.get_text(strip=True),
                    "filename": filename,
                })
        item_data["files"] = files
        item_data["file_count"] = len(files)

        items.append(item_data)

    return items


def analyze_meeting(meeting):
    """Fetch and analyze a single meeting's agenda."""
    mid = meeting["unique"]
    mdate = str(meeting["numberdate"])
    mname = meeting.get("name", "untitled")

    url = BASE_URL + "/PRINT-AgendaDetailed"
    data = f"id={mid}&current_committee_id={COMMITTEE_ID}"
    resp = make_request(url, data)

    if not resp or resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.content, "html.parser")
    items = parse_agenda_items(soup)

    # Also get total file count from the whole document
    all_public_files = soup.find_all("div", class_="public-file")
    total_pdfs = len(all_public_files)

    results = {
        "meeting_id": mid,
        "date": mdate,
        "name": mname,
        "total_agenda_items": len(items),
        "total_pdfs": total_pdfs,
        "flagged_items": [],
        "all_items": items,
    }

    for item in items:
        text = item["text"]
        dollar_amounts = extract_dollar_amounts(text)
        contract_keywords = has_contract_language(text)

        if dollar_amounts or contract_keywords:
            max_amount = max(dollar_amounts) if dollar_amounts else 0
            item["dollar_amounts"] = dollar_amounts
            item["max_amount"] = max_amount
            item["contract_keywords"] = contract_keywords
            item["has_attachment"] = item["file_count"] > 0
            item["transparency_gap"] = not item["has_attachment"]
            results["flagged_items"].append(item)

    return results


def main():
    print("=" * 80)
    print("GMS TRANSPARENCY GAP ANALYZER")
    print("Jersey City Board of Education — Jan 2024 to Present")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: {BASE_URL}/Public")
    print()

    # Step 1: Get meetings
    print("Fetching meetings since Jan 2024...")
    meetings = get_meetings_since(CUTOFF_DATE)
    print(f"Found {len(meetings)} meetings in scope.\n")

    # Step 2: Analyze each meeting
    all_results = []
    all_flagged = []
    all_gaps = []

    for i, meeting in enumerate(meetings):
        mdate = str(meeting["numberdate"])
        mname = meeting.get("name", "")
        print(f"[{i+1}/{len(meetings)}] {mdate} - {mname[:50]}...", end="", flush=True)

        result = analyze_meeting(meeting)
        time.sleep(REQUEST_DELAY)

        if not result:
            print(" FAILED")
            continue

        flagged_count = len(result["flagged_items"])
        gap_items = [f for f in result["flagged_items"] if f["transparency_gap"]]
        gap_count = len(gap_items)

        all_results.append(result)
        all_flagged.extend(result["flagged_items"])
        all_gaps.extend(gap_items)

        status = f" {result['total_agenda_items']} items, {result['total_pdfs']} PDFs, "
        status += f"{flagged_count} financial items, {gap_count} GAPS"
        if gap_count > 0:
            status += " ⚠️"
        print(status)

    # Step 3: Generate report
    print("\n" + "=" * 80)
    print("TRANSPARENCY GAP REPORT")
    print("=" * 80)

    total_items = sum(r["total_agenda_items"] for r in all_results)
    total_pdfs = sum(r["total_pdfs"] for r in all_results)

    print(f"\nMeetings analyzed: {len(all_results)}")
    print(f"Total agenda items: {total_items}")
    print(f"Total PDF attachments: {total_pdfs}")
    print(f"Financial/contract items identified: {len(all_flagged)}")
    print(f"Financial items WITH attachments: {len(all_flagged) - len(all_gaps)}")
    print(f"Financial items WITHOUT attachments: {len(all_gaps)} ← TRANSPARENCY GAPS")

    if all_flagged:
        transparency_rate = ((len(all_flagged) - len(all_gaps)) / len(all_flagged)) * 100
        print(f"Attachment rate for financial items: {transparency_rate:.1f}%")

    # Dollar amounts at risk
    total_dollars_flagged = sum(
        item.get("max_amount", 0) for item in all_flagged
    )
    total_dollars_gap = sum(
        item.get("max_amount", 0) for item in all_gaps
    )
    print(f"\nTotal dollar amounts in financial items: ${total_dollars_flagged:,.2f}")
    print(f"Dollar amounts in items WITHOUT docs: ${total_dollars_gap:,.2f}")

    # Top gaps by dollar amount
    if all_gaps:
        print(f"\n{'─' * 80}")
        print("TOP TRANSPARENCY GAPS (by dollar amount, no document attached)")
        print(f"{'─' * 80}")

        gaps_sorted = sorted(all_gaps, key=lambda x: x.get("max_amount", 0), reverse=True)
        for i, gap in enumerate(gaps_sorted[:25]):
            amounts_str = ", ".join(f"${a:,.2f}" for a in gap.get("dollar_amounts", []))
            keywords_str = ", ".join(gap.get("contract_keywords", [])[:3])
            date_str = ""
            # Find the meeting date for this item
            for r in all_results:
                if gap in r["flagged_items"]:
                    date_str = r["date"]
                    break

            print(f"\n  [{i+1}] {date_str} | Item {gap['item_number']}")
            print(f"      Amounts: {amounts_str}")
            print(f"      Keywords: {keywords_str}")
            # Truncate text for display
            preview = gap["text"][:200].replace("\n", " ")
            print(f"      Preview: {preview}...")

    # Meetings with worst transparency gaps
    if all_results:
        print(f"\n{'─' * 80}")
        print("MEETINGS RANKED BY TRANSPARENCY GAPS")
        print(f"{'─' * 80}")

        meetings_by_gaps = sorted(
            all_results,
            key=lambda r: len([f for f in r["flagged_items"] if f["transparency_gap"]]),
            reverse=True
        )
        for r in meetings_by_gaps[:10]:
            gaps_in_meeting = [f for f in r["flagged_items"] if f["transparency_gap"]]
            if gaps_in_meeting:
                gap_dollars = sum(g.get("max_amount", 0) for g in gaps_in_meeting)
                print(f"  {r['date']} | {r['name'][:40]} | "
                      f"{len(gaps_in_meeting)} gaps | ${gap_dollars:,.2f} undocumented")

    # Export to CSV
    csv_file = "jcboe_transparency_gaps.csv"
    print(f"\nExporting all flagged items to {csv_file}...")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "meeting_date", "meeting_name", "item_number",
            "dollar_amounts", "max_amount", "contract_keywords",
            "has_attachment", "transparency_gap", "file_count",
            "attached_files", "item_text_preview"
        ])
        for result in all_results:
            for item in result["flagged_items"]:
                writer.writerow([
                    result["date"],
                    result["name"],
                    item["item_number"],
                    "; ".join(f"${a:,.2f}" for a in item.get("dollar_amounts", [])),
                    item.get("max_amount", 0),
                    "; ".join(item.get("contract_keywords", [])),
                    item.get("has_attachment", False),
                    item.get("transparency_gap", False),
                    item.get("file_count", 0),
                    "; ".join(f["text"][:60] for f in item.get("files", [])),
                    item["text"][:300].replace("\n", " "),
                ])

    print(f"Done. CSV saved to: {csv_file}")

    print(f"\n{'=' * 80}")
    print("NEXT STEPS FOR GMS")
    print(f"{'=' * 80}")
    print("1. Review the CSV for the highest-dollar transparency gaps")
    print("2. Cross-reference gap items with vendor names and board vote records")
    print("3. Build the IPM (Influence & Power Map) layer to track who moves/seconds these items")
    print("4. Download and analyze the PDFs that DO exist for contract terms and vendor patterns")
    print("5. Feed findings into the GHI (Governance Health Index) for a scorecard")


if __name__ == "__main__":
    main()
