#!/usr/bin/env python3
"""
Build DATA object for gms-jcboe-dashboard.html from fresh source CSVs.

Reads:
  - jcboe_contract_source_docs.csv (board actions, vendor, amount, attached files)
  - jcboe_pdf_analysis.csv (per-PDF classification)
  - undoc_summaries.json (categorized plain-English summaries + exclusion flags)

Outputs:
  - dashboard_data.json (JSON with keys: meetings, vendors, undocumented, amendments, pdf_types, totals)

The DATA object follows the schema expected by gms-jcboe-dashboard.html. Run this
script whenever source data changes, then paste the output into the dashboard HTML
(replace the `var DATA = {...}` line).
"""

import csv
import json
import re
from collections import defaultdict, Counter

CONTRACT_CSV = "jcboe_contract_source_docs.csv"
PDF_CSV = "jcboe_pdf_analysis.csv"
UNDOC_JSON = "undoc_summaries.json"
OUT = "dashboard_data.json"


def load_contracts():
    with open(CONTRACT_CSV) as f:
        return list(csv.DictReader(f))


def load_pdfs():
    with open(PDF_CSV) as f:
        return list(csv.DictReader(f))


def load_undoc():
    with open(UNDOC_JSON) as f:
        return json.load(f)


def dedupe(rows):
    """Apply both dedup rules: Feb29/Mar19 re-votes and HP state contract re-vote."""
    feb29 = {r["resolution_text"][:100]: r for r in rows if r.get("date") == "20240229"}
    step1 = [
        r for r in rows
        if not (r.get("date") == "20240319" and r["resolution_text"][:100] in feb29)
    ]
    step2 = [
        r for r in step1
        if not (
            r.get("date") == "20250828"
            and abs(float(r.get("max_amount", 0) or 0) - 1029870.0) < 1
            and "hewlett" in (r.get("resolution_text", "") or "").lower()
        )
    ]
    return step2


def build_meetings(rows):
    """Aggregate rows by meeting date → meeting object with items[]."""
    by_date = defaultdict(list)
    name_by_date = {}
    for r in rows:
        d = r.get("date", "")
        by_date[d].append(r)
        name_by_date[d] = r.get("meeting", "")

    meetings = []
    for d in sorted(by_date.keys()):
        items = by_date[d]
        with_doc = sum(1 for r in items if r.get("has_file") == "True")
        without_doc = sum(1 for r in items if r.get("has_file") != "True")
        total_value = sum(float(r.get("max_amount", 0) or 0) for r in items)
        doc_value = sum(float(r.get("max_amount", 0) or 0) for r in items if r.get("has_file") == "True")
        undoc_value = total_value - doc_value
        meetings.append({
            "date": d,
            "name": name_by_date[d],
            "total_items": len(items),
            "with_doc": with_doc,
            "without_doc": without_doc,
            "total_value": total_value,
            "doc_value": doc_value,
            "undoc_value": undoc_value,
            "items": [
                {
                    "vendor": r.get("vendor", ""),
                    "amount": float(r.get("max_amount", 0) or 0),
                    "has_file": r.get("has_file") == "True",
                    "file_count": int(r.get("file_count", 0) or 0),
                    "file_types": r.get("file_types", ""),
                    "text": (r.get("resolution_text", "") or "")[:200],
                }
                for r in items
            ],
        })
    return meetings


