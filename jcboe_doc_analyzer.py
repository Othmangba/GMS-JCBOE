"""
GMS Document Content Analyzer — What's Actually In The Attachments?
===================================================================
Downloads a sample of the PDFs attached to contract items and extracts
their contents. Answers: what does the public actually get to see?

Categories to analyze:
- PO forms (the "AF" numbered docs that make up 330 of 340 attachments)
- The 4 items classified as actual "contracts"
- The 6 items classified as "attachments"
- Compare documented vs undocumented items side by side
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

# Optional: try to import PDF reader
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False

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
# For downloading PDFs we need browser-like headers
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
            resp = requests.post(url, headers=HEADERS, data=data, timeout=45)
            return resp
        except Exception as e:
            print(f"    [RETRY {attempt+1}] {e}")
            time.sleep(3)
    return None


def download_pdf(href, filename):
    """Download a PDF from BoardDocs."""
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
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return filepath, len(resp.content)
        else:
            return None, 0
    except Exception as e:
        print(f"      Download error: {e}")
        return None, 0


def is_only_watermark(text):
    """Check if extracted text is just BoardDocs page stamps, not real content."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return True
    watermark_lines = sum(1 for l in lines if re.match(
        r'^(Attachment\s+\S+\s*-\s*Board Meeting|Meeting of .+|Page \d+ of \d+)$', l))
    return watermark_lines >= len(lines) * 0.8


def ocr_pdf(filepath, max_pages=5):
    """OCR a scanned PDF using tesseract. Only OCRs first max_pages to save time."""
    if not HAS_TESSERACT or not HAS_PYMUPDF:
        return None, 0
    try:
        doc = fitz.open(filepath)
        page_count = len(doc)
        text = ""
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            # Render page to image at 200 DPI
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = pytesseract.image_to_string(img)
            text += page_text + "\n"
        doc.close()
        return text, page_count
    except Exception as e:
        return f"[OCR error: {e}]", 0


def extract_pdf_text(filepath):
    """Extract text from a PDF. Falls back to OCR for scanned documents."""
    if HAS_PYMUPDF:
        try:
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            page_count = len(doc)
            doc.close()

            # If text is just watermarks, try OCR
            if is_only_watermark(text) and HAS_TESSERACT:
                print(f"     (Scanned PDF detected, running OCR on first 5 pages...)")
                ocr_text, _ = ocr_pdf(filepath)
                if ocr_text and not ocr_text.startswith("["):
                    return ocr_text, page_count

            return text, page_count
        except Exception as e:
            return f"[PyMuPDF error: {e}]", 0

    if HAS_PDFMINER:
        try:
            text = pdfminer_extract(filepath)
            return text, 0  # pdfminer doesn't easily give page count
        except Exception as e:
            return f"[pdfminer error: {e}]", 0

    return "[No PDF reader available - install PyMuPDF: pip3 install PyMuPDF]", 0


