"""
GMS Deep Dive v3 — Budget Docs + Contract Source Documents
Jersey City Board of Education
==============================================================
Two investigations based on former board member's guidance:

1. BUDGET CHECK: Are budget documents attached in March-June meetings?
   (Legally required to be publicly available before the vote)

2. CONTRACT SOURCE CHECK: When a contract is approved, is the actual
   signed agreement attached — or just the resolution paragraph?
   (The agenda item says "approve contract with X, NTE $1M" but
   the underlying contract with terms/conditions/signatures is missing)
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

SITE = "nj/jcps/Board.nsf"
BASE_URL = f"https://go.boarddocs.com/{SITE}"
COMMITTEE_ID = "A9QM9A5A1F6C"
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    "referer": f"https://go.boarddocs.com/{SITE}/Public",
}
REQUEST_DELAY = 1.5


def make_request(url, data=None):
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=HEADERS, data=data, timeout=45)
            return resp
        except Exception as e:
            print(f"    [RETRY {attempt+1}] {e}")
            time.sleep(3)
    return None


def get_all_meetings():
    resp = make_request(BASE_URL + "/BD-GetMeetingsList?open",
                        f"current_committee_id={COMMITTEE_ID}")
    return json.loads(resp.text)


def fetch_meeting_html(meeting):
    mid = meeting["unique"]
    data = f"id={mid}&current_committee_id={COMMITTEE_ID}"
    return make_request(BASE_URL + "/PRINT-AgendaDetailed", data)


def parse_items_with_files(soup):
    """Parse agenda items and their attached files."""
    items = []
    for item_div in soup.find_all("div", class_="item"):
        leftcol = item_div.find("div", class_="leftcol")
        item_num = leftcol.get_text(strip=True) if leftcol else ""

        rightcol = item_div.find("div", class_="rightcol") or item_div
        itembody = rightcol.find("div", class_="itembody")
        text = itembody.get_text(separator=" ", strip=True) if itembody else rightcol.get_text(separator=" ", strip=True)

        files = []
        for fd in rightcol.find_all("div", class_="public-file"):
            link = fd.find("a")
            if link and link.get("href"):
                files.append({
                    "href": link["href"],
                    "text": link.get_text(strip=True),
                    "filename": unquote(link["href"].split("/")[-1]) if "/" in link["href"] else ""
                })

        items.append({
            "item_number": item_num,
            "text": text,
            "files": files,
            "file_count": len(files),
        })
    return items


# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 1: BUDGET DOCUMENTS
# ═══════════════════════════════════════════════════════════════════
def check_budget_docs():
    print("=" * 90)
    print("INVESTIGATION 1: BUDGET DOCUMENT AVAILABILITY")
    print("Are budget documents attached during March-June (legally required)? [2024-2026]")
    print("=" * 90)

    all_meetings = get_all_meetings()

    # Budget season: March-June, 2021-2026
    budget_meetings = []
    for m in all_meetings:
        nd = str(m.get("numberdate", ""))
        if len(nd) >= 6:
            year = nd[:4]
            month = int(nd[4:6])
            if year in ["2024", "2025", "2026"] and month in [3, 4, 5, 6]:
                budget_meetings.append(m)

    budget_meetings.sort(key=lambda m: str(m["numberdate"]))
    print(f"\nBudget-season meetings (Mar-Jun, 2024-2026): {len(budget_meetings)}\n")

    results = []

    for m in budget_meetings:
        mdate = str(m["numberdate"])
        mname = m.get("name", "")
        print(f"  Checking {mdate} | {mname[:55]}...", end="", flush=True)

        resp = fetch_meeting_html(m)
        time.sleep(REQUEST_DELAY)

        if not resp or resp.status_code != 200:
            print(" FAILED")
            continue

        soup = BeautifulSoup(resp.content, "html.parser")
        items = parse_items_with_files(soup)
        all_files = soup.find_all("div", class_="public-file")

        # Look for budget-specific items
        budget_items = []
        for item in items:
            t = item["text"].lower()
            if any(kw in t for kw in [
                "preliminary budget", "final budget", "adopt the",
                "budget hearing", "public hearing",
                "school year budget", "tax levy",
                "user friendly budget", "budget summary",
            ]):
                budget_items.append(item)

        # Look for budget-related PDFs anywhere in meeting
        budget_pdfs = []
        for fd in all_files:
            link = fd.find("a")
            if link:
                link_text = (link.get_text() + " " + link.get("href", "")).lower()
                if any(kw in link_text for kw in [
                    "budget", "tax levy", "revenue", "appropriation",
                    "user friendly", "summary", "expenditure",
                    "tentative", "preliminary", "final"
                ]):
                    budget_pdfs.append(link.get_text(strip=True))

        # Categorize this meeting
        has_budget_item = len(budget_items) > 0
        has_budget_pdf = len(budget_pdfs) > 0

        # Check if budget items specifically have files attached
        budget_items_with_files = [bi for bi in budget_items if bi["file_count"] > 0]

        result = {
            "date": mdate,
            "name": mname,
            "budget_items": len(budget_items),
            "budget_items_with_files": len(budget_items_with_files),
            "budget_pdfs_in_meeting": len(budget_pdfs),
            "total_pdfs": len(all_files),
        }
        results.append(result)

        if has_budget_pdf:
            print(f" ✅ {len(budget_pdfs)} budget PDF(s)")
            for bp in budget_pdfs[:3]:
                print(f"       📎 {bp[:75]}")
        elif has_budget_item:
            print(f" ⚠️  Budget item found, NO budget PDF attached")
            for bi in budget_items[:2]:
                print(f"       Item: {bi['text'][:100]}...")
        else:
            print(f" — No budget content (likely not a budget meeting)")

    # Summary
    print(f"\n{'─' * 90}")
    print("BUDGET DOCUMENT SUMMARY BY YEAR")
    print(f"{'─' * 90}")

    for year in ["2024", "2025", "2026"]:
        year_results = [r for r in results if r["date"].startswith(year)]
        if not year_results:
            continue
        meetings_with_budget = [r for r in year_results if r["budget_items"] > 0]
        meetings_with_pdf = [r for r in year_results if r["budget_pdfs_in_meeting"] > 0]
        print(f"\n  {year}:")
        print(f"    Mar-Jun meetings: {len(year_results)}")
        print(f"    Meetings with budget items: {len(meetings_with_budget)}")
        print(f"    Meetings with budget PDFs: {len(meetings_with_pdf)}")
        if meetings_with_budget and not meetings_with_pdf:
            print(f"    ⚠️  BUDGET DISCUSSED BUT NO DOCUMENTS PROVIDED TO PUBLIC")

    return results


# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 2: CONTRACT SOURCE DOCUMENTS
# ═══════════════════════════════════════════════════════════════════
def check_contract_docs():
    print(f"\n\n{'=' * 90}")
    print("INVESTIGATION 2: CONTRACT SOURCE DOCUMENTS")
    print("When board approves a contract, is the actual agreement attached?")
    print("(Not just the resolution paragraph, but the signed contract itself)")
    print("=" * 90)

    all_meetings = get_all_meetings()

    # All meetings from 2024 onward (regular, special, and other — contracts can be approved in any)
    target_meetings = [
        m for m in all_meetings
        if m.get("numberdate") and str(m["numberdate"]) >= "20240101"
    ]
    target_meetings.sort(key=lambda m: str(m["numberdate"]))
    print(f"\nAll meetings since Jan 2024: {len(target_meetings)}\n")

    # Contract detection
    contract_pattern = re.compile(
        r'(approve|authorize|award|ratif).{0,30}(contract|agreement|purchase order|professional .* service)',
        re.IGNORECASE
    )
    dollar_pattern = re.compile(r'\$[\d,]+(?:\.\d{2})?')

    # Exclude personnel/HR items
    personnel_patterns = [
        re.compile(r'(transfer|promotion|appointment|separation|leave|resignation|retirement|degree status|salary adjust)', re.IGNORECASE),
        re.compile(r'(instructional|non-instructional)\.\s*NAME\s+POSITION', re.IGNORECASE),
    ]

    all_contract_items = []
    csv_rows = []

    for m in target_meetings:
        mdate = str(m["numberdate"])
        mname = m.get("name", "")
        print(f"  Scanning {mdate} | {mname[:50]}...", end="", flush=True)

        resp = fetch_meeting_html(m)
        time.sleep(REQUEST_DELAY)

        if not resp or resp.status_code != 200:
            print(" FAILED")
            continue

        soup = BeautifulSoup(resp.content, "html.parser")
        items = parse_items_with_files(soup)

        meeting_contracts = 0
        meeting_with_source_doc = 0
        meeting_resolution_only = 0

        for item in items:
            text = item["text"]

            # Skip personnel items
            is_personnel = any(p.search(text) for p in personnel_patterns)
            if is_personnel:
                continue

            # Check if this is a contract approval
            if not contract_pattern.search(text):
                continue

            # Extract dollar amounts
            amounts = dollar_pattern.findall(text)
            max_amount = 0
            for a in amounts:
                try:
                    val = float(a.replace('$', '').replace(',', ''))
                    max_amount = max(max_amount, val)
                except:
                    pass

            # Skip tiny items
            if max_amount < 10000:
                continue

            meeting_contracts += 1

            # Analyze what's attached
            has_files = item["file_count"] > 0
            has_source_doc = False
            file_types = []

            for f in item["files"]:
                fname = f["filename"].lower()
                ftext = f["text"].lower()
                # Categorize what kind of document is attached
                if any(kw in fname + ftext for kw in ["contract", "agreement", "terms", "scope"]):
                    has_source_doc = True
                    file_types.append("CONTRACT")
                elif any(kw in fname + ftext for kw in ["af1", "af0", "po", "purchase"]):
                    file_types.append("PO_FORM")
                elif any(kw in fname + ftext for kw in ["bid", "proposal", "rfp", "quote"]):
                    has_source_doc = True
                    file_types.append("BID/PROPOSAL")
                elif any(kw in fname + ftext for kw in ["resolution", "attc", "attachment"]):
                    file_types.append("ATTACHMENT")
                else:
                    file_types.append("OTHER")

            if has_files:
                meeting_with_source_doc += 1
            else:
                meeting_resolution_only += 1

            # Extract vendor name — multiple patterns since resolutions vary
            vendor = ""
            vendor_patterns = [
                # "WHEREAS, [Vendor] was awarded..."
                r'WHEREAS\s*,\s*([A-Z][A-Za-z0-9\s&,.\'\-/]+?)\s+was\s+awarded',
                # "WHEREAS, [Vendor] has offered to renew..."
                r'WHEREAS\s*,\s*([A-Z][A-Za-z0-9\s&,.\'\-/]+?)\s+has\s+offered',
                # "WHEREAS, [Vendor] provides..."
                r'WHEREAS\s*,\s*([A-Z][A-Za-z0-9\s&,.\'\-/]+?)\s+provides',
                # "WHEREAS, [Vendor] is awarded..."
                r'WHEREAS\s*,\s*([A-Z][A-Za-z0-9\s&,.\'\-/]+?)\s+is\s+awarded',
                # "WHEREAS, [Vendor] located at..."
                r'WHEREAS\s*,\s*([A-Z][A-Za-z0-9\s&,.\'\-/]+?)\s+[Ll]ocated\s+at',
                # "contract/agreement with [Vendor]" (original pattern, broadened)
                r'(?:contract|agreement|order|services)\s+(?:with|to|from|awarded to)\s+([A-Z][A-Za-z0-9\s&,.\'\-/]+?)(?:\s*,\s*(?:LLC|Inc|Corp|Ltd|LP|LLP)\.?)?(?:\s*[,.]|\s+for\s+|\s+in\s+)',
                # "awarded a contract to [Vendor]"
                r'awarded\s+(?:a\s+)?(?:contract|the\s+contract)\s+to\s+([A-Z][A-Za-z0-9\s&,.\'\-/]+?)(?:\s*,|\s+for\s+|\s+in\s+|\s+thru\s+)',
                # "[Vendor], [address]" pattern (Vendor followed by street number)
                r'WHEREAS\s*,\s*([A-Z][A-Za-z0-9\s&,.\'\-/]+?),\s+\d+\s+[A-Z]',
            ]
            skip_prefixes = [
                'the jersey city', 'the district', 'the board', 'the special',
                'njac', 'n.j.s.a', 'pursuant', 'section', 'in accordance',
                'the 2', 'a notice', 'the notice', 'p arents', 'parents',
            ]
            for vp in vendor_patterns:
                vm = re.search(vp, text)
                if vm:
                    candidate = vm.group(1).strip().rstrip(',. ')
                    # Skip generic/institutional phrases
                    if not any(candidate.lower().startswith(s) for s in skip_prefixes) and len(candidate) > 2:
                        vendor = candidate
                        # Clean up trailing suffixes that got included
                        vendor = re.sub(r'\s*,?\s*(LLC|Inc|Corp|Ltd|LP|LLP)\.?\s*$', '', vendor).strip()
                        break

            item_info = {
                "date": mdate,
                "meeting": mname,
                "vendor": vendor,
                "max_amount": max_amount,
                "has_any_file": has_files,
                "file_count": item["file_count"],
                "file_types": file_types,
                "text_preview": text[:300],
                "files": [f["text"][:60] for f in item["files"]],
            }
            all_contract_items.append(item_info)

            csv_rows.append({
                "date": mdate,
                "meeting": mname,
                "vendor": vendor,
                "max_amount": max_amount,
                "has_file": has_files,
                "file_count": item["file_count"],
                "file_types": "; ".join(file_types),
                "attached_files": "; ".join(f["text"][:60] for f in item["files"]),
                "resolution_text": text[:500].replace("\n", " "),
            })

        total = meeting_contracts
        if total > 0:
            pct = meeting_resolution_only / total * 100
            print(f" {total} contracts, {meeting_with_source_doc} with docs, {meeting_resolution_only} resolution-only ({pct:.0f}% gap)")
        else:
            print(f" no contract items")

    # ─── Report ──────────────────────────────────────────────────
    with_docs = [c for c in all_contract_items if c["has_any_file"]]
    without_docs = [c for c in all_contract_items if not c["has_any_file"]]

    print(f"\n{'=' * 90}")
    print("CONTRACT SOURCE DOCUMENT REPORT")
    print(f"{'=' * 90}")
    print(f"\nTotal contract approvals (>$10K, non-personnel): {len(all_contract_items)}")
    print(f"  With some form of attachment: {len(with_docs)}")
    print(f"  Resolution paragraph ONLY (no source doc): {len(without_docs)}")

    total_dollars = sum(c["max_amount"] for c in all_contract_items)
    doc_dollars = sum(c["max_amount"] for c in with_docs)
    nodoc_dollars = sum(c["max_amount"] for c in without_docs)
    print(f"\n  Total contract value: ${total_dollars:,.0f}")
    print(f"  $ with documents: ${doc_dollars:,.0f}")
    print(f"  $ resolution-only: ${nodoc_dollars:,.0f}")

    # What types of docs are attached when they exist?
    print(f"\n{'─' * 90}")
    print("WHAT'S ATTACHED WHEN DOCS EXIST?")
    print("(PO forms ≠ actual contracts; they're internal purchase orders)")
    print(f"{'─' * 90}")
    type_counts = defaultdict(int)
    for c in with_docs:
        for ft in c["file_types"]:
            type_counts[ft] += 1
    for ft in sorted(type_counts, key=lambda x: type_counts[x], reverse=True):
        print(f"  {ft:20s}: {type_counts[ft]:4d}")

    # Biggest resolution-only items
    print(f"\n{'─' * 90}")
    print("TOP 20 CONTRACTS WITH RESOLUTION ONLY (no source document)")
    print(f"{'─' * 90}")
    without_docs_sorted = sorted(without_docs, key=lambda x: x["max_amount"], reverse=True)
    for i, c in enumerate(without_docs_sorted[:20]):
        print(f"\n  [{i+1}] {c['date']} | ${c['max_amount']:>12,.0f}")
        if c["vendor"]:
            print(f"      Vendor: {c['vendor']}")
        print(f"      Resolution: {c['text_preview'][:200]}...")

    # Export CSV
    csv_file = "jcboe_contract_source_docs.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "date", "meeting", "vendor", "max_amount", "has_file",
            "file_count", "file_types", "attached_files", "resolution_text"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"\nCSV exported: {csv_file}")


# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 3: RETROACTIVE DOCUMENTATION TRACKING
# Do undocumented contracts from Aug-Sep 2024 ever get documented
# in subsequent meetings? Track by vendor, PO number, project name.
# ═══════════════════════════════════════════════════════════════════
def check_retroactive_docs():
    print(f"\n\n{'=' * 90}")
    print("INVESTIGATION 3: RETROACTIVE DOCUMENTATION TRACKING")
    print("Do the undocumented Aug-Sep 2024 contracts ever get follow-up docs?")
    print("Searching ALL subsequent meetings (Oct 2024 onward) for references.")
    print("=" * 90)

    all_meetings = get_all_meetings()

    # ─── Step 1: Define what we're looking for ────────────────────
    # These are the specific undocumented projects from Aug 26 & Sep 25, 2024
    search_targets = [
        {
            "label": "GL Group — HVAC VRF PS#27 ($2.3M + $2.635M)",
            "search_terms": ["gl group", "vrf", "ps#27", "ps #27", "zampella", "heat recovery"],
            "project_ids": ["EDS24-001-6-17", "EDS24-001-6-18"],
            "amount": 4_935_000,
        },
        {
            "label": "GL Group — HVAC VRF Academy I ($1.99M + $2.285M)",
            "search_terms": ["gl group", "academy i", "vrf", "heat recovery"],
            "project_ids": ["EDS24-001-6-17"],
            "amount": 4_275_000,
        },
        {
            "label": "GL Group — Bathroom Renovation PS#23 ($3.7M)",
            "search_terms": ["gl group", "ps#23", "ps #23", "gandhi", "bathroom", "renovation"],
            "project_ids": ["EDS24-001-5-51"],
            "amount": 3_700_000,
        },
        {
            "label": "GL Group — HVAC demo PS#23/Academy I ($620K)",
            "search_terms": ["gl group", "demo", "uninvent", "hvac"],
            "project_ids": ["EDS24-001-6-20"],
            "amount": 620_000,
        },
        {
            "label": "GL Group — HVAC PS#7 Williams ($835K)",
            "search_terms": ["gl group", "ps#7", "ps #7", "williams", "cooling tower"],
            "project_ids": ["EDS24-001-6-27"],
            "amount": 835_000,
        },
        {
            "label": "White Rock Corp — Roof PS#41 Change Order ($2.47M)",
            "search_terms": ["white rock", "ps#41", "ps #41", "roof replacement"],
            "project_ids": ["24-004003"],
            "amount": 2_474_148,
        },
        {
            "label": "Edmentum — Tutoring Services ($2.13M)",
            "search_terms": ["edmentum", "tutoring services", "omnia"],
            "project_ids": ["R19103"],
            "amount": 2_128_132,
        },
        {
            "label": "Edmentum — Virtual Instruction ($578K Aug + $882K Sep)",
            "search_terms": ["edmentum", "virtual instruction", "edoptions academy"],
            "project_ids": [],
            "amount": 1_460_495,
        },
        {
            "label": "Spectrotel — Telecom Services ($240K)",
            "search_terms": ["spectrotel", "telecommunication"],
            "project_ids": ["25-002236"],
            "amount": 240_000,
        },
        {
            "label": "Sherwood Pool — Emergency Pool Repairs ($235K + $90K)",
            "search_terms": ["sherwood", "spcg", "pool"],
            "project_ids": ["24-002720"],
            "amount": 325_235,
        },
        {
            "label": "Adams Lattiboudere — Legal Services ($225K)",
            "search_terms": ["adams", "lattiboudere", "labor & employment", "labor and employment"],
            "project_ids": [],
            "amount": 225_000,
        },
        {
            "label": "Machado Law Group — Special Ed Legal ($75K)",
            "search_terms": ["machado", "special education"],
            "project_ids": [],
            "amount": 75_000,
        },
        {
            "label": "Food Service Meal Contract Amendment ($2.77M)",
            "search_terms": ["pre-plated", "commercial vended meals", "pd22-23-fd12-64"],
            "project_ids": ["PD22-23-FD12-64"],
            "amount": 2_774_730,
        },
        {
            "label": "Natural Lawn Care — Landscaping ($198K)",
            "search_terms": ["natural lawn", "landscaping", "escnj 23/24-09"],
            "project_ids": ["ESCNJ 23/24-09"],
            "amount": 197_600,
        },
        {
            "label": "Mobile Modular — Remove TCUs PS#17 ($135K)",
            "search_terms": ["mobile modular", "tcu", "ps#17", "ps #17"],
            "project_ids": ["298000539"],
            "amount": 135_450,
        },
        {
            "label": "Christopher Lighty — Security Consultant ($60K)",
            "search_terms": ["christopher lighty", "lighty", "security/environmental", "security consultant"],
            "project_ids": [],
            "amount": 60_000,
        },
    ]

    total_undocumented = sum(t["amount"] for t in search_targets)
    print(f"\nTracking {len(search_targets)} undocumented projects totaling ${total_undocumented:,.0f}")
    print(f"Searching all meetings from Oct 2024 onward...\n")

    # ─── Step 2: Fetch all subsequent meetings ────────────────────
    subsequent = [
        m for m in all_meetings
        if m.get("numberdate") and str(m["numberdate"]) >= "20241001"
    ]
    subsequent.sort(key=lambda m: str(m["numberdate"]))
    print(f"Subsequent meetings to search: {len(subsequent)}\n")

    # Store all meeting texts for searching
    meeting_texts = {}
    meeting_files = {}

    for i, m in enumerate(subsequent):
        mdate = str(m["numberdate"])
        mname = m.get("name", "")
        print(f"  [{i+1}/{len(subsequent)}] Fetching {mdate} | {mname[:40]}...", end="", flush=True)

        resp = fetch_meeting_html(m)
        time.sleep(REQUEST_DELAY)

        if not resp or resp.status_code != 200:
            print(" FAILED")
            continue

        soup = BeautifulSoup(resp.content, "html.parser")
        full_text = soup.get_text(separator=" ")
        meeting_texts[mdate + "|" + mname] = full_text

        # Also catalog all files in this meeting
        files_in_meeting = []
        for fd in soup.find_all("div", class_="public-file"):
            link = fd.find("a")
            if link:
                files_in_meeting.append({
                    "text": link.get_text(strip=True),
                    "href": link.get("href", ""),
                })
        meeting_files[mdate + "|" + mname] = files_in_meeting
        print(f" {len(full_text)} chars, {len(files_in_meeting)} files")

    # ─── Step 3: Search for each target ──────────────────────────
    print(f"\n{'─' * 90}")
    print("RESULTS: Did documentation ever follow?")
    print(f"{'─' * 90}")

    never_found = []
    found_later = []

    for target in search_targets:
        print(f"\n  📋 {target['label']}")
        print(f"     Original amount: ${target['amount']:,.0f}")

        hits = []
        for meeting_key, text in meeting_texts.items():
            text_lower = text.lower()
            mdate = meeting_key.split("|")[0]

            # Check search terms
            terms_found = []
            for term in target["search_terms"]:
                if term.lower() in text_lower:
                    terms_found.append(term)

            # Check project IDs
            ids_found = []
            for pid in target["project_ids"]:
                if pid.lower() in text_lower:
                    ids_found.append(pid)

            # Need at least 2 search terms matching, or 1 project ID
            if len(terms_found) >= 2 or len(ids_found) >= 1:
                # Check if this meeting has relevant files
                files = meeting_files.get(meeting_key, [])
                relevant_files = []
                for f in files:
                    f_combined = (f["text"] + " " + f["href"]).lower()
                    if any(t.lower() in f_combined for t in target["search_terms"][:2]):
                        relevant_files.append(f["text"])
                    # Also check for PO/contract docs
                    for pid in target["project_ids"]:
                        if pid.lower() in f_combined:
                            relevant_files.append(f["text"])

                hits.append({
                    "date": mdate,
                    "meeting": meeting_key.split("|")[1],
                    "terms_matched": terms_found,
                    "ids_matched": ids_found,
                    "has_relevant_files": len(relevant_files) > 0,
                    "relevant_files": relevant_files,
                })

        if hits:
            has_any_doc = any(h["has_relevant_files"] for h in hits)
            for h in hits:
                file_status = "✅ WITH DOCS" if h["has_relevant_files"] else "❌ NO DOCS"
                print(f"     {h['date']} | {file_status} | matched: {', '.join(h['terms_matched'][:3])}", end="")
                if h["ids_matched"]:
                    print(f" + ID: {', '.join(h['ids_matched'])}", end="")
                print()
                if h["relevant_files"]:
                    for rf in h["relevant_files"][:3]:
                        print(f"       📎 {rf[:70]}")

            if has_any_doc:
                found_later.append(target)
            else:
                print(f"     ⚠️  REFERENCED IN LATER MEETINGS BUT STILL NO DOCUMENTS")
                never_found.append(target)
        else:
            print(f"     ⚠️  NEVER REFERENCED AGAIN IN ANY SUBSEQUENT MEETING")
            never_found.append(target)

    # ─── Summary ─────────────────────────────────────────────────
    print(f"\n{'=' * 90}")
    print("RETROACTIVE DOCUMENTATION SUMMARY")
    print(f"{'=' * 90}")
    print(f"\nTotal undocumented projects tracked: {len(search_targets)}")
    print(f"Total undocumented value: ${total_undocumented:,.0f}")
    print(f"\n  Later documented:     {len(found_later)} projects (${sum(t['amount'] for t in found_later):,.0f})")
    print(f"  NEVER documented:     {len(never_found)} projects (${sum(t['amount'] for t in never_found):,.0f})")

    if never_found:
        print(f"\n  Projects that NEVER received documentation:")
        for t in sorted(never_found, key=lambda x: x["amount"], reverse=True):
            print(f"    ${t['amount']:>12,.0f}  {t['label']}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("GMS Deep Dive v3 — Budget Docs + Contract Source Docs + Retroactive Tracking")
    print(f"Jersey City Board of Education")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    budget_results = check_budget_docs()
    check_contract_docs()
    check_retroactive_docs()

    print(f"\n{'=' * 90}")
    print("ANALYSIS COMPLETE")
    print(f"{'=' * 90}")
    print("Files saved:")
    print("  jcboe_contract_source_docs.csv — every contract approval with doc status")
    print("\nThree investigations answered:")
    print("  1. Are budget documents publicly available as legally required?")
    print("  2. When the board votes to approve a contract, is the actual")
    print("     signed agreement attached, or just a summary paragraph?")
    print("  3. Do the specific undocumented Aug-Sep 2024 contracts")
    print("     (GL Group, White Rock, Edmentum, etc.) ever get documented later?")
