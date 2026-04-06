"""
GMS Transparency Gap Analyzer v2 — FILTERED
Jersey City Board of Education
=============================================
Filters out noise (budget resolutions, monthly bill lists, reorg boilerplate)
to focus on the real signal: specific vendor/service contracts missing documents.
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
CUTOFF_DATE = "20240101"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    "referer": f"https://go.boarddocs.com/{SITE}/Public",
}

REQUEST_DELAY = 1.5

# ─── Detection patterns ─────────────────────────────────────────
DOLLAR_PATTERN = re.compile(r'\$[\d,]+(?:\.\d{2})?')

# Items that indicate a specific vendor/service contract
CONTRACT_KEYWORDS = [
    'contract', 'agreement', 'vendor', 'bid', 'rfp', 'rfi', 'rfq',
    'purchase order', 'procurement', 'consultant', 'professional service',
    'award', 'not to exceed', 'nte', 'change order',
    'memorandum of understanding', 'mou', 'lease', 'rental',
    'legal services', 'architect', 'construction',
    'renovation', 'repair', 'maintenance agreement',
    'transportation', 'food service', 'tuition',
    'insurance', 'technology', 'software', 'license',
]

# ─── NOISE FILTERS: patterns to EXCLUDE ──────────────────────────
EXCLUDE_PATTERNS = [
    # Budget resolutions (the $443M+ items)
    r'resolution to adopt the (preliminary|final) \d{4}[/\-]\d{4} school year budget',
    r'adopts the (preliminary|final) \d{4}[/\-]\d{4} school year budget',
    # Monthly bill lists / expenditure runs
    r'approve/accept the monthly? (bill|expenditure|payment) (list|schedule|run)',
    r'approve.*monthly.*bill.*list',
    r'n\.?j\.?s\.?a\.?\s*\.?\s*18a:19-9',  # The statute cited in every monthly bill list
    # Tax levy resolutions
    r'tax levy and payroll tax payment schedule',
    r'approves the \d{4}[/\-]\d{2,4} tax levy',
    # Bank cap resolutions
    r'bank cap in the total amount',
    r'cap adjustment of increase in health care',
    # Reorganization boilerplate
    r'designation of (official )?depositor',
    r'designation of (official )?newspaper',
    r'appointment of (board )?attorney',
    r'appointment of (board )?auditor',
    r'appointment of (board )?secretary',
    r'appointment of (board )?treasurer',
    r'establish(ment of)? (petty cash|regular meeting|board meeting)',
    r'(election|appointment) of (president|vice.president)',
    r'(adopt|acceptance of).*(bylaw|rule|procedure|robert.s rules)',
    r'salaries? (of|for) (the )?(superintendent|board secretary|board attorney)',
    r'authorize.*to sign (checks|warrants)',
    r'bonding of (board )?employees',
    # Travel/mileage reimbursement policy (not a contract)
    r'travel and expense reimbursement',
    r'mileage reimbursement',
    # Transfer resolutions (moving money between accounts)
    r'(budget )?transfer(s)? (of|between|from)',
    r'line item transfer',
    # Certification of budget
    r'certif(y|ication) (of |that )(the )?(budget|sufficient)',
    # Secretary/treasurer reports
    r"(secretary|treasurer).s (monthly )?report",
    r"board secretary.s report",
]

EXCLUDE_COMPILED = [re.compile(p, re.IGNORECASE) for p in EXCLUDE_PATTERNS]


def make_request(url, data=None):
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=HEADERS, data=data, timeout=45)
            return resp
        except requests.exceptions.RequestException as e:
            print(f"    [RETRY {attempt+1}] {e}")
            time.sleep(3)
    return None


def get_meetings_since(cutoff):
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
    amounts = DOLLAR_PATTERN.findall(text)
    parsed = []
    for a in amounts:
        try:
            val = float(a.replace('$', '').replace(',', ''))
            if val > 0:
                parsed.append(val)
        except ValueError:
            pass
    return parsed


def is_noise(text):
    """Return True if this item matches any exclusion pattern."""
    for pattern in EXCLUDE_COMPILED:
        if pattern.search(text):
            return True
    return False


def has_contract_language(text):
    text_lower = text.lower()
    found = [kw for kw in CONTRACT_KEYWORDS if kw in text_lower]
    return found


def classify_item(text, dollar_amounts):
    """Classify the type of financial item for reporting."""
    text_lower = text.lower()

    if any(kw in text_lower for kw in ['rfp', 'rfq', 'rfi', 'bid', 'procurement']):
        return "COMPETITIVE_BID"
    if any(kw in text_lower for kw in ['professional service', 'consultant', 'legal services']):
        return "PROFESSIONAL_SERVICE"
    if any(kw in text_lower for kw in ['construction', 'renovation', 'repair', 'architect']):
        return "CONSTRUCTION"
    if any(kw in text_lower for kw in ['transportation', 'food service']):
        return "OPERATIONS"
    if any(kw in text_lower for kw in ['software', 'technology', 'license']):
        return "TECHNOLOGY"
    if any(kw in text_lower for kw in ['tuition', 'stipend']):
        return "EDUCATIONAL"
    if any(kw in text_lower for kw in ['insurance']):
        return "INSURANCE"
    if any(kw in text_lower for kw in ['lease', 'rental']):
        return "LEASE"
    if any(kw in text_lower for kw in ['change order']):
        return "CHANGE_ORDER"
    if any(kw in text_lower for kw in ['contract', 'agreement', 'vendor', 'award', 'nte', 'not to exceed', 'mou']):
        return "CONTRACT_GENERAL"
    return "OTHER_FINANCIAL"


def extract_vendor_name(text):
    """Try to extract a vendor/company name from the item text."""
    # Common patterns in board resolutions:
    # "...with [Vendor Name], ..."
    # "...to [Vendor Name] for..."
    # "...from [Vendor Name],..."
    # "...[Vendor Name], LLC..."
    # "...[Vendor Name], Inc..."

    patterns = [
        # "contract with X" / "agreement with X"
        r'(?:contract|agreement|mou|memorandum)\s+(?:by and\s+)?(?:between|with)\s+([A-Z][A-Za-z\s&,.\'-]+?)(?:\s*,\s*(?:LLC|Inc|Corp|Ltd|LP|LLP|Co\b))?(?:\s*[,.]|\s+for\s+|\s+to\s+|\s+in\s+|\s+at\s+)',
        # "award to X"
        r'(?:award|awarded)\s+(?:a\s+)?(?:contract\s+)?to\s+([A-Z][A-Za-z\s&,.\'-]+?)(?:\s*,\s*(?:LLC|Inc|Corp|Ltd|LP|LLP|Co\b))?(?:\s*[,.]|\s+for\s+|\s+in\s+)',
        # "services of X" / "services from X" / "services provided by X"
        r'services?\s+(?:of|from|provided by|rendered by)\s+([A-Z][A-Za-z\s&,.\'-]+?)(?:\s*,\s*(?:LLC|Inc|Corp|Ltd|LP|LLP|Co\b))?(?:\s*[,.]|\s+for\s+|\s+in\s+)',
        # "vendor: X" or "provider: X"
        r'(?:vendor|provider|contractor|consultant)[:\s]+([A-Z][A-Za-z\s&,.\'-]+?)(?:\s*,\s*(?:LLC|Inc|Corp|Ltd|LP|LLP|Co\b))?(?:\s*[,.]|\s+for\s+)',
        # Entity suffixes
        r'([A-Z][A-Za-z\s&.\'-]+?(?:LLC|Inc\.?|Corp\.?|Ltd\.?|LP|LLP|Associates|Group|Company|Co\.))',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip().rstrip(',.')
            # Filter out false positives
            if len(name) > 3 and len(name) < 80:
                skip_words = ['Board of Education', 'Jersey City', 'State of New Jersey',
                              'BE IT RESOLVED', 'WHEREAS', 'Superintendent',
                              'School Business Administrator', 'County of Hudson']
                if not any(sw.lower() in name.lower() for sw in skip_words):
                    return name
    return ""


def parse_agenda_items(soup):
    items = []
    item_divs = soup.find_all("div", class_="item")

    for item_div in item_divs:
        item_data = {}
        leftcol = item_div.find("div", class_="leftcol")
        item_data["item_number"] = leftcol.get_text(strip=True) if leftcol else ""

        rightcol = item_div.find("div", class_="rightcol")
        if not rightcol:
            rightcol = item_div

        itembody = rightcol.find("div", class_="itembody")
        if itembody:
            item_data["text"] = itembody.get_text(separator=" ", strip=True)
        else:
            item_data["text"] = rightcol.get_text(separator=" ", strip=True)

        files = []
        file_divs = rightcol.find_all("div", class_="public-file") if rightcol else []
        for fd in file_divs:
            link = fd.find("a")
            if link and link.get("href"):
                files.append({
                    "href": link["href"],
                    "text": link.get_text(strip=True),
                })
        item_data["files"] = files
        item_data["file_count"] = len(files)
        items.append(item_data)

    return items


def analyze_meeting(meeting):
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
    all_public_files = soup.find_all("div", class_="public-file")

    result = {
        "meeting_id": mid,
        "date": mdate,
        "name": mname,
        "total_agenda_items": len(items),
        "total_pdfs": len(all_public_files),
        "flagged_items": [],
        "noise_items": [],
    }

    for item in items:
        text = item["text"]
        dollar_amounts = extract_dollar_amounts(text)
        contract_keywords = has_contract_language(text)

        if not (dollar_amounts or contract_keywords):
            continue

        # Check if this is noise
        if is_noise(text):
            result["noise_items"].append(item)
            continue

        max_amount = max(dollar_amounts) if dollar_amounts else 0
        item["dollar_amounts"] = dollar_amounts
        item["max_amount"] = max_amount
        item["contract_keywords"] = contract_keywords
        item["has_attachment"] = item["file_count"] > 0
        item["transparency_gap"] = not item["has_attachment"]
        item["category"] = classify_item(text, dollar_amounts)
        item["vendor"] = extract_vendor_name(text)
        result["flagged_items"].append(item)

    return result


def main():
    print("=" * 80)
    print("GMS TRANSPARENCY GAP ANALYZER v2 — FILTERED")
    print("Jersey City Board of Education — Jan 2024 to Present")
    print("=" * 80)
    print("Filters active: budget resolutions, monthly bill lists, reorg boilerplate,")
    print("tax levy, bank cap, transfers, secretary reports EXCLUDED.")
    print("Focus: specific vendor contracts, professional services, procurements.")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Get meetings
    print("Fetching meetings since Jan 2024...")
    meetings = get_meetings_since(CUTOFF_DATE)
    print(f"Found {len(meetings)} meetings.\n")

    all_results = []
    all_flagged = []
    all_gaps = []
    total_noise = 0

    for i, meeting in enumerate(meetings):
        mdate = str(meeting["numberdate"])
        mname = meeting.get("name", "")
        print(f"[{i+1}/{len(meetings)}] {mdate} - {mname[:50]}...", end="", flush=True)

        result = analyze_meeting(meeting)
        time.sleep(REQUEST_DELAY)

        if not result:
            print(" FAILED")
            continue

        flagged = result["flagged_items"]
        gaps = [f for f in flagged if f["transparency_gap"]]
        noise = len(result["noise_items"])
        total_noise += noise

        all_results.append(result)
        all_flagged.extend(flagged)
        all_gaps.extend(gaps)

        status = f" {len(flagged)} contracts found, {len(gaps)} missing docs"
        if noise:
            status += f", {noise} noise filtered"
        if gaps:
            status += " ⚠️"
        print(status)

    # ─── REPORT ──────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("FILTERED TRANSPARENCY GAP REPORT")
    print("=" * 80)

    print(f"\nMeetings analyzed: {len(all_results)}")
    print(f"Noise items filtered out: {total_noise}")
    print(f"Contract/vendor items identified: {len(all_flagged)}")
    print(f"  With supporting documents: {len(all_flagged) - len(all_gaps)}")
    print(f"  WITHOUT supporting documents: {len(all_gaps)} ← TRANSPARENCY GAPS")

    if all_flagged:
        rate = ((len(all_flagged) - len(all_gaps)) / len(all_flagged)) * 100
        print(f"  Document attachment rate: {rate:.1f}%")

    total_dollars = sum(item.get("max_amount", 0) for item in all_flagged)
    gap_dollars = sum(item.get("max_amount", 0) for item in all_gaps)
    documented_dollars = total_dollars - gap_dollars

    print(f"\nTotal $ in contract items: ${total_dollars:,.2f}")
    print(f"  $ with documents attached: ${documented_dollars:,.2f}")
    print(f"  $ WITHOUT documents attached: ${gap_dollars:,.2f}")

    # ─── GAPS BY CATEGORY ────────────────────────────────────────
    print(f"\n{'─' * 80}")
    print("TRANSPARENCY GAPS BY CATEGORY")
    print(f"{'─' * 80}")

    cat_gaps = defaultdict(lambda: {"count": 0, "dollars": 0})
    for item in all_gaps:
        cat = item.get("category", "UNKNOWN")
        cat_gaps[cat]["count"] += 1
        cat_gaps[cat]["dollars"] += item.get("max_amount", 0)

    for cat in sorted(cat_gaps.keys(), key=lambda c: cat_gaps[c]["dollars"], reverse=True):
        info = cat_gaps[cat]
        print(f"  {cat:25s} {info['count']:4d} items   ${info['dollars']:>15,.2f}")

    # ─── VENDOR FREQUENCY IN GAPS ────────────────────────────────
    print(f"\n{'─' * 80}")
    print("VENDORS WITH MOST UNDOCUMENTED ITEMS")
    print(f"{'─' * 80}")

    vendor_gaps = defaultdict(lambda: {"count": 0, "dollars": 0, "dates": []})
    for item in all_gaps:
        v = item.get("vendor", "")
        if v:
            vendor_gaps[v]["count"] += 1
            vendor_gaps[v]["dollars"] += item.get("max_amount", 0)
            # find meeting date
            for r in all_results:
                if item in r["flagged_items"]:
                    vendor_gaps[v]["dates"].append(r["date"])
                    break

    if vendor_gaps:
        top_vendors = sorted(vendor_gaps.items(), key=lambda x: x[1]["dollars"], reverse=True)
        for v, info in top_vendors[:20]:
            dates_str = ", ".join(sorted(set(info["dates"]))[:3])
            if len(info["dates"]) > 3:
                dates_str += f" +{len(info['dates'])-3} more"
            print(f"  {v[:45]:45s} {info['count']:3d}x  ${info['dollars']:>12,.2f}  ({dates_str})")
    else:
        print("  (Vendor extraction found no named vendors in gap items)")

    # ─── TOP INDIVIDUAL GAPS ─────────────────────────────────────
    print(f"\n{'─' * 80}")
    print("TOP 25 TRANSPARENCY GAPS (specific contracts, no documents)")
    print(f"{'─' * 80}")

    gaps_sorted = sorted(all_gaps, key=lambda x: x.get("max_amount", 0), reverse=True)
    for i, gap in enumerate(gaps_sorted[:25]):
        amounts_str = ", ".join(f"${a:,.2f}" for a in gap.get("dollar_amounts", [])[:5])
        if len(gap.get("dollar_amounts", [])) > 5:
            amounts_str += " ..."
        vendor = gap.get("vendor", "NO VENDOR IDENTIFIED")
        cat = gap.get("category", "")

        date_str = ""
        for r in all_results:
            if gap in r["flagged_items"]:
                date_str = r["date"]
                break

        print(f"\n  [{i+1}] {date_str} | Item {gap['item_number']} | {cat}")
        if vendor:
            print(f"      Vendor: {vendor}")
        print(f"      Amounts: {amounts_str}")
        preview = gap["text"][:250].replace("\n", " ")
        print(f"      Preview: {preview}...")

    # ─── MEETINGS RANKED ─────────────────────────────────────────
    print(f"\n{'─' * 80}")
    print("MEETINGS RANKED BY FILTERED TRANSPARENCY GAPS")
    print(f"{'─' * 80}")

    for r in sorted(all_results, key=lambda r: len([f for f in r["flagged_items"] if f["transparency_gap"]]), reverse=True)[:15]:
        gaps_in = [f for f in r["flagged_items"] if f["transparency_gap"]]
        if gaps_in:
            gap_d = sum(g.get("max_amount", 0) for g in gaps_in)
            print(f"  {r['date']} | {r['name'][:45]:45s} | {len(gaps_in):3d} gaps | ${gap_d:>14,.2f}")

    # ─── EXPORT CSV ──────────────────────────────────────────────
    csv_file = "jcboe_filtered_gaps.csv"
    print(f"\nExporting to {csv_file}...")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "meeting_date", "meeting_name", "item_number", "category",
            "vendor", "dollar_amounts", "max_amount",
            "contract_keywords", "has_attachment", "transparency_gap",
            "file_count", "attached_files", "item_text_preview"
        ])
        for result in all_results:
            for item in result["flagged_items"]:
                writer.writerow([
                    result["date"],
                    result["name"],
                    item["item_number"],
                    item.get("category", ""),
                    item.get("vendor", ""),
                    "; ".join(f"${a:,.2f}" for a in item.get("dollar_amounts", [])),
                    item.get("max_amount", 0),
                    "; ".join(item.get("contract_keywords", [])),
                    item.get("has_attachment", False),
                    item.get("transparency_gap", False),
                    item.get("file_count", 0),
                    "; ".join(f["text"][:60] for f in item.get("files", [])),
                    item["text"][:500].replace("\n", " "),
                ])
    print(f"Done. Saved: {csv_file}")
    print(f"\nAlso contains all items WITH attachments for comparison analysis.")


if __name__ == "__main__":
    main()
