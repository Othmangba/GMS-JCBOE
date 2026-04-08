# GMS-JCBOE — Jersey City Board of Education Contract Transparency Monitor

## Project Purpose
A Governance Memory System (GMS) investigation by [OCC Research](https://occresearch.org) tracking public transparency gaps in Jersey City Board of Education contract approvals via BoardDocs. The core finding: the Board approves hundreds of millions in contracts but rarely attaches the actual signed agreements — the public sees only resolution paragraphs and internal PO forms.

## Architecture

### Data Collection Scripts
- **jcboe_recon.py** — Phase 0: BoardDocs API endpoint mapping and rate limit testing
- **jcboe_transparency_gap.py / _v2.py** — Phase 1: Identify contract agenda items with missing docs
- **jcboe_deep_dive_v3.py** — Phase 2: Contract source doc check, budget doc check, retroactive tracking. Covers all 42 meetings (regular, special, reorganization) from Jan 2024 onward. Includes vendor name extraction with 8+ regex patterns.
- **jcboe_doc_analyzer.py** — Phase 3: Download and classify actual PDF content with OCR support. 7-category classifier (ACTUAL_CONTRACT, PROPOSAL/QUOTE, PO_FORM, AMENDMENT, BID_TABULATION, SOFTWARE_RENEWAL, OTHER).
- **jcboe_vendor_ocr.py** — Phase 4: OCR attached PO forms to extract vendor names from scanned documents when the resolution text doesn't name the vendor.
- **jcboe_opramachine.py** — Playwright-based scraper for OPRAMachine (Cloudflare-protected). Uses headed browser with stealth mode.

### Data Files
- **jcboe_contract_source_docs.csv** — All 374 contract items with vendor, amount, doc status, resolution text
- **jcboe_pdf_analysis.csv** — 362 PDFs classified by document type with content analysis flags
- **jcboe_bid_tabulations.csv** — OCR'd bid tabulation sheets with competing vendor names and bid amounts
- **dashboard_data.json** — Aggregated data for the dashboard (meetings, vendors, amendments, undocumented items)
- **undoc_summaries.json** — Hand-written plain-English summaries for all 51 undocumented contract items
- **jcboe_filtered_gaps.csv** — Phase 1 raw transparency gap data (2,155 items)
- **jcboe_transparency_gaps.csv** — Phase 1 full gap analysis

### Dashboard
- **dashboard.html** — Self-contained single-page dashboard with all data embedded inline. No server required — open directly in a browser. GMS/OCC Research branding, citizen-friendly language, interactive glossary.

### Other
- **pdf_samples/** — Downloaded PDFs (gitignored, ~400 files)
- **devlog.md** — Running development log
- **requirements.txt** — Python dependencies

## Key Data Points
- BoardDocs site: `go.boarddocs.com/nj/jcps/Board.nsf`
- Committee ID: `A9QM9A5A1F6C`
- API delay: 1.5s between requests (rate limit safe)
- Date range: Jan 2024 — Mar 2026 (42 meetings scanned, 29 had contract items)
- Contract detection regex: `(approve|authorize|award|ratif).{0,30}(contract|agreement|purchase order|professional .* service)`
- Personnel items excluded via separate patterns
- Dollar threshold: $10K minimum for contract items

## Current Findings (as of 2026-04-08)
- **374 board actions** tracked across 29 meetings — **367 unique spending commitments** after removing 7 re-votes (Feb 29 → Mar 19, 2024)
- Total unique value: **$389.7M** (not $402.6M — the difference is the re-voted items)
- **50 unique items ($21.6M)** have zero documentation attached
- **362 PDFs** analyzed: only **20 are actual contracts** ($7.2M), **262 are PO forms**
- **92% vendor identification** (345/374) via text extraction, PD# cross-reference, and OCR
- FY2024 audit: **19 findings**. FY2025 audit: **13 findings**. **10 repeat** across both years.
- Key undocumented contracts: Pennetta ($7.26M boiler replacements), Edmentum ($2.13M tutoring), Hewlett Packard ($1.03M x2 software), Sal Electric ($800K)
- HVAC/Mechanical is merged into **Facilities & Maintenance** (not a separate category)

## Document Classification Categories
- **ACTUAL_CONTRACT** — has terms, scope, and signatures/legal boilerplate
- **PROPOSAL/QUOTE** — has scope + dollar amounts but no signed agreement
- **PO_FORM** — internal purchase order (AF-numbered forms with account codes)
- **AMENDMENT** — contract amendments or change orders
- **BID_TABULATION** — bid comparison sheets from procurement
- **SOFTWARE_RENEWAL** — license/maintenance renewal notices
- **OTHER** — unclassified (only 3 of 362 PDFs)

## Fact-Check Rules (MANDATORY)

**Before committing ANY number to FINDINGS_REPORT.md or the website report page:**
1. **Verify against source data.** Every number must be traceable to a specific CSV query or PDF page. Do not rely on memory from previous sessions.
2. **Run `python3 verify_report.py`** before every commit that touches the report. It validates 31 key numbers against the CSV data. Do not push if it fails.
3. **Read the full source PDF.** When referencing audit findings, read ALL pages of the audit PDF — not just the first few. The FY2024 audit has 19 findings across 12 pages, not 16.
4. **Check for duplicates.** 7 items from Feb 29, 2024 were re-voted at Mar 19, 2024 with identical text. Use deduplicated figures ($389.7M / 367 items / 50 undocumented) for dollar calculations. Use 374 for gap rates and item counts.
5. **Check the dashboard categorization function.** The dashboard has its own `categorize()` function in the HTML. Any category changes in the report must also be reflected there. HVAC is merged into Facilities & Maintenance.
6. **Cross-check across all files.** When a number changes, it must be updated in: FINDINGS_REPORT.md, the website page (page.tsx), the homepage deployment card (page.tsx), and the dashboard (gms-jcboe-dashboard.html).

## Conventions
- Python 3.9+, use requests + BeautifulSoup for scraping
- CSV output for all data exports
- PDF extraction: PyMuPDF (fitz) primary, pdfminer fallback, tesseract OCR for scanned docs
- All scripts are standalone and runnable independently
- Print progress to stdout during long runs
- Dashboard is self-contained HTML — data embedded as JS variable, no server needed
- All public-facing text uses plain English accessible to general citizens
- Vendor names are normalized to merge duplicates (typos, abbreviations, address suffixes)

## Running
```bash
pip install -r requirements.txt
pip install PyMuPDF pytesseract Pillow  # For PDF/OCR
pip install playwright && playwright install chromium  # For OPRAMachine
brew install tesseract  # macOS OCR engine

# Phase 2 — Contract source doc check (all 42 meetings)
python3 jcboe_deep_dive_v3.py

# Phase 3 — PDF content analysis (downloads and classifies all contract PDFs)
python3 jcboe_doc_analyzer.py

# Phase 4 — OCR PO forms for missing vendor names
python3 jcboe_vendor_ocr.py

# OPRAMachine scraper (opens a browser window — may need manual CAPTCHA)
python3 jcboe_opramachine.py

# Dashboard — just open in a browser
open dashboard.html

# Fact-check the report against source data (run before every commit)
python3 verify_report.py
```
