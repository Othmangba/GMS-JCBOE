#!/usr/bin/env python3
"""
GMS Phase 5 — Meeting Minutes Scraper & Analyzer
==================================================
Downloads meeting minutes PDFs from BoardDocs and scans them for:
  - Mentions of specific vendors (Pennetta, Edmentum, HP, etc.)
  - Discussion about missing documentation
  - Vote breakdowns on contract items
  - Public comment about transparency
  - Staff explanations about contracts

Usage:
    python3 jcboe_minutes_scraper.py

Output:
    - pdf_samples/minutes/ — downloaded minutes PDFs
    - jcboe_minutes_analysis.csv — extracted mentions and context
"""

import csv
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime

import requests
from bs4 import BeautifulSoup

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF not installed. Run: pip install PyMuPDF")
    sys.exit(1)

# ─── Configuration ───────────────────────────────────────────────
SITE = "nj/jcps/Board.nsf"
BASE_URL = f"https://go.boarddocs.com/{SITE}"
COMMITTEE_ID = "A9QM9A5A1F6C"
REQUEST_DELAY = 1.5
MINUTES_DIR = "pdf_samples/minutes"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    "referer": f"https://go.boarddocs.com/{SITE}/Public",
    "origin": "https://go.boarddocs.com",
}

# Vendors and keywords to search for in minutes
WATCH_VENDORS = [
    "pennetta", "edmentum", "hewlett packard", "hp inc",
    "adams lattiboudere", "machado law", "sal electric",
    "strulowitz", "guarini", "cdw",
]

WATCH_KEYWORDS = [
    # Documentation gaps
    r"missing.*document", r"document.*missing", r"where.*contract",
    r"no.*contract.*attach", r"contract.*not.*provided",
    r"documentation.*not", r"unable.*provide",
    # Transparency
    r"transparency", r"public.*access", r"opra",
    # Audit
    r"audit.*finding", r"corrective.*action", r"auditor",
    r"lerch.*vinci", r"management.*report",
    # Financial concerns
    r"surplus", r"excess.*surplus", r"tax.*increase", r"tax.*levy",
    r"capital.*reserve",
    # Procurement
    r"procurement.*portal", r"opengov", r"bid.*threshold",
    r"state.*comptroller",
    # Votes
    r"voted?\s+\d+-\d+", r"roll\s+call", r"nay", r"dissent",
    # Public comment
    r"public.*comment", r"public.*speak", r"resident.*ask",
]


def get_meetings():
    """Fetch all meetings from BoardDocs."""
    url = BASE_URL + "/BD-GetMeetingsList?open"
    data = f"current_committee_id={COMMITTEE_ID}"
    resp = requests.post(url, headers=HEADERS, data=data, timeout=30)
    return json.loads(resp.text)


def get_agenda_html(meeting_id):
    """Get the full detailed agenda HTML for a meeting."""
    url = BASE_URL + "/PRINT-AgendaDetailed?open"
    data = f"id={meeting_id}&current_committee_id={COMMITTEE_ID}"
    resp = requests.post(url, headers=HEADERS, data=data, timeout=60)
    return resp.text


def find_minutes_pdfs(agenda_html, meeting_id):
    """Extract minutes PDF links from the agenda HTML."""
    soup = BeautifulSoup(agenda_html, "html.parser")
    minutes_pdfs = []

    # Find all links that look like minutes PDFs
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text().lower()

        if "minute" in text and href.endswith(".pdf"):
            # Build full URL if relative
            if not href.startswith("http"):
                href = BASE_URL + "/" + href.lstrip("/")
            minutes_pdfs.append({
                "url": href,
                "label": link.get_text().strip(),
                "meeting_id": meeting_id,
            })

    # Also check for file attachment links in the minutes section
    for link in soup.find_all("a"):
        href = link.get("href", "")
        text = link.get_text().strip()
        if ".pdf" in href.lower() and "minute" in text.lower():
            if not href.startswith("http"):
                href = BASE_URL + "/" + href.lstrip("/")
            # Avoid duplicates
            urls_so_far = {p["url"] for p in minutes_pdfs}
            if href not in urls_so_far:
                minutes_pdfs.append({
                    "url": href,
                    "label": text,
                    "meeting_id": meeting_id,
                })

    return minutes_pdfs


def download_pdf(url, filepath):
    """Download a PDF file."""
    try:
        resp = requests.get(url, headers={
            "referer": f"https://go.boarddocs.com/{SITE}/Public",
        }, timeout=60)
        if resp.status_code == 200 and len(resp.content) > 100:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"    Download error: {e}")
    return False


def extract_text_from_pdf(filepath):
    """Extract text from a PDF using PyMuPDF."""
    try:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"    PDF extraction error: {e}")
        return ""


