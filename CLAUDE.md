# GMS-JCBOE — Jersey City Board of Education Transparency Investigation

## Project Purpose
Investigating public transparency gaps in Jersey City Board of Education (JCBOE) contract approvals via BoardDocs. The core finding: the board approves tens of millions in contracts but rarely attaches the actual signed agreements — the public sees only resolution paragraphs and internal PO forms.

## Architecture
- **jcboe_recon.py** — Phase 0: BoardDocs API endpoint mapping and rate limit testing
- **jcboe_transparency_gap.py / _v2.py** — Phase 1: Identify contract agenda items with missing docs
- **jcboe_deep_dive_v3.py** — Phase 2: Three investigations (budget docs, contract source docs, retroactive tracking)
- **jcboe_doc_analyzer.py** — Phase 3: Download and classify actual PDF content with OCR support
- **pdf_samples/** — Downloaded PDFs (gitignored)
- **devlog.md** — Running development log

## Key Data
- BoardDocs site: `go.boarddocs.com/nj/jcps/Board.nsf`
- Committee ID: `A9QM9A5A1F6C`
- API delay: 1.5s between requests (rate limit safe)
- Contract items identified by regex: `(approve|authorize|award|ratif).{0,30}(contract|agreement|purchase order|professional .* service)`
- Personnel items excluded via separate patterns

## Conventions
- Python 3, use requests + BeautifulSoup for scraping
- CSV output for all data exports
- PDF extraction: PyMuPDF (fitz) primary, pdfminer fallback, tesseract OCR for scanned docs
- All scripts are standalone and runnable independently
- Print progress to stdout during long runs
- Dollar threshold: $10K minimum for contract items

## Document Classification Categories
- ACTUAL_CONTRACT — has terms, scope, and signatures/legal boilerplate
- PROPOSAL/QUOTE — has scope + dollar amounts but no signed agreement
- PO_FORM — internal purchase order (AF-numbered forms with account codes)
- RESOLUTION_COPY — board resolution text (WHEREAS... BE IT RESOLVED)
- BID_TABULATION — bid comparison sheets from procurement
- SOFTWARE_RENEWAL — license/maintenance renewal notices
- AMENDMENT — contract amendments or change orders
- SCANNED_FORM — scanned single-page AF/PO with minimal extractable text
- OTHER — unclassified

## Running
```bash
pip install -r requirements.txt
# Optional for OCR: pip install PyMuPDF pytesseract Pillow
# Optional: brew install tesseract

python3 jcboe_doc_analyzer.py   # Phase 3 — PDF analysis
python3 jcboe_deep_dive_v3.py   # Phase 2 — contract source doc check
```
