#!/usr/bin/env python3
"""
FINDINGS_REPORT.md Fact-Checker
================================
Validates every key number in the report against the source CSV data.
Run before any commit that touches FINDINGS_REPORT.md.

Usage:
    python3 verify_report.py

Exit code 0 = all checks pass
Exit code 1 = one or more checks failed
"""

import csv
import re
import sys

REPORT_PATH = "FINDINGS_REPORT.md"
CONTRACT_CSV = "jcboe_contract_source_docs.csv"
PDF_CSV = "jcboe_pdf_analysis.csv"

passed = 0
failed = 0
warnings = 0


def check(description, expected, actual, tolerance=0):
    global passed, failed
    if isinstance(expected, float) and isinstance(actual, float):
        if abs(expected - actual) <= tolerance:
            print(f"  PASS  {description}: {actual}")
            passed += 1
            return
    elif expected == actual:
        print(f"  PASS  {description}: {actual}")
        passed += 1
        return
    print(f"  FAIL  {description}: expected {expected}, got {actual}")
    failed += 1


def warn(description, detail):
    global warnings
    print(f"  WARN  {description}: {detail}")
    warnings += 1


def load_contracts():
    with open(CONTRACT_CSV) as f:
        return list(csv.DictReader(f))


def load_pdfs():
    with open(PDF_CSV) as f:
        return list(csv.DictReader(f))


def load_report():
    with open(REPORT_PATH) as f:
        return f.read()


def get_deduped(rows):
    """Remove the 7 Mar 19 re-votes of Feb 29 items."""
    feb29_texts = {
        r.get("resolution_text", "")[:100]: r
        for r in rows
        if r.get("date", "") == "20240229"
    }
    return [
        r
        for r in rows
        if not (
            r.get("date", "") == "20240319"
            and r.get("resolution_text", "")[:100] in feb29_texts
        )
    ]