def analyze_pdf_content(text, filename="", page_count=0, file_size=0):
    """Analyze what type of document this is based on content and metadata.

    Uses both text content analysis and filename/metadata heuristics to
    classify documents into specific categories, reducing the 'OTHER' bucket.
    """
    text_lower = text.lower()
    fname_lower = filename.lower()
    text_len = len(text.strip())

    findings = {
        "has_signatures": bool(re.search(r'(signature|signed by|authorized by|witness|notary)', text_lower)),
        "has_terms": bool(re.search(r'(terms and conditions|term of (contract|agreement)|shall commence|shall terminate|duration|effective.*throu)', text_lower)),
        "has_scope": bool(re.search(r'(scope of (work|services)|deliverables|specifications|shall provide|shall perform|services to be rendered)', text_lower)),
        "has_dollar_amounts": bool(re.search(r'\$[\d,]+', text)),
        "has_dates": bool(re.search(r'(effective date|commencement|expiration|through|thru)\s*:?\s*\w+\s+\d', text_lower)),
        "has_vendor_info": bool(re.search(r'(vendor|contractor|consultant|provider|company|firm)\s*:?\s*[A-Z]', text)),
        "has_insurance_requirements": bool(re.search(r'(insurance|liability|indemnif)', text_lower)),
        "has_termination_clause": bool(re.search(r'(terminat|cancel|breach|default|remedy)', text_lower)),
        "has_payment_terms": bool(re.search(r'(payment|invoice|billing|net \d+|upon completion|monthly)', text_lower)),
        "has_legal_boilerplate": bool(re.search(r'(governing law|jurisdiction|dispute|arbitrat|force majeure|severab)', text_lower)),
        "has_po_number": bool(re.search(r'(p/?o\s*#|purchase order|requisition|approval form)', text_lower)),
        "has_account_code": bool(re.search(r'(acct|account)\s*(#|code|number)?\s*\d{2}[-.]?\d{3}', text_lower)),
        "has_board_resolution": bool(re.search(r'(be it resolved|whereas\s*,|now,?\s*therefore|board of education)', text_lower)),
        # New signals
        "has_bid_tabulation": bool(re.search(r'(bid tabulation|bid summary|bid results|bidder|low bid|responsive bid|bid opening|bid award)', text_lower)),
        "has_renewal_language": bool(re.search(r'(renew|renewal|year\s+\d\s+of|extend|extension|maintenance.*support|license.*maint|subscription)', text_lower)),
        "has_amendment_language": bool(re.search(r'(amendment|change order|addendum|modification|supplement|revised|increase.*amount|additional.*amount)', text_lower)),
        "has_whereas_pattern": bool(re.search(r'whereas\s*,.*whereas\s*,', text_lower, re.DOTALL)),
        "has_af_form_markers": bool(re.search(r'(af\s*\d{4,5}|approval\s*form|approved\s*for\s*payment|fund\s*cert)', text_lower)),
        "has_software_language": bool(re.search(r'(software|license|saas|cloud|hosting|subscription|proprietary)', text_lower)),
        "has_tuition_language": bool(re.search(r'(tuition|sending.*receiving|iep|individualized education|out.of.district|oodt)', text_lower)),
    }

    # --- Classification logic (ordered from most specific to least) ---

    # 1. ACTUAL_CONTRACT — has contractual terms + scope + legal weight
    if findings["has_terms"] and findings["has_scope"] and (findings["has_signatures"] or findings["has_legal_boilerplate"]):
        doc_type = "ACTUAL_CONTRACT"

    # 2. AMENDMENT — change orders or contract modifications
    elif findings["has_amendment_language"] and findings["has_dollar_amounts"]:
        doc_type = "AMENDMENT"

    # 3. BID_TABULATION — bid comparison/award sheets
    elif findings["has_bid_tabulation"]:
        doc_type = "BID_TABULATION"

    # 4. PROPOSAL/QUOTE — scope + pricing but no signed agreement
    elif findings["has_scope"] and findings["has_dollar_amounts"] and not findings["has_whereas_pattern"]:
        doc_type = "PROPOSAL/QUOTE"

    # 5. SOFTWARE_RENEWAL — license/maintenance/subscription renewals
    elif findings["has_software_language"] and findings["has_renewal_language"]:
        doc_type = "SOFTWARE_RENEWAL"

    # 6. PO_FORM — AF-numbered approval forms (by filename or content)
    elif (findings["has_po_number"] or findings["has_af_form_markers"] or
          re.search(r'af\d{4,5}', fname_lower)):
        # AF forms detected by filename pattern (strongest signal)
        if re.search(r'af\d{4,5}', fname_lower) and page_count <= 2 and text_len < 3000:
            doc_type = "PO_FORM"
        elif findings["has_po_number"] and findings["has_account_code"]:
            doc_type = "PO_FORM"
        elif findings["has_af_form_markers"]:
            doc_type = "PO_FORM"
        else:
            doc_type = "PO_FORM"

    # 7. TUITION_CONTRACT — special ed / out-of-district tuition agreements
    elif findings["has_tuition_language"] and findings["has_dollar_amounts"]:
        doc_type = "TUITION_CONTRACT"

    # 8. RESOLUTION_COPY — board resolution text
    elif findings["has_board_resolution"] or findings["has_whereas_pattern"]:
        doc_type = "RESOLUTION_COPY"

    # 9. SCANNED_FORM — minimal text from a scanned document (likely AF form)
    elif text_len < 300 and page_count <= 2:
        doc_type = "SCANNED_FORM"
    elif is_only_watermark(text) and page_count >= 1:
        doc_type = "SCANNED_FORM"

    # 10. Fallback
    else:
        doc_type = "OTHER"

    return findings, doc_type


def get_all_meetings():
    resp = make_request(BASE_URL + "/BD-GetMeetingsList?open",
                        f"current_committee_id={COMMITTEE_ID}")
    return json.loads(resp.text)