def normalize_vendor(v):
    """Clean vendor name for aggregation — canonicalize known vendors to a single name."""
    v = (v or "").strip()
    if not v:
        return ""
    # Common OCR/extraction junk patterns
    if v.lower() in ("vendors", "vendor", "na na na na", "unknown", ""):
        return ""

    vl = v.lower()
    # Canonicalization map — keyed by substring, value is the canonical vendor name.
    # Check specific vendors first so they aggregate across extracted name variants.
    canonical_rules = [
        ("pennetta",                    "Pennetta Industrial Automation"),
        ("c. dougherty",                "C. Dougherty & Co., Inc."),
        ("dougherty & co",              "C. Dougherty & Co., Inc."),
        ("adams, lattiboudere",         "Adams, Lattiboudere, Croot & Herman LLC"),
        ("adams lattiboudere",          "Adams, Lattiboudere, Croot & Herman LLC"),
        ("adams",                       "Adams, Lattiboudere, Croot & Herman LLC"),
        ("machado law",                 "Machado Law Group LLC"),
        ("machado",                     "Machado Law Group LLC"),
        ("genova burns",                "Genova Burns LLC"),
        ("riggs distler",               "Riggs Distler & Company Inc."),
        ("riggs, distler",              "Riggs Distler & Company Inc."),
        ("strulowitz",                  "Strulowitz & Gargiulo"),
        ("hewlett packard",             "Hewlett Packard"),
        ("hewlett-packard",             "Hewlett Packard"),
        ("edmentum",                    "Edmentum Inc."),
        ("frontline education",         "Frontline Education"),
        ("frontline educational",       "Frontline Education"),
        ("vector solutions",            "Vector Solutions"),
        ("spectrotel",                  "Spectrotel"),
        ("center for supportive",       "Center for Supportive Schools"),
        ("hudson community enterprises","Hudson Community Enterprises"),
        ("rutgers",                     "Rutgers Behavioral Health Care"),
        ("peak pediatrics",             "Peak Pediatrics"),
        ("bergen county",               "Bergen County Special Services"),
        ("kid's empire",                "Kid's Empire Transportation"),
        ("kids empire",                 "Kid's Empire Transportation"),
        ("kid s empire",                "Kid's Empire Transportation"),
        ("nw transport",                "NW Transportation"),
        ("tlc couriers",                "TLC Couriers"),
        ("hudson county transport",     "Hudson County Transport Inc."),
        ("hudson county trans",         "Hudson County Transport Inc."),
        ("mayor transport",             "Mayor Transportation LLC"),
        ("jr transport",                "JR Transportation"),
        ("pameh",                       "Pameh LLC"),
        ("american star",               "American Star Transport"),
        ("sal electric",                "Sal Electric Co."),
        ("west side tire",              "West Side Tire and Auto"),
        ("njpsa",                       "NJPSA/FEA"),
        ("inspired instruction",        "Inspired Instruction"),
        ("institute for multi-sensory", "Institute for Multi-Sensory Education"),
        ("cdw",                         "CDW"),
    ]
    for needle, canonical in canonical_rules:
        if needle in vl:
            return canonical

    # If it's long garbled text (likely OCR'd from a PDF), drop it so it doesn't pollute
    if len(v) > 80:
        return ""
    return v


def build_vendors(rows):
    """Aggregate rows by normalized vendor."""
    by_vendor = defaultdict(list)
    for r in rows:
        v = normalize_vendor(r.get("vendor", ""))
        if not v:
            continue
        by_vendor[v].append(r)

    vendors = []
    for v, items in by_vendor.items():
        with_doc = sum(1 for r in items if r.get("has_file") == "True")
        without_doc = sum(1 for r in items if r.get("has_file") != "True")
        total = sum(float(r.get("max_amount", 0) or 0) for r in items)
        undoc_value = sum(float(r.get("max_amount", 0) or 0) for r in items if r.get("has_file") != "True")
        meetings_set = set(r.get("date", "") for r in items)
        gap_details = [
            {
                "date": r.get("date", ""),
                "amount": float(r.get("max_amount", 0) or 0),
                "text": (r.get("resolution_text", "") or "")[:300],
            }
            for r in items
            if r.get("has_file") != "True"
        ]
        vendors.append({
            "vendor": v,
            "count": len(items),
            "total": total,
            "with_doc": with_doc,
            "without_doc": without_doc,
            "undoc_value": undoc_value,
            "meetings": len(meetings_set),
            "gap_details": gap_details,
            "is_vendor": True,
            "gap_rate": (without_doc / len(items) * 100) if items else 0.0,
        })
    vendors.sort(key=lambda x: -x["total"])
    return vendors


def build_undocumented(undoc_data):
    """Build the undocumented[] array from undoc_summaries.json."""
    sums = undoc_data.get("summaries", [])
    out = []
    for s in sums:
        if "duplicate_of" in s:
            continue
        out.append({
            "idx": s["idx"],
            "date": s["date"],
            "vendor": s.get("vendor_fix", ""),
            "amount": float(s["amount"]),
            "text": s.get("summary", ""),
            "category": s.get("category", "Other"),
            "action_type": s.get("action_type"),
            "chain_status": s.get("chain_status"),
            "chain_parent_date": s.get("chain_parent_date"),
            "chain_parent_resolution": s.get("chain_parent_resolution"),
            "chain_parent_nte": s.get("chain_parent_nte"),
            "increment_amount": s.get("increment_amount"),
            "excluded_from_spending_total": s.get("excluded_from_spending_total", False),
            "excluded_reason": s.get("excluded_reason"),
        })
    return out