def main():
    global passed, failed, warnings
    print("=" * 60)
    print("FINDINGS REPORT FACT-CHECKER")
    print("=" * 60)

    rows = load_contracts()
    pdfs = load_pdfs()
    report = load_report()
    deduped = get_deduped(rows)

    # ── Source data checks ──
    print("\n--- Contract Data (source: jcboe_contract_source_docs.csv) ---")

    check("Total board actions", 374, len(rows))

    total_val = sum(float(r.get("max_amount", 0) or 0) for r in rows)
    check("Total value (all items)", 402_579_067, round(total_val), tolerance=100)

    check("Unique commitments (deduped)", 367, len(deduped))

    dedup_val = sum(float(r.get("max_amount", 0) or 0) for r in deduped)
    check("Unique value (deduped)", 389_746_291, round(dedup_val), tolerance=100)

    no_docs = [r for r in rows if r.get("has_file", "") == "False"]
    check("Items with zero docs (all)", 51, len(no_docs))

    no_docs_dedup = [r for r in deduped if r.get("has_file", "") == "False"]
    check("Items with zero docs (deduped)", 50, len(no_docs_dedup))

    undoc_val = sum(float(r.get("max_amount", 0) or 0) for r in no_docs_dedup)
    check("Undocumented value (deduped)", 21_637_508, round(undoc_val), tolerance=100)

    vendors = sum(
        1
        for r in rows
        if r.get("vendor", "").strip() not in ["", "Unknown", "UNKNOWN"]
    )
    check("Vendors identified", 345, vendors)

    # ── PDF analysis checks ──
    print("\n--- PDF Analysis (source: jcboe_pdf_analysis.csv) ---")

    check("PDFs analyzed", 362, len(pdfs))

    from collections import Counter

    types = Counter(p.get("doc_type", "") for p in pdfs)
    check("ACTUAL_CONTRACT count", 20, types.get("ACTUAL_CONTRACT", 0))
    check("PO_FORM count", 262, types.get("PO_FORM", 0))
    check("PROPOSAL/QUOTE count", 39, types.get("PROPOSAL/QUOTE", 0))
    check("AMENDMENT count", 17, types.get("AMENDMENT", 0))
    check("SOFTWARE_RENEWAL count", 12, types.get("SOFTWARE_RENEWAL", 0))
    check("BID_TABULATION count", 9, types.get("BID_TABULATION", 0))
    check("OTHER count", 3, types.get("OTHER", 0))

    ac_val = sum(
        float(p.get("contract_amount", 0) or 0)
        for p in pdfs
        if p.get("doc_type", "") == "ACTUAL_CONTRACT"
    )
    check("Actual contracts value", 7_210_387, round(ac_val), tolerance=100)

    # ── Duplicate detection ──
    print("\n--- Duplicate Detection ---")

    feb29 = [r for r in rows if r.get("date", "") == "20240229"]
    mar19 = [r for r in rows if r.get("date", "") == "20240319"]
    feb_texts = {r.get("resolution_text", "")[:100] for r in feb29}
    dups = [
        r
        for r in mar19
        if r.get("resolution_text", "")[:100] in feb_texts
    ]
    check("Feb29/Mar19 duplicates", 7, len(dups))

    dup_val = sum(float(r.get("max_amount", 0) or 0) for r in dups)
    check("Duplicate value", 12_832_776, round(dup_val), tolerance=100)

    # ── Report content checks ──
    print("\n--- Report Content (source: FINDINGS_REPORT.md) ---")

    # Check that old/wrong numbers are NOT present
    bad_patterns = {
        r"\b16 findings\b": "Should be 19 findings",
        r"\b8 of the same\b": "Should be 10 of the same",
        r"\$402\.6": "Should be $389.7 (deduplicated)",
        r"\$28\.9 million": "Should be $21.6 million (deduplicated)",
        r"\$14\.5M": "Old Facilities number, should be $8.5M",
        r"HVAC / Mechanical": "Should be merged into Facilities & Maintenance",
        r"\b342 items\b": "Should be 347 or 354",
    }

    for pattern, reason in bad_patterns.items():
        if re.search(pattern, report):
            warn(f"Stale number found: {pattern}", reason)

    # Check that correct numbers ARE present
    good_patterns = {
        r"\b367\b": "Unique commitments count",
        r"\$389\.7": "Deduplicated total value",
        r"\b19 findings\b": "FY2024 finding count",
        r"\b10 of the same\b": "Repeat finding count",
        r"\b50\b.*undoc": "Undocumented items (deduped)",
        r"\$21\.6": "Undocumented value (deduped)",
        r"2024-17.*2025-12": "Transportation IEP repeat finding",
        r"2024-18.*2025-13": "Transportation County repeat finding",
    }

    for pattern, description in good_patterns.items():
        if re.search(pattern, report, re.IGNORECASE | re.DOTALL):
            print(f"  PASS  Report contains: {description}")
            passed += 1
        else:
            print(f"  FAIL  Report missing: {description}")
            failed += 1

    # ── Pennetta checks ──
    print("\n--- Pennetta Industrial Automation ---")

    pennetta = [
        r
        for r in deduped
        if "pennetta" in (r.get("vendor", "") or "").lower()
        or "pennetta" in (r.get("resolution_text", "") or "").lower()
    ]
    pennetta_val = sum(float(r.get("max_amount", 0) or 0) for r in pennetta)
    pennetta_undoc = [r for r in pennetta if r.get("has_file", "") == "False"]
    pennetta_undoc_val = sum(
        float(r.get("max_amount", 0) or 0) for r in pennetta_undoc
    )

    check("Pennetta unique items", 10, len(pennetta))
    check("Pennetta total (deduped)", 12_109_125, round(pennetta_val), tolerance=100)
    check("Pennetta undocumented items", 3, len(pennetta_undoc))
    check("Pennetta undocumented value", 7_686_000, round(pennetta_undoc_val), tolerance=100)

    # ── Summary ──
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 60)

    if failed > 0:
        print("\nFAILED — fix the issues above before committing.")
        sys.exit(1)
    elif warnings > 0:
        print("\nPASSED with warnings — review warnings above.")
        sys.exit(0)
    else:
        print("\nALL CHECKS PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
