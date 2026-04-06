# GMS-JCBOE Development Log

## 2026-04-06 — Full build: Phases 0-4

### Phase 0: Recon
- Mapped BoardDocs API endpoints for JCBOE (`go.boarddocs.com/nj/jcps/Board.nsf`)
- Tested rate limits — 1.5s delay is safe
- Committee ID: `A9QM9A5A1F6C`

### Phase 1: Transparency gap analysis
- Identified 2,155 contract agenda items across all available meetings
- Built filtering to exclude personnel/HR items
- Exported to CSV for analysis

### Phase 2: Contract source document check
- Deep dive on contract items — extracted dollar amounts, file counts, vendor names
- Three sub-investigations: budget doc availability, contract source docs, retroactive tracking
- Initially covered 24 regular meetings, later expanded to all 42 meetings (regular + special + reorganization)
- Found that special meetings and reorganization meetings also approve contracts (3 reorg meetings each had 1 contract with 100% gap rate)

### Phase 3: PDF content analysis
- Initial run: 60 PDFs from 5 sample meetings, 54/60 classified as "OTHER" — classifier too weak
- Improved classifier with 7 categories + 20 content signals (up from 13)
- Added filename-based detection (AF##### pattern for PO forms)
- Added categories: BID_TABULATION, SOFTWARE_RENEWAL, AMENDMENT, SCANNED_FORM
- Full run across all 42 meetings: **362 PDFs analyzed**
  - 262 PO Forms ($198.8M) — 72%
  - 39 Proposals/Quotes ($37.2M) — 11%
  - 20 Actual Contracts ($7.2M) — 5.5%
  - 17 Amendments ($127.1M) — 4.7%
  - 12 Software Renewals ($72.8M) — 3.3%
  - 9 Bid Tabulations ($33.7M) — 2.5%
  - 3 Other ($9.8M) — 0.8%

### Phase 4: Dashboard + vendor resolution

#### Vendor name extraction (18% -> 92%)
- **Pass 1 (18%)**: Original regex in `jcboe_deep_dive_v3.py` — single pattern matching "contract with/to [Vendor]"
- **Pass 2 (43%)**: Added 8 vendor extraction patterns — "WHEREAS, [X] was awarded", "[X] has offered to renew", "[X] provides", "[X] located at", etc.
- **Pass 3 (63%)**: Deep extraction using full resolution text (not truncated), PD# cross-referencing against original meeting agendas, employment contract detection
- **Pass 4 (89%)**: OCR'd 107 attached PO form PDFs to extract vendor names from scanned documents
- **Pass 5 (92%)**: Manual vendor fixes for bad OCR extractions, vendor name normalization (merged duplicates like "Sal Electric" / "Sal Electric Co." / "Sal Electric Co., Inc.")
- Final: **345/374 vendors identified** (92%)

#### Vendor normalization
- Reduced from 112 to 97 unique vendor names by merging duplicates
- Key merges: "Center of/for Supportive Schools" (typo), "NW Transport/Transportation", "Sal Electric" variants, "Pennetta Automation/Industrial Automation"
- Normalization applied via lookup table in data generation

#### Bid tabulation analysis
- OCR'd 9 bid tabulation PDFs to extract competing vendor names and bid amounts
- Found GL Group bidding $3.9M against Pennetta's winning $2.07M bid on cooling units
- IAQ upgrades: Riggs Distler, AMCO, Unitemp competing for $27.7M across 4 high schools
- Walk-in box replacement: Drill Construction lowest at $620K vs $1.1M third bidder

#### Cross-referencing resolution references
- Fetched original meeting agendas for June 27, 2024 and December 11, 2025 to resolve vendor names from amendment items that reference prior resolutions
- Limited success (5 resolved) — most original resolutions also use generic "lowest bidder" language without naming vendors in text

#### Dashboard
- Self-contained HTML with all data embedded as JS variable (no server needed)
- GMS / OCC Research branding (navy #0B1628, Rajdhani + DM Sans + Instrument Serif fonts)
- 6 panels:
  1. **Meeting Timeline** — gap rate heatmap with special/reorg meeting badges
  2. **Document Type Breakdown** — 7-color bar chart with legend (PO Forms, Contracts, Proposals, Amendments, Bids, SW Renewals, No Docs)
  3. **Largest Undocumented Contracts** — sortable table with plain-English summaries
  4. **Vendor Documentation Tracker** — cards with hover tooltips showing specific gap dates/amounts
  5. **Renewals & Amendments** — chain tracking with resolution references
  6. **Dollar Exposure** — total documented vs undocumented value
- Citizen-friendly features:
  - "What is this?" guide banner
  - Interactive glossary defining: Contract, Resolution, PO Form, Source Document, Documentation Gap, Amendment, NTE, OPRA, BoardDocs, Vendor, Renewal, Bid Tabulation
  - Plain-English summaries for all 51 undocumented items (hand-written, not regex-stripped)
  - "What This Means" / "Why This Matters" callouts on each finding

#### OPRAMachine integration (partial)
- Built Playwright-based scraper (`jcboe_opramachine.py`) with Cloudflare bypass (headed browser + stealth)
- Cloudflare still blocking automated access — script opens visible browser for manual CAPTCHA solving
- OPRAMachine has a JSON API but it's also behind Cloudflare
- Found existing OPRA requests via web search: contract requests for NCASA, AFSCME, attorney/health broker contracts

### Methodology gaps identified
1. **Vendor extraction ceiling at 92%** — remaining 29 unknowns are generic bid awards ("lowest bidder") or multi-vendor route awards where names are only in attached spreadsheets
2. **PO-to-contract linkage** — 330 PO forms reference contract numbers but we don't verify those contracts exist publicly
3. **Amendment chain tracking** — 32% of items reference prior resolutions but we can't always trace the original contract's documentation status
4. **No content analysis of "documented" items** — an item having an attachment doesn't mean the attachment is the actual contract (most are PO forms)
5. **Meeting minutes not analyzed** — votes, discussion, and dissent are in minutes, not agendas

### Key findings summary
| Metric | Value |
|--------|-------|
| Meetings scanned | 42 (Jan 2024 - Mar 2026) |
| Contract items tracked | 374 |
| Total contract value | $402.6M |
| Items with zero documentation | 51 ($28.9M) |
| PDFs analyzed | 362 |
| Actual signed contracts found | 20 ($7.2M) |
| PO forms (not contracts) | 262 ($198.8M) |
| Vendor identification rate | 92% (345/374) |
| Worst meeting (gap rate) | Sep 25, 2024 — 100% gap (5/5 items) |
