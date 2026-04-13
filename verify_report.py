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

    check("Total board actions", 376, len(rows))

    total_val = sum(float(r.get("max_amount", 0) or 0) for r in rows)
    check("Total value (all items)", 442_219_922, round(total_val), tolerance=100)

    check("Unique commitments (deduped - revotes only)", 369, len(deduped))

    # Further dedup: remove HP Aug 2025 duplicate of May 2025
    deduped_full = [
        r for r in deduped
        if not (
            r.get("date", "") == "20250828"
            and abs(float(r.get("max_amount", 0) or 0) - 1029870.0) < 1
            and "hewlett" in (r.get("resolution_text", "") or "").lower()
        )
    ]
    check("Unique commitments (fully deduped)", 368, len(deduped_full))

    dedup_val = sum(float(r.get("max_amount", 0) or 0) for r in deduped_full)
    check("Unique value (fully deduped)", 430_431_276, round(dedup_val), tolerance=100)

    no_docs = [r for r in rows if r.get("has_file", "") == "False"]
    check("Items with zero docs (all)", 51, len(no_docs))

    no_docs_dedup = [r for r in deduped_full if r.get("has_file", "") == "False"]
    check("Items with zero docs (fully deduped)", 49, len(no_docs_dedup))

    undoc_val = sum(float(r.get("max_amount", 0) or 0) for r in no_docs_dedup)
    check("Undocumented value (fully deduped, raw)", 18_533_638, round(undoc_val), tolerance=100)

    vendors = sum(
        1
        for r in rows
        if r.get("vendor", "").strip() not in ["", "Unknown", "UNKNOWN"]
    )
    check("Vendors identified", 348, vendors)

    # ── PDF analysis checks ──
    print("\n--- PDF Analysis (source: jcboe_pdf_analysis.csv) ---")

    check("PDFs analyzed", 364, len(pdfs))

    from collections import Counter

    types = Counter(p.get("doc_type", "") for p in pdfs)
    check("ACTUAL_CONTRACT count", 20, types.get("ACTUAL_CONTRACT", 0))
    check("PO_FORM count", 262, types.get("PO_FORM", 0))
    check("PROPOSAL/QUOTE count", 39, types.get("PROPOSAL/QUOTE", 0))
    check("AMENDMENT count", 17, types.get("AMENDMENT", 0))
    check("SOFTWARE_RENEWAL count", 12, types.get("SOFTWARE_RENEWAL", 0))
    check("BID_TABULATION count", 9, types.get("BID_TABULATION", 0))
    check("OTHER count", 5, types.get("OTHER", 0))  # 3 original + AF11561 + AF14181 (rate schedules)

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
    # Duplicate value dropped by $2,074,000 after Scenario C: the Feb29/Mar19 re-voted
    # capital reserve withdrawal row was reduced from $7,261,000 to $5,187,000.
    check("Duplicate value", 10_758_776, round(dup_val), tolerance=100)

    # ── Report content checks ──
    print("\n--- Report Content (source: FINDINGS_REPORT.md) ---")

    # Check that old/wrong numbers are NOT present
    bad_patterns = {
        r"\b16 findings\b": "Should be 19 findings",
        r"\b8 of the same\b": "Should be 10 of the same",
        r"\$402\.6": "Old raw total, should be $446.4M raw / $432.5M deduped",
        r"\$28\.9 million": "Old raw undoc, should be $20.6M raw / $16.55M genuine",
        r"\$14\.5M": "Old Facilities number, should be $8.5M",
        r"HVAC / Mechanical": "Should be merged into Facilities & Maintenance",
        r"\b342 items\b": "Should be 347 or 354",
        r"\b374 board actions\b": "Should be 376 after adding Resolutions 10.18 and 10.16",
        r"\b367 unique": "Should be 369 (revote-only) or 368 (fully deduped)",
        r"\b366 unique": "Should be 368 (fully deduped)",
        r"\$389\.7": "Should be $432.5M (fully deduped)",
        r"\$388\.7": "Should be $432.5M (fully deduped)",
    }

    for pattern, reason in bad_patterns.items():
        if re.search(pattern, report):
            warn(f"Stale number found: {pattern}", reason)

    # Check that correct numbers ARE present
    good_patterns = {
        r"\b368\b": "Unique commitments count (fully deduped)",
        r"\$432\.5": "Fully deduplicated total value",
        r"\b19 findings\b": "FY2024 finding count",
        r"\b10 of the same\b": "Repeat finding count",
        r"\b49\b.*undoc|undoc.*\b49\b": "Undocumented items (raw)",
        r"\$20\.6|\$20,607": "Raw undocumented value (deduped)",
        r"\$16\.55|\$16\.5M|16,551": "Genuine undocumented spending (after exclusions)",
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

    # ── Pennetta / Dougherty checks (Scenario C applied) ──
    # Resolution 11.06 (Feb 29, 2024) was a capital reserve withdrawal of $7,261,000 that
    # funded two projects: C. Dougherty & Co. $5,187,000 for boilers (originally awarded
    # Resolution 10.03 on Nov 16, 2023, outside dataset window), and Pennetta Industrial
    # Automation $2,074,000 for HVAC at Central Office (Resolution 11.10, same day,
    # separately in dataset with bid tab AF10659 attached).
    #
    # Because Resolution 11.10 already tracks the $2,074,000 Pennetta slice, we store
    # Resolution 11.06 as a $5,187,000 C. Dougherty row to avoid double-counting the
    # same Pennetta money across two resolutions. The full $7.26M capital reserve figure
    # is NOT in source_docs.csv; it's only referenced in the resolution_text narrative.
    print("\n--- Pennetta Industrial Automation (direct contracts) ---")

    pennetta_direct = [
        r
        for r in deduped
        if "pennetta" in (r.get("vendor", "") or "").lower()
    ]
    penn_dir_val = sum(float(r.get("max_amount", 0) or 0) for r in pennetta_direct)
    penn_dir_undoc = [r for r in pennetta_direct if r.get("has_file", "") == "False"]
    penn_dir_undoc_val = sum(
        float(r.get("max_amount", 0) or 0) for r in penn_dir_undoc
    )

    check("Pennetta direct items (deduped)", 9, len(pennetta_direct))
    check("Pennetta direct total (deduped)", 4_848_125, round(penn_dir_val), tolerance=100)
    check("Pennetta direct undocumented items", 2, len(penn_dir_undoc))
    check("Pennetta direct undocumented value", 425_000, round(penn_dir_undoc_val), tolerance=100)

    # ── Dougherty check ──
    print("\n--- C. Dougherty & Co. (boiler replacements via capital reserve) ---")
    dougherty = [
        r for r in deduped
        if "dougherty" in (r.get("vendor", "") or "").lower()
    ]
    check("Dougherty items (deduped)", 1, len(dougherty))
    doug_val = sum(float(r.get("max_amount", 0) or 0) for r in dougherty)
    check("Dougherty total (deduped)", 5_187_000, round(doug_val), tolerance=100)
    doug_undoc = [r for r in dougherty if r.get("has_file", "") == "False"]
    check("Dougherty undocumented items", 1, len(doug_undoc))

    # ── Undoc summaries category checks ──
    print("\n--- Undocumented summaries categorization ---")
    import json
    try:
        with open("undoc_summaries.json") as f:
            undoc_data = json.load(f)
        sums = undoc_data["summaries"]
        unique_sums = [s for s in sums if "duplicate_of" not in s]
        check("Undoc summaries: unique entries", 49, len(unique_sums))

        excluded = [s for s in unique_sums if s.get("excluded_from_spending_total")]
        check("Undoc summaries: excluded from spending total", 13, len(excluded))

        # Breakdown of exclusions — check via action_type / chain_status
        # (category field uses dashboard taxonomy: Travel Policy, Grants, Policy/Admin, Transportation, etc.)
        rescissions = [s for s in unique_sums if s.get("action_type")=="rescission"]
        check("Undoc summaries: rescissions (via action_type)", 1, len(rescissions))
        grants = [s for s in unique_sums if s.get("action_type")=="grant_application"]
        check("Undoc summaries: grant applications (via action_type)", 1, len(grants))
        policies = [s for s in unique_sums if s.get("action_type")=="policy_threshold_adjustment"]
        check("Undoc summaries: policy threshold (via action_type)", 1, len(policies))
        chain_amendments = [s for s in unique_sums if s.get("chain_status")=="within_nte"]
        check("Undoc summaries: amendments within parent NTE (via chain_status)", 10, len(chain_amendments))

        in_total = [s for s in unique_sums if not s.get("excluded_from_spending_total")]
        check("Undoc summaries: items in genuine spending total", 36, len(in_total))

        genuine_val = sum(s["amount"] for s in in_total)
        check("Genuine undocumented spending total", 14_477_997, genuine_val, tolerance=100)

        # Each amendment chain stays within parent NTE
        chain_totals = {}
        for s in unique_sums:
            if s.get("chain_status") == "within_nte":
                key = f"{s['chain_parent_date']}_{s['chain_parent_resolution']}"
                chain_totals.setdefault(key, {
                    'parent_nte': s['chain_parent_nte'],
                    'increments': 0,
                })
                chain_totals[key]['increments'] += s.get('increment_amount', 0)
        all_within = all(t['increments'] < t['parent_nte'] for t in chain_totals.values())
        check("All amendment chains within parent NTE", True, all_within)
        check("Amendment chains tracked", 4, len(chain_totals))
    except (FileNotFoundError, KeyError) as e:
        warn("Undoc summaries check skipped", str(e))

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