def analyze_minutes_text(text, meeting_date, meeting_name, pdf_label):
    """Search minutes text for vendors, keywords, and patterns of interest."""
    findings = []
    text_lower = text.lower()

    # Search for vendor mentions
    for vendor in WATCH_VENDORS:
        if vendor in text_lower:
            # Get context around each mention
            for match in re.finditer(re.escape(vendor), text_lower):
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end].replace("\n", " ").strip()
                findings.append({
                    "meeting_date": meeting_date,
                    "meeting_name": meeting_name,
                    "pdf_label": pdf_label,
                    "type": "VENDOR_MENTION",
                    "match": vendor,
                    "context": context,
                })

    # Search for keywords
    for pattern in WATCH_KEYWORDS:
        for match in re.finditer(pattern, text_lower):
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 200)
            context = text[start:end].replace("\n", " ").strip()
            findings.append({
                "meeting_date": meeting_date,
                "meeting_name": meeting_name,
                "pdf_label": pdf_label,
                "type": "KEYWORD_MATCH",
                "match": match.group(),
                "context": context,
            })

    return findings


def main():
    os.makedirs(MINUTES_DIR, exist_ok=True)

    print("=" * 70)
    print("GMS PHASE 5: Meeting Minutes Scraper & Analyzer")
    print("=" * 70)

    # Step 1: Get all meetings
    print("\n[1/4] Fetching meeting list...")
    meetings = get_meetings()
    print(f"  Found {len(meetings)} meetings")

    # Step 2: Scan each meeting's agenda for minutes PDFs
    print("\n[2/4] Scanning agendas for minutes PDFs...")
    all_minutes = []

    for i, meeting in enumerate(meetings):
        name = meeting.get("name", "Unknown")
        mid = meeting["unique"]
        print(f"  [{i+1}/{len(meetings)}] {name}...", end=" ", flush=True)

        time.sleep(REQUEST_DELAY)
        try:
            agenda_html = get_agenda_html(mid)
            pdfs = find_minutes_pdfs(agenda_html, mid)
            print(f"{len(pdfs)} minutes PDF(s)")
            for pdf in pdfs:
                pdf["meeting_name"] = name
                # Extract date from the PDF label or meeting name
                pdf["meeting_date"] = meeting.get("numberdate", "")
            all_minutes.extend(pdfs)
        except Exception as e:
            print(f"error: {e}")

    print(f"\n  Total minutes PDFs found: {len(all_minutes)}")

    # Step 3: Download and extract text
    print("\n[3/4] Downloading and extracting text...")
    all_findings = []

    for i, pdf_info in enumerate(all_minutes):
        label = pdf_info["label"]
        url = pdf_info["url"]
        meeting_name = pdf_info.get("meeting_name", "")
        meeting_date = pdf_info.get("meeting_date", "")

        # Create safe filename
        safe_label = re.sub(r'[^\w\s.-]', '', label)[:80]
        filepath = os.path.join(MINUTES_DIR, f"{meeting_date}_{safe_label}.pdf")

        print(f"  [{i+1}/{len(all_minutes)}] {label[:60]}...", end=" ", flush=True)

        if os.path.exists(filepath):
            print("(cached)", end=" ")
        else:
            time.sleep(REQUEST_DELAY)
            if not download_pdf(url, filepath):
                print("FAILED")
                continue

        # Extract and analyze
        text = extract_text_from_pdf(filepath)
        if text:
            findings = analyze_minutes_text(text, meeting_date, meeting_name, label)
            all_findings.extend(findings)
            vendor_hits = sum(1 for f in findings if f["type"] == "VENDOR_MENTION")
            keyword_hits = sum(1 for f in findings if f["type"] == "KEYWORD_MATCH")
            print(f"{vendor_hits} vendor mentions, {keyword_hits} keyword matches")
        else:
            print("no text extracted")

    # Step 4: Write results
    print(f"\n[4/4] Writing results...")
    output_file = "jcboe_minutes_analysis.csv"

    if all_findings:
        fieldnames = ["meeting_date", "meeting_name", "pdf_label", "type", "match", "context"]
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_findings)
        print(f"  Wrote {len(all_findings)} findings to {output_file}")
    else:
        print("  No findings to write")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Meetings scanned: {len(meetings)}")
    print(f"Minutes PDFs found: {len(all_minutes)}")
    print(f"Total findings: {len(all_findings)}")

    if all_findings:
        type_counts = defaultdict(int)
        match_counts = defaultdict(int)
        for f in all_findings:
            type_counts[f["type"]] += 1
            match_counts[f["match"]] += 1

        print(f"\nBy type:")
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")

        print(f"\nTop matches:")
        for m, c in sorted(match_counts.items(), key=lambda x: -x[1])[:20]:
            print(f"  {m}: {c}")


if __name__ == "__main__":
    main()
