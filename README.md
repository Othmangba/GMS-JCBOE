# GMS-JCBOE

**Governance Memory System — Jersey City Board of Education Contract Transparency Monitor**

An [OCC Research](https://occresearch.org) investigation tracking whether the Jersey City Board of Education provides the public with actual contract documents when approving spending.

## The Problem

When the Board of Education votes to approve a contract, residents should be able to see the full agreement — what work is being done, how much it costs, and who signed off. This project systematically checks whether that information is actually available through [BoardDocs](https://go.boarddocs.com/nj/jcps/Board.nsf/Public), the Board's official document portal.

## Key Findings

| Metric | Value |
|--------|-------|
| Meetings analyzed | 42 (Jan 2024 — Mar 2026) |
| Board actions tracked | 376 (368 unique commitments after deduplicating re-votes) |
| Total contract value | $430.4M (deduplicated, after Scenario C) |
| Items with zero documents attached (raw) | 49 ($18.5M) |
| **Genuine undocumented vendor spending** (excludes 1 rescission, 1 grant application, 1 policy threshold, and 10 amendments absorbed within documented parent NTE) | **36 items ($14.48M)** |
| PDFs analyzed | 364 |
| **Actual signed contracts found** | **20 out of 364 PDFs** |
| PO forms (internal forms, not contracts) | 262 ($198.8M) |

**The bottom line:** When the Board says it "approved a contract," the actual signed agreement is almost never publicly available. What gets attached instead is an internal purchase order form — a document the district uses to authorize its own spending, not the agreement with the vendor.

## Dashboard

The interactive dashboard lives at [occresearch.org/gms-jcboe-dashboard.html](https://occresearch.org/gms-jcboe-dashboard.html).

It includes:
- Meeting-by-meeting documentation gap timeline
- Document type breakdown (what's actually attached vs. what should be)
- Largest undocumented contracts with plain-English descriptions
- Vendor documentation tracker with gap details on hover
- Amendment and renewal chain tracking
- Interactive glossary explaining all terms for non-technical audiences

## How It Works

1. **Data collection** — Scripts query the BoardDocs API to pull every contract-related agenda item from Jan 2024 onward
2. **Document download** — Each attached PDF is downloaded and stored locally
3. **Content classification** — PDFs are analyzed via text extraction and OCR to determine what type of document they actually are (contract? PO form? bid sheet? proposal?)
4. **Vendor extraction** — Vendor names are pulled from resolution text, cross-referenced via PD numbers, and OCR'd from PO forms when not found in text
5. **Gap analysis** — Items are flagged when the Board approves spending but doesn't attach the underlying agreement

## Setup

```bash
pip install -r requirements.txt
brew install tesseract          # macOS — for OCR of scanned PDFs
playwright install chromium     # For OPRAMachine scraper only
```

## Scripts

| Script | Purpose |
|--------|---------|
| `jcboe_deep_dive_v3.py` | Contract source document check across all meetings |
| `jcboe_doc_analyzer.py` | Download and classify PDF attachments |
| `jcboe_vendor_ocr.py` | OCR PO forms to extract missing vendor names |
| `jcboe_opramachine.py` | Scrape OPRA request history from OPRAMachine |
| `jcboe_recon.py` | BoardDocs API endpoint mapping |
| `jcboe_transparency_gap.py` | Initial gap identification |

## Data Files

| File | Description |
|------|-------------|
| `jcboe_contract_source_docs.csv` | 374 contract items with vendor, amount, documentation status |
| `jcboe_pdf_analysis.csv` | 362 PDFs with document type classification |
| `jcboe_bid_tabulations.csv` | OCR'd bid sheets with competing vendors and amounts |
| `undoc_summaries.json` | Plain-English summaries of undocumented items (49 unique after dedup) |

## What You Can Do

- **Browse the dashboard** to understand the scope of the problem
- **File OPRA requests** for specific contracts that should be public
- **Share the findings** with your community, local journalists, or elected officials
- **Run the scripts** to update the data as new meetings occur

## About

Built by [OCC Research](https://occresearch.org) — independent governance infrastructure consultancy specializing in institutional memory systems. *Governance that remembers.*

---

*Data sourced entirely from public records available on BoardDocs. No private or restricted information was accessed.*