def main():
    print("=" * 90)
    print("GMS DOCUMENT CONTENT ANALYZER")
    print("What's actually inside the attachments on JC BOE contract items?")
    print("=" * 90)
    print(f"Timestamp: {datetime.now().isoformat()}")

    if not HAS_PYMUPDF and not HAS_PDFMINER:
        print("\n⚠️  No PDF reader found. Install one:")
        print("   pip3 install PyMuPDF")
        print("   (or: pip3 install pdfminer.six)")
        print("   Then re-run this script.\n")
        sys.exit(1)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    all_meetings = get_all_meetings()

    # All meetings from Jan 2024 through present
    target_meetings = [
        m for m in all_meetings
        if m.get("numberdate") and str(m["numberdate"]) >= "20240101"
    ]
    target_meetings.sort(key=lambda m: str(m["numberdate"]))
    sample_meetings = target_meetings

    print(f"\nAnalyzing ALL {len(sample_meetings)} meetings from 2024-2026")
    print(f"PDF reader: {'PyMuPDF' if HAS_PYMUPDF else 'pdfminer'}\n")

    # Contract approval pattern
    contract_pattern = re.compile(
        r'(approve|authorize|award|ratif).{0,30}(contract|agreement|purchase order|professional .* service)',
        re.IGNORECASE
    )
    personnel_patterns = [
        re.compile(r'(transfer|promotion|appointment|separation|leave|resignation|retirement|degree status|salary adjust)', re.IGNORECASE),
    ]

    all_analyzed = []
    pdf_count = 0

    total_meetings = len(sample_meetings)
    for mi, m in enumerate(sample_meetings, 1):
        mdate = str(m["numberdate"])
        mname = m.get("name", "")
        print(f"\n{'─' * 90}")
        print(f"[{mi}/{total_meetings}] Meeting: {mdate} | {mname}")
        print(f"{'─' * 90}")

        resp = make_request(BASE_URL + "/PRINT-AgendaDetailed",
                           f"id={m['unique']}&current_committee_id={COMMITTEE_ID}")
        time.sleep(REQUEST_DELAY)

        if not resp or resp.status_code != 200:
            print("  FAILED to fetch")
            continue

        soup = BeautifulSoup(resp.content, "html.parser")

        # Parse items
        for item_div in soup.find_all("div", class_="item"):
            rightcol = item_div.find("div", class_="rightcol") or item_div
            itembody = rightcol.find("div", class_="itembody")
            text = itembody.get_text(separator=" ", strip=True) if itembody else rightcol.get_text(separator=" ", strip=True)

            # Only contract items
            if not contract_pattern.search(text):
                continue
            if any(p.search(text) for p in personnel_patterns):
                continue

            # Must have files
            file_divs = rightcol.find_all("div", class_="public-file")
            if not file_divs:
                continue

            # Get dollar amount
            amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', text)
            max_amount = 0
            for a in amounts:
                try:
                    val = float(a.replace('$', '').replace(',', ''))
                    max_amount = max(max_amount, val)
                except:
                    pass

            if max_amount < 10000:
                continue

            # Download and analyze each attached file
            for fd in file_divs:
                link = fd.find("a")
                if not link or not link.get("href"):
                    continue

                href = link["href"]
                file_label = link.get_text(strip=True)
                filename = unquote(href.split("/")[-1]) if "/" in href else file_label
                # Clean filename
                safe_name = re.sub(r'[^\w\-.]', '_', filename)[:80]
                safe_name = f"{mdate}_{safe_name}"

                print(f"\n  📎 Downloading: {file_label[:65]}")
                print(f"     Contract amount: ${max_amount:,.0f}")

                filepath, size = download_pdf(href, safe_name)
                time.sleep(0.5)

                if not filepath:
                    print(f"     ❌ Download failed")
                    continue

                pdf_count += 1
                print(f"     Size: {size:,} bytes")

                # Extract text
                pdf_text, page_count = extract_pdf_text(filepath)
                if page_count:
                    print(f"     Pages: {page_count}")

                if not pdf_text or pdf_text.startswith("["):
                    print(f"     ❌ Could not extract text: {pdf_text}")
                    continue

                print(f"     Text extracted: {len(pdf_text)} chars")

                # Analyze content
                findings, doc_type = analyze_pdf_content(pdf_text, filename=safe_name, page_count=page_count, file_size=size)
                print(f"     Document type: {doc_type}")

                present = [k.replace("has_", "") for k, v in findings.items() if v]
                absent = [k.replace("has_", "") for k, v in findings.items() if not v]
                print(f"     ✅ Contains: {', '.join(present)}")
                print(f"     ❌ Missing:  {', '.join(absent)}")

                # Show a preview
                preview = pdf_text[:500].replace("\n", " | ").strip()
                print(f"     Preview: {preview[:300]}...")

                all_analyzed.append({
                    "meeting_date": mdate,
                    "contract_amount": max_amount,
                    "file_label": file_label,
                    "file_size": size,
                    "page_count": page_count,
                    "doc_type": doc_type,
                    "findings": findings,
                    "text_length": len(pdf_text),
                    "resolution_preview": text[:200],
                })

    # ─── Summary Report ──────────────────────────────────────────
    print(f"\n\n{'=' * 90}")
    print("DOCUMENT CONTENT ANALYSIS SUMMARY")
    print(f"{'=' * 90}")
    print(f"\nPDFs downloaded and analyzed: {len(all_analyzed)}")

    # By document type
    type_counts = {}
    for a in all_analyzed:
        t = a["doc_type"]
        if t not in type_counts:
            type_counts[t] = {"count": 0, "total_contract_value": 0}
        type_counts[t]["count"] += 1
        type_counts[t]["total_contract_value"] += a["contract_amount"]

    print(f"\n  {'Document Type':<20s} {'Count':>6s}  {'Contract $ Covered':>20s}")
    print(f"  {'─'*20} {'─'*6}  {'─'*20}")
    for t in sorted(type_counts, key=lambda x: type_counts[x]["count"], reverse=True):
        info = type_counts[t]
        print(f"  {t:<20s} {info['count']:>6d}  ${info['total_contract_value']:>18,.0f}")

    # What elements are typically present vs absent
    print(f"\n{'─' * 90}")
    print("HOW OFTEN DOES EACH ELEMENT APPEAR IN ATTACHMENTS?")
    print(f"{'─' * 90}")

    element_counts = {}
    for a in all_analyzed:
        for k, v in a["findings"].items():
            label = k.replace("has_", "")
            if label not in element_counts:
                element_counts[label] = {"present": 0, "absent": 0}
            if v:
                element_counts[label]["present"] += 1
            else:
                element_counts[label]["absent"] += 1

    total = len(all_analyzed) if all_analyzed else 1
    print(f"\n  {'Element':<30s} {'Present':>8s} {'Absent':>8s} {'Rate':>7s}")
    print(f"  {'─'*30} {'─'*8} {'─'*8} {'─'*7}")
    for elem in sorted(element_counts, key=lambda x: element_counts[x]["present"], reverse=True):
        info = element_counts[elem]
        rate = info["present"] / total * 100
        print(f"  {elem:<30s} {info['present']:>8d} {info['absent']:>8d} {rate:>6.1f}%")

    # Key finding
    print(f"\n{'─' * 90}")
    print("KEY FINDING")
    print(f"{'─' * 90}")
    actual_contracts = [a for a in all_analyzed if a["doc_type"] == "ACTUAL_CONTRACT"]
    po_forms = [a for a in all_analyzed if a["doc_type"] == "PO_FORM"]
    proposals = [a for a in all_analyzed if a["doc_type"] == "PROPOSAL/QUOTE"]

    print(f"\n  Of {len(all_analyzed)} PDFs analyzed:")
    print(f"    {len(actual_contracts)} are actual contracts (with terms, scope, signatures)")
    print(f"    {len(proposals)} are proposals/quotes (scope + pricing but no signed agreement)")
    print(f"    {len(po_forms)} are PO forms (internal spending authorization only)")
    print(f"    {len(all_analyzed) - len(actual_contracts) - len(proposals) - len(po_forms)} are other/unclassified")

    if po_forms:
        print(f"\n  Typical PO form contains:")
        po_elements = {}
        for po in po_forms:
            for k, v in po["findings"].items():
                label = k.replace("has_", "")
                if label not in po_elements:
                    po_elements[label] = 0
                if v:
                    po_elements[label] += 1
        for elem in sorted(po_elements, key=lambda x: po_elements[x], reverse=True):
            pct = po_elements[elem] / len(po_forms) * 100
            marker = "✅" if pct > 50 else "❌"
            print(f"    {marker} {elem}: {pct:.0f}%")

    # Export
    csv_file = "jcboe_pdf_analysis.csv"
    finding_keys = [
        "signatures", "terms", "scope", "dollar_amounts", "dates",
        "vendor_info", "insurance_requirements", "termination_clause",
        "payment_terms", "legal_boilerplate", "po_number", "account_code",
        "board_resolution", "bid_tabulation", "renewal_language",
        "amendment_language", "whereas_pattern", "af_form_markers",
        "software_language", "tuition_language",
    ]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["meeting_date", "contract_amount", "file_label", "file_size",
                         "page_count", "doc_type", "text_length",
                         *[f"has_{k}" for k in finding_keys],
                         "resolution_preview"])
        for a in all_analyzed:
            writer.writerow([
                a["meeting_date"], a["contract_amount"], a["file_label"],
                a["file_size"], a["page_count"], a["doc_type"], a["text_length"],
                *[a["findings"].get(f"has_{x}", False) for x in finding_keys],
                a["resolution_preview"],
            ])
    print(f"\nCSV exported: {csv_file}")
    print(f"PDFs saved to: {DOWNLOAD_DIR}/")


if __name__ == "__main__":
    main()