def build_amendments(rows):
    """Detect amendment items via text pattern matching."""
    amend_re = re.compile(
        r"(amend|increase the contract|amended to read|ratif.*renew|year \d+ of)",
        re.I,
    )
    ref_re = re.compile(r"Resolution\s*(\d+\.\d+)")
    out = []
    for r in rows:
        text = r.get("resolution_text", "") or ""
        if not amend_re.search(text):
            continue
        ref = ref_re.search(text)
        out.append({
            "date": r.get("date", ""),
            "vendor": r.get("vendor", ""),
            "amount": float(r.get("max_amount", 0) or 0),
            "has_file": r.get("has_file") == "True",
            "ref_resolution": ref.group(1) if ref else "",
            "text": text[:300],
        })
    out.sort(key=lambda x: (x["date"], x["vendor"]))
    return out


def build_pdf_types(pdfs):
    """Aggregate pdf_analysis by doc_type."""
    out = {}
    for p in pdfs:
        t = p.get("doc_type", "OTHER")
        if t not in out:
            out[t] = {"count": 0, "total": 0.0}
        out[t]["count"] += 1
        out[t]["total"] += float(p.get("contract_amount", 0) or 0)
    return out


def build_totals(rows_full, rows_dedup, undoc_data):
    """Compute top-level totals including raw and genuine undoc figures."""
    total_items = len(rows_dedup)
    total_value = sum(float(r.get("max_amount", 0) or 0) for r in rows_dedup)
    with_doc = sum(1 for r in rows_dedup if r.get("has_file") == "True")
    without_doc = sum(1 for r in rows_dedup if r.get("has_file") != "True")
    doc_value = sum(float(r.get("max_amount", 0) or 0) for r in rows_dedup if r.get("has_file") == "True")
    undoc_value = total_value - doc_value

    # Genuine undocumented spending (filters applied)
    sums = undoc_data.get("summaries", [])
    unique_sums = [s for s in sums if "duplicate_of" not in s]
    in_total = [s for s in unique_sums if not s.get("excluded_from_spending_total")]
    genuine_items = len(in_total)
    genuine_value = sum(s["amount"] for s in in_total)

    excluded = [s for s in unique_sums if s.get("excluded_from_spending_total")]
    excluded_items = len(excluded)
    excluded_value = sum(s["amount"] for s in excluded)

    meetings = set(r.get("date", "") for r in rows_full)

    return {
        "total_items": total_items,
        "with_doc": with_doc,
        "without_doc": without_doc,
        "total_value": total_value,
        "doc_value": doc_value,
        "undoc_value": undoc_value,
        "meetings_count": len(meetings),
        "date_range": f"{min(meetings)} to {max(meetings)}",
        "pdfs_analyzed": None,  # filled later
        "actual_contracts_found": None,  # filled later
        # New fields for the genuine undocumented figure
        "genuine_undoc_items": genuine_items,
        "genuine_undoc_value": genuine_value,
        "excluded_undoc_items": excluded_items,
        "excluded_undoc_value": excluded_value,
        "raw_undoc_items": without_doc,
        "raw_undoc_value": undoc_value,
    }


def main():
    rows = load_contracts()
    pdfs = load_pdfs()
    undoc = load_undoc()
    rows_dedup = dedupe(rows)

    meetings = build_meetings(rows_dedup)
    vendors = build_vendors(rows_dedup)
    undocumented = build_undocumented(undoc)
    amendments = build_amendments(rows_dedup)
    pdf_types = build_pdf_types(pdfs)
    totals = build_totals(rows, rows_dedup, undoc)

    # Patch pdf totals
    totals["pdfs_analyzed"] = len(pdfs)
    totals["actual_contracts_found"] = pdf_types.get("ACTUAL_CONTRACT", {}).get("count", 0)

    DATA = {
        "meetings": meetings,
        "vendors": vendors,
        "undocumented": undocumented,
        "amendments": amendments,
        "pdf_types": pdf_types,
        "totals": totals,
    }

    with open(OUT, "w") as f:
        json.dump(DATA, f, separators=(",", ":"))
    print(f"Wrote {OUT}")
    print(f"  meetings: {len(meetings)}")
    print(f"  vendors: {len(vendors)}")
    print(f"  undocumented: {len(undocumented)}")
    print(f"  amendments: {len(amendments)}")
    print(f"  pdf_types: {len(pdf_types)}")
    print(f"  totals: {json.dumps(totals, indent=2)}")


if __name__ == "__main__":
    main()
