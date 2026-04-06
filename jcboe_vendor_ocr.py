"""
GMS Vendor Name Extractor — OCR PO Forms for Missing Vendor Names
==================================================================
For contract items where the vendor name isn't in the resolution text,
download the attached PO form and OCR it to find the vendor name.
"""

import json
import os
import re
import csv
import time
import sys
from datetime import datetime
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

SITE = "nj/jcps/Board.nsf"
BASE_URL = f"https://go.boarddocs.com/{SITE}"
COMMITTEE_ID = "A9QM9A5A1F6C"
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    "referer": f"https://go.boarddocs.com/{SITE}/Public",
}
PDF_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "referer": f"https://go.boarddocs.com/{SITE}/Public",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}
REQUEST_DELAY = 1.5
DOWNLOAD_DIR = "pdf_samples"


def make_request(url, data=None):
    for attempt in range(3):
        try:
            return requests.post(url, headers=HEADERS, data=data, timeout=45)
        except Exception as e:
            print(f"    [RETRY {attempt+1}] {e}")
            time.sleep(3)
    return None


def download_pdf(href, filename):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
        return filepath, os.path.getsize(filepath)
    if href.startswith("/"):
        url = f"https://go.boarddocs.com{href}"
    else:
        url = href
    try:
        resp = requests.get(url, headers=PDF_HEADERS, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 100:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return filepath, len(resp.content)
    except Exception as e:
        print(f"      Download error: {e}")
    return None, 0


def ocr_first_page(filepath):
    """OCR just the first page of a PDF to extract vendor info."""
    if not HAS_PYMUPDF or not HAS_TESSERACT:
        return None
    try:
        doc = fitz.open(filepath)
        if len(doc) == 0:
            doc.close()
            return None
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img)
        doc.close()
        return text
    except Exception as e:
        return f"[OCR error: {e}]"


def extract_text_native(filepath):
    """Try native text extraction first (faster than OCR)."""
    if not HAS_PYMUPDF:
        return None
    try:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        # Check if it's just watermarks
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        watermark_lines = sum(1 for l in lines if re.match(
            r'^(Attachment\s+\S+\s*-\s*Board Meeting|Meeting of .+|Page \d+ of \d+)$', l))
        if not lines or watermark_lines >= len(lines) * 0.8:
            return None  # Scanned document, need OCR
        return text
    except:
        return None


