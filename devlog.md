# GMS-JCBOE Development Log

## 2026-04-06 — Project bootstrap and Phases 0-3

### Completed prior to this session
- **Phase 0**: Mapped BoardDocs API endpoints, tested rate limits
- **Phase 1**: Identified 2,155 contract agenda items across all available meetings
- **Phase 2**: Deep dive on 352 contract items — extracted dollar amounts, file counts, vendor names. Three sub-investigations: budget doc availability, contract source docs, retroactive documentation tracking
- **Phase 3**: Downloaded and analyzed 60 PDFs from 5 sample meetings covering $133M in contracts

### Phase 3 key finding
Of 60 PDFs analyzed:
- 0 actual signed contracts (with terms, scope, and signatures)
- 4 proposals/quotes
- 2 resolution copies
- 54 classified as "OTHER"

The "OTHER" bucket is too large — many are really resolution-only text or scanned AF (approval form) documents that the regex patterns don't catch.

### Current session: Improve classification + expand to all 2024-2026 meetings
- Goal: Reduce "OTHER" with better classification patterns
- Goal: Run analysis on ALL meetings from Jan 2024 through present, not just 5 samples
- New doc categories being added: BID_TABULATION, SOFTWARE_RENEWAL, AMENDMENT, SCANNED_FORM
- Better detection of resolution text (WHEREAS pattern), AF forms (filename-based), and renewals

### PDF Analyzer Results (full run, all 2024-2026 meetings)
- 362 PDFs downloaded and analyzed (up from 60 in sample)
- "OTHER" category reduced from 54/60 (90%) to 3/362 (0.8%)
- Classification breakdown:
  - 262 PO Forms ($198.8M)
  - 39 Proposals/Quotes ($37.2M)
  - 20 Actual Contracts ($7.2M) — only 5.5% of docs
  - 17 Amendments ($127.1M)
  - 12 Software Renewals ($72.8M)
  - 9 Bid Tabulations ($33.7M)
  - 3 Other ($9.8M)

### Methodology gap identified: meeting coverage
- Phase 2 only analyzed 24 regular meetings
- JCBOE had 42 total meetings since Jan 2024 (12 special + 6 other)
- Special meetings can include contract votes — need to expand coverage

### Dashboard v1 built
- Self-contained HTML with embedded data, GMS/OCC Research branding
- 6 panels: timeline, doc types, undocumented table, vendor tracker, amendments, dollar exposure
- Citizen-friendly language with glossary for non-technical audiences