def extract_vendor_from_po(text):
    """Extract vendor name from PO form / AF form text."""
    if not text or text.startswith("["):
        return None

    # PO forms typically have vendor name in these patterns:
    patterns = [
        # "VENDOR: Company Name" or "Vendor Name: X"
        r'[Vv][Ee][Nn][Dd][Oo][Rr]\s*[:#]?\s*([A-Z][A-Za-z0-9\s&,.\'\-/()]+?)(?:\n|\r|$)',
        # "PAYABLE TO: Company"
        r'[Pp][Aa][Yy][Aa][Bb][Ll][Ee]\s+[Tt][Oo]\s*:?\s*([A-Z][A-Za-z0-9\s&,.\'\-/()]+?)(?:\n|\r|$)',
        # "AWARDED TO: Company" or "Award: Company"
        r'[Aa][Ww][Aa][Rr][Dd](?:[Ee][Dd])?\s*(?:[Tt][Oo])?\s*:?\s*([A-Z][A-Za-z0-9\s&,.\'\-/()]+?)(?:\n|\r|$)',
        # "TO: Company Name" at start of line
        r'(?:^|\n)\s*TO\s*:\s*([A-Z][A-Za-z0-9\s&,.\'\-/()]+?)(?:\n|\r|$)',
        # "Company Name\nAddress" pattern — look for company-like names followed by street address
        r'(?:^|\n)\s*([A-Z][A-Za-z0-9\s&.\'\-]+(?:LLC|Inc|Corp|Ltd|Co\.|Company|Group|Services)\.?)\s*(?:\n|\r)',
        # "REMIT TO: Company"
        r'[Rr][Ee][Mm][Ii][Tt]\s+[Tt][Oo]\s*:?\s*([A-Z][A-Za-z0-9\s&,.\'\-/()]+?)(?:\n|\r|$)',
        # "Contractor: X" or "Provider: X"
        r'(?:Contractor|Provider|Consultant|Supplier)\s*:?\s*([A-Z][A-Za-z0-9\s&,.\'\-/()]+?)(?:\n|\r|$)',
        # "BID RESULTS" section — "AWARDED VENDOR" followed by name
        r'AWARDED\s+VENDOR\s*[:\n]\s*([A-Z][A-Za-z0-9\s&,.\'\-/()]+?)(?:\n|\r|$)',
        # Just look for prominent company names (capitalized, multi-word, on their own line)
        r'(?:^|\n)\s*([A-Z][A-Z0-9\s&.\'\-]{5,50}(?:LLC|INC|CORP|LTD|CO|COMPANY|GROUP|SERVICES)?\.?)\s*(?:\n|\r)',
    ]

    skip = ['jersey city', 'board of education', 'public school', 'attachment',
            'meeting of', 'page ', 'purchase order', 'approval form',
            'whereas', 'be it resolved', 'resolution', 'department',
            'approved for', 'total amount', 'account', 'fund', 'description',
            'date', 'requisition', 'the jersey']

    for p in patterns:
        matches = re.finditer(p, text, re.MULTILINE)
        for m in matches:
            candidate = m.group(1).strip().rstrip(',. \n\r')
            # Clean up
            candidate = re.sub(r'\s+', ' ', candidate).strip()
            if len(candidate) < 3 or len(candidate) > 80:
                continue
            if any(candidate.lower().startswith(s) for s in skip):
                continue
            if re.match(r'^[\d\s\-/]+$', candidate):  # All numbers
                continue
            if re.match(r'^[A-Z]{1,2}\d', candidate):  # Like "AF10413"
                continue
            # Likely a vendor name
            candidate = re.sub(r'\s*,?\s*(?:Inc|LLC|Corp|Ltd|LP|LLP)\.?\s*$', '', candidate).strip()
            return candidate

    return None


def main():
    print("=" * 90)
    print("GMS VENDOR NAME EXTRACTOR — OCR PO Forms")
    print("=" * 90)
    print(f"Timestamp: {datetime.now().isoformat()}")

    if not HAS_PYMUPDF:
        print("ERROR: PyMuPDF required. pip install PyMuPDF")
        sys.exit(1)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Load contracts with unknown vendors
    with open('jcboe_contract_source_docs.csv') as f:
        contracts = list(csv.DictReader(f))

    unknown = [r for r in contracts if not r.get('vendor', '').strip() and r['has_file'] == 'True']
    print(f"\nUnknown-vendor items with attachments: {len(unknown)}")
    print(f"(Items with no attachments can't be resolved this way)\n")

    # Get all meetings
    resp = make_request(BASE_URL + "/BD-GetMeetingsList?open",
                        f"current_committee_id={COMMITTEE_ID}")
    all_meetings = json.loads(resp.text)

    # Group unknowns by meeting date
    by_date = {}
    for r in unknown:
        d = r['date']
        if d not in by_date:
            by_date[d] = []
        by_date[d].append(r)

    print(f"Meetings to process: {len(by_date)}\n")

    # Contract detection patterns
    contract_pattern = re.compile(
        r'(approve|authorize|award|ratif).{0,30}(contract|agreement|purchase order|professional .* service)',
        re.IGNORECASE
    )
    personnel_patterns = [
        re.compile(r'(transfer|promotion|appointment|separation|leave|resignation|retirement|degree status|salary adjust)', re.IGNORECASE),
    ]

    resolved = 0
    failed = 0
    vendor_map = {}  # index in contracts -> vendor name

    for mdate in sorted(by_date.keys()):
        items_to_resolve = by_date[mdate]
        meeting = [m for m in all_meetings if str(m.get("numberdate", "")) == mdate]
        if not meeting:
            print(f"  {mdate}: Meeting not found, skipping {len(items_to_resolve)} items")
            continue

        for m in meeting:
            print(f"\n{'─' * 80}")
            print(f"[{mdate}] {m.get('name', '')[:60]}")
            print(f"{'─' * 80}")

            resp = make_request(BASE_URL + "/PRINT-AgendaDetailed",
                               f"id={m['unique']}&current_committee_id={COMMITTEE_ID}")
            time.sleep(REQUEST_DELAY)

            if not resp or resp.status_code != 200:
                print("  FAILED to fetch meeting")
                continue

            soup = BeautifulSoup(resp.content, "html.parser")

            for item_div in soup.find_all("div", class_="item"):
                rightcol = item_div.find("div", class_="rightcol") or item_div
                itembody = rightcol.find("div", class_="itembody")
                text = itembody.get_text(separator=" ", strip=True) if itembody else rightcol.get_text(separator=" ", strip=True)

                if not contract_pattern.search(text):
                    continue
                if any(p.search(text) for p in personnel_patterns):
                    continue

                # Check if this item matches one of our unknowns
                # Match by resolution text prefix
                text_prefix = text[:100].strip()
                matching_unknown = None
                for ur in items_to_resolve:
                    ur_prefix = ur.get('resolution_text', '')[:100].strip()
                    if ur_prefix and ur_prefix[:60] in text_prefix or text_prefix[:60] in ur_prefix:
                        matching_unknown = ur
                        break

                if not matching_unknown:
                    continue

                # Found a matching item — download and OCR its first attachment
                file_divs = rightcol.find_all("div", class_="public-file")
                if not file_divs:
                    continue

                for fd in file_divs[:2]:  # Try first 2 attachments
                    link = fd.find("a")
                    if not link or not link.get("href"):
                        continue

                    href = link["href"]
                    file_label = link.get_text(strip=True)
                    filename = unquote(href.split("/")[-1]) if "/" in href else file_label
                    safe_name = re.sub(r'[^\w\-.]', '_', filename)[:80]
                    safe_name = f"{mdate}_{safe_name}"

                    print(f"  Downloading: {file_label[:60]}...")
                    filepath, size = download_pdf(href, safe_name)
                    time.sleep(0.3)

                    if not filepath:
                        continue

                    # Try native text first, then OCR
                    pdf_text = extract_text_native(filepath)
                    if not pdf_text:
                        print(f"    OCR-ing...")
                        pdf_text = ocr_first_page(filepath)

                    if not pdf_text or pdf_text.startswith("["):
                        continue

                    vendor = extract_vendor_from_po(pdf_text)
                    if vendor:
                        print(f"    VENDOR FOUND: {vendor}")
                        # Update the contract record
                        idx = contracts.index(matching_unknown)
                        contracts[idx]['vendor'] = vendor
                        resolved += 1
                        items_to_resolve.remove(matching_unknown)
                        break
                    else:
                        failed += 1
                        # Save text for debugging
                        print(f"    No vendor extracted from {len(pdf_text)} chars")

    # Summary
    print(f"\n{'=' * 90}")
    print("VENDOR OCR EXTRACTION SUMMARY")
    print(f"{'=' * 90}")
    print(f"Resolved: {resolved}")
    print(f"Failed to extract: {failed}")
    still_unknown = sum(1 for r in contracts if not r.get('vendor', '').strip())
    print(f"Still unknown: {still_unknown}/{len(contracts)}")
    print(f"Known vendors: {len(contracts) - still_unknown}/{len(contracts)} ({(len(contracts) - still_unknown) / len(contracts) * 100:.0f}%)")

    # Save updated CSV
    fieldnames = list(contracts[0].keys())
    with open('jcboe_contract_source_docs.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(contracts)
    print(f"\nCSV updated: jcboe_contract_source_docs.csv")


if __name__ == "__main__":
    main()
