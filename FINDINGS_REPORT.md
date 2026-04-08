# Where Did the Money Go?

## A GMS Investigation into Jersey City Board of Education Contract Transparency

**Governance Memory System (GMS) | OCC Research**
**April 2026**

---

## How to Read This Report

If you've ever tried to follow a Board of Education meeting — on BoardDocs, in person, or in the minutes — you know the language can be hard to follow. Resolutions are full of parliamentary jargon: "WHEREAS," "BE IT RESOLVED," "pursuant to N.J.S.A. 18A:18A-4.1," and references to prior resolutions by number. It's designed for legal compliance, not for residents trying to understand what's happening with their tax dollars.

**This report is a plain-language guide.** I translated the jargon into straightforward English so that any Jersey City resident — whether you're a parent, a student, a homeowner, or just someone who pays taxes here — can understand what the Board is approving, what documentation is missing, and why it matters. When I do use technical terms (like "encumbrance" or "excess surplus"), I explain what they mean right there in the text.

Think of this as the companion guide you wish existed when you tried to read the meeting minutes yourself.

---

## TLDR

I looked at every contract the Jersey City Board of Education approved over the last two years. I checked whether the actual agreements — the documents that say what a company will do, for how much, and under what conditions — were available to the public.

**They almost never were.**

Out of 367 unique spending commitments worth $389.7 million, I found just 20 actual signed contracts in the attached documents — covering only $7.2 million. That means **95% of contract approvals lack the actual agreement.** And when I compared my findings to the district's own official audit? The auditors found the same problems — and then some.

This isn't just a transparency problem. It's a compliance problem. And it affects every taxpayer and student in Jersey City.

---

## Who I Am

[OCC Research](https://occresearch.org) builds governance infrastructure for institutions that matter. The Governance Memory System (GMS) treats governance as a solvable engineering problem — I believe that when decisions are documented, tracked, and made accessible, better outcomes follow.

This investigation applies GMS methodology to a question any Jersey City resident should be able to answer: **When the Board of Education votes to spend your money, can you see the actual contract?**

---

## What I Did

I built software that systematically analyzed the Jersey City Board of Education's public records on [BoardDocs](https://go.boarddocs.com/nj/jcps/Board.nsf/Public) — the platform where the Board posts its meeting agendas and attachments.

Here's what I checked:

1. **Every meeting** from January 2024 through March 2026 — 42 meetings total (regular sessions, special meetings, and reorganizations)
2. **Every contract approval** on each agenda — 374 items where the Board voted to spend money on a contract, agreement, or purchase order over $10,000
3. **Every attached document** — I downloaded 362 PDFs and analyzed what was actually inside them using text extraction and OCR (optical character recognition for scanned documents)
4. **Every vendor name** — I identified who received the contracts, extracting names from resolution text, cross-referencing procurement numbers, and OCR-ing purchase order forms

All data was collected from publicly available records. No private or restricted information was accessed.

---

## The Numbers

| What I Measured | What I Found |
|---|---|
| Meetings analyzed | 42 |
| Board actions tracked | 374 (367 unique spending commitments) |
| Total contract value | $389.7 million (unique commitments) |
| Items with zero documents attached | 50 ($21.6 million) |
| PDFs downloaded and analyzed | 362 |
| **Actual signed contracts found** | **20 out of 362** |
| Internal PO forms (not contracts) | 262 |
| Vendors identified | 345 out of 374 (92%) |

*Note on counting: This report uses two numbers depending on what's being measured. **374** is the total number of contract-related board actions tracked — every time the Board voted on a contract item, it counts. **367** is the number of unique spending commitments — because 7 items from the February 29, 2024 regular meeting were re-voted with identical resolution text at the March 19, 2024 special budget meeting. Both votes are real board actions, but they represent the same contracts, not additional spending. Gap rates and item counts use the 374 figure (since each board action should have documentation regardless of whether it's a re-vote). Dollar exposure calculations use the 367 figure to avoid inflating the amount of money at stake. Of the 374 board actions, 354 lack an actual signed contract. Of the 367 unique commitments, 347 lack one.*

---

## What's Actually in the Attachments?

When the Board votes to approve a contract, they sometimes attach a document. You might think that document would be the contract itself — the agreement with terms, signatures, and a scope of work.

It almost never is.

Here's what I actually found inside 362 attached PDFs:

| Document Type | Count | What It Is |
|---|---|---|
| **PO Forms** | 262 (72%) | Internal purchase orders — a form the district uses to tell itself "ok, spend this money." This is NOT the contract with the vendor. |
| **Proposals / Quotes** | 39 (11%) | A vendor's pitch or price quote, but not a signed agreement. |
| **Actual Contracts** | 20 (5.5%) | Documents with actual contract terms, scope of work, and signatures. These are what should be attached every time. |
| **Amendments** | 17 (4.7%) | Changes to existing contracts — usually to spend more money. |
| **Software Renewals** | 12 (3.3%) | License renewal notices. |
| **Bid Tabulations** | 9 (2.5%) | Spreadsheets showing who bid and who won. Useful, but not the contract. |
| **Other** | 3 (0.8%) | Unclassified. |

**The bottom line:** 20 actual contracts exist — but they cover only $7.2 million of the $389.7 million the Board approved. For 95% of contract spending, the public cannot see what was actually agreed to.

---

## What the Auditors Found — And How It Confirms My Investigation

The district's own independent auditors — Lerch, Vinci & Bliss, LLP — have now completed audits for two consecutive fiscal years: FY2023-24 (ending June 30, 2024) and FY2024-25 (ending June 30, 2025). The FY2024 audit contained **19 findings**. The FY2025 audit contained **13 findings**.

**Here's the problem: 10 of the same findings appear in both years.** The auditors told the district to fix these issues in 2024. The district didn't fix them. The same problems showed up again in 2025.

### Repeat Findings — Two Years Running

| Problem | FY2024 Finding | FY2025 Finding |
|---|---|---|
| Payroll deposits don't match required amounts | 2024-1 | 2025-1 |
| Financial books not closed on time, checks backdated | 2024-7 | 2025-3 |
| Can't provide documentation for salary/wage liabilities | 2024-8 | 2025-4 |
| No actuarial report for workers comp claims | 2024-9 | 2025-5 |
| Bank reconciliation revised multiple times with significant variance | 2024-10 | 2025-6 |
| Contract documentation missing — can't verify procurement method | 2024-13 | 2025-8 |
| State contract prices don't match invoices, docs missing | 2024-14 | 2025-9 |
| State Comptroller not notified about contracts over $2.5M | 2024-15 | 2025-10 |
| Transported students missing IEPs and tuition contracts | 2024-17 | 2025-12 |
| Transportation contracts not submitted to County for up to 12 months | 2024-18 | 2025-13 |

The FY2024 audit also found issues that may or may not have been resolved: CASPER program timesheets missing (2024-3), payroll check verification not done since 2019 (2024-4), invalid purchase order encumbrances (2024-5), Energy Savings payments not in financial system (2024-6), food service deposits made a month late (2024-16), ESEA/ESSER budget reporting inaccuracies (2024-11.1, 2024-11.2), ESSER employee rate/timesheet issues (2024-12), payroll deduction discrepancies (2024-2), and capital assets ledger not maintained (2024-19).

The FY2025 audit found **new** problems not in the prior year: employment contracts missing for Board-approved administrators (2025-2), federal grant salary approvals missing from Board minutes (2025-7), and students categorized as special education on state aid application without current IEPs (2025-11).

Many directly confirm what my GMS investigation discovered.

### Finding-by-Finding Comparison

#### Missing Contract Documentation
**What I found:** 50 unique contracts worth $21.6 million had zero documents attached on BoardDocs. Of 362 PDFs that were attached, only 20 were actual contracts.

**What the auditors found (Finding 2025-8):** *"Contract awards and purchases which exceeded the bid threshold were not approved in the minutes and therefore we were unable to determine the method of procurement."* The auditors also found:
- Prevailing wage reports from construction vendors were missing
- Political contribution disclosure forms were missing
- Post-award advertisement notices were missing
- Quotes were not obtained for certain purchases exceeding the legal threshold

**What this means:** The auditors couldn't even verify how contracts were awarded because the documentation didn't exist. The FY2024 audit (Finding 2024-13) found the same thing the year before, plus two additional problems: *"Contract change orders were not always approved by the Board in the official minutes"* and *"Documentation was unable to be provided for audit with respect to certain contracts awarded through the public advertisement for bid."*

Two years in a row, the district's own auditors said: we asked for the contracts, and the district couldn't produce them. My GMS data shows this isn't an occasional oversight — it's the norm.

---

#### Missing Employment Contracts
**What I found:** The Superintendent's employment contract ($330,440) and the School Business Administrator's contract ($216,000) were approved without attached documentation.

**What the auditors found (Finding 2025-2):** *"Salaries of certain administrative personnel approved by the Board in the minutes were not supported by employment contracts. Such contracts are required to be submitted to the County for review and approval."*

**What this means:** The people managing a $900+ million budget don't have publicly verifiable employment agreements. The County is supposed to review these contracts, but they can't review what doesn't exist.

---

#### State Contract Purchasing Problems
**What I found:** Hewlett Packard contracts ($1.03 million, appearing twice) and CDW contracts ($429K) were approved under state cooperative purchasing but without attached contract documentation.

**What the auditors found (Finding 2025-9):** *"Contract award documentation was unable to be provided for audit... Per unit prices charged on vendor invoices for payment were not in agreement with the cooperative purchasing contract award documentation... Vendor invoices were not sufficiently detailed to determine compliance with contract award pricing."*

**What this means:** The district is buying from state contract vendors but can't prove they're getting the prices they agreed to. Without the actual contract on file, there's no way to verify whether the district is being overcharged.

---

#### Contracts Over $2 Million Not Reported to the State
**What I found:** Multiple contracts exceeding $2 million — including the Pennetta Industrial Automation capital reserve withdrawal ($7.26 million) and Edmentum tutoring services ($2.13 million).

**What the auditors found (Finding 2025-10):** *"Post-award notification to the State Comptroller's office was not made for certain contracts, the cost of which exceeded $2.5 million."*

**What this means:** New Jersey law requires that the State Comptroller be notified about large contracts. The district didn't do this — in either year. The FY2024 audit (Finding 2024-15) was even more specific: *"a pre-bid notification for a contract exceeding $12.5 million was not made."* That means a contract worth more than $12.5 million went through without the State even being told it was happening.

Combined with my finding that these contracts lack public documentation, there's a pattern of large expenditures moving through without proper oversight at any level — not from the public, not from the Board's own records, and not from the State.

---

#### Transportation Contract Delays
**What I found:** Transportation contracts were frequently amended — I found 11 amendments to special education transportation routes across multiple meetings. The original vendor lists were only available in spreadsheet attachments from the original award meeting; follow-up amendments never re-attached the vendor list.

**What the auditors found (Finding 2025-13):** *"Renewal contracts for student transportation services were not submitted to the County for review and approval in a timely manner. Certain contracts were not submitted while others were submitted up to twelve (12) months after approval by the Board."*

**What this means:** The County is supposed to review transportation contracts before they take effect. Instead, contracts were being executed and kids were being transported for up to a year before the County even saw the paperwork.

---

#### Financial Reporting System Not Closed on Time
**What the auditors found (Finding 2025-3):** *"The financial reporting system for the fiscal year ending June 30, 2025 was not closed for several months subsequent to year end, resulting in financial reporting misstatements related to the District's cash balances. In addition, checks for the 2024-25 fiscal year issued subsequent to year end were back dated."*

**What this means in plain English:** The district's books weren't closed on time, which means the financial numbers were shifting even after the fiscal year ended. And checks were being backdated — meaning payments were made to look like they happened during the previous budget year when they actually happened later. This is a basic accounting control that wasn't being followed.

---

#### Bank Reconciliation Problems
**What the auditors found (Finding 2025-6):** *"The District's year-end reconciliation of the general operating bank account was revised several times, resulting in a significant variance between the cash balances reported on the District's financial records and the final reconciled bank account balance."*

**What this means in plain English:** The district tried to reconcile its main bank account at year-end and had to redo it multiple times because the numbers didn't match. A "significant variance" between what the books say and what the bank says is a red flag for any organization managing public money.

---

---

## Three Systems, Zero Contracts

The district operates three separate systems for tracking contracts. None of them reliably contain the actual signed agreement.

### System 1: The Procurement Portal (OpenGov)

The district uses an [OpenGov e-Procurement portal](https://procurement.opengov.com/portal/jcboe) to manage the bidding process. Vendors register, receive bid notifications, submit proposals, and the district posts solicitations with addenda and specifications.

I manually created an account on the procurement portal to see firsthand what information the district makes available through this system. Even though procurement records should be easily accessible to the public, I wanted to check whether the district kept more detailed documentation behind this slightly gated venue — a portal that requires registration to browse. What I found is that the portal confirms the bidding process happened, but still doesn't house the signed contracts.

The portal's own terms — written by the district — say this:

> *"Upon notification of award of contract by the Board of Education, the contractor shall sign and execute a formal contract agreement between the Board of Education and the contractor."*

> *"Contracts and related documents shall be returned to the Office of the School Business Administrator/Board Secretary within ten (10) days of receipt of notification and shall not exceed twenty-one (21) days."*

In other words: the district's own procurement rules require a signed contract to exist within 21 days of every Board approval. These contracts are supposed to be returned to the School Business Administrator's office.

I browsed the procurement portal's project list and focused on the highest-value solicitations and ones that indicated contract documentation should be present. The portal confirms these projects went through a formal bidding process with PD numbers, release dates, and addenda. The bidding happened. The Board voted. But the resulting signed contracts still aren't on BoardDocs.

### System 2: BoardDocs

This is the public-facing system where residents go to see what the Board voted on. My analysis of 362 attached PDFs found that 72% are internal purchase order forms, not contracts. Only 20 documents (5.5%) contain actual contract terms, scope, and signatures.

### System 3: The SBA's Office

The procurement portal says contracts must be returned to the School Business Administrator within 21 days. But when the independent auditors asked for these contracts, they couldn't find them. Finding 2025-8: *"Contract awards and purchases which exceeded the bid threshold were not approved in the minutes and therefore we were unable to determine the method of procurement."* Finding 2025-9: *"Contract award documentation was unable to be provided for audit."*

### What This Means

The contracts should exist. The district's own rules require them to be signed within 21 days. The procurement portal proves the bidding happened. The Board voted to approve them. But somewhere between the Board vote and the SBA's filing cabinet, the actual agreements disappear — from the public portal, from the Board's records, and from the auditor's reach.

This isn't a technology problem. All three systems exist and function. It's a **governance memory problem** — no system is responsible for ensuring the signed contract makes it from the vendor's desk back to a place where the public, the Board, or the auditors can find it.

---

## The Amendment Chain Gap — A Problem Only Memory Can Solve

This is one of the most important things I found, and it's worth explaining carefully because it affects millions of dollars and it's almost invisible unless you know to look for it.

### How It's Supposed to Work

Let's say the Board votes in June to hire 12 bus companies to drive special education students to school. That's a big deal — $1.85 million, split across a dozen small companies. At the June meeting, there's a 5-page spreadsheet attached that lists every company, every route, every daily rate, and every annual total. If you attend that meeting or pull up the agenda on BoardDocs, you can see exactly who is getting paid what.

So far, so good.

### What Happens Next

In August, one of those routes needs a change. A student needs a personal aide on the bus. That costs an extra $100 per day. The Board votes to approve the change — an "amendment" to the original contract.

Here's what the August agenda says:

> *"WHEREAS, the Jersey City Board of Education adopted Resolution 10.16 at the June 27, 2024 board meeting, awarding contracts to multiple vendors..."*

That's it. No spreadsheet. No vendor names. No route numbers. Just a reference to "Resolution 10.16" from a meeting two months ago.

If you're a parent, a journalist, or a concerned citizen reading the August agenda, you see: **"$1.85 million to multiple vendors."** Who are those vendors? The agenda doesn't say. You'd have to know to go back to the June meeting, find Resolution 10.16, and hope the spreadsheet is still there.

### Then It Gets Worse

In November, another route gets amended. More money for a different aide. The November agenda references the same June resolution. Then in December, another amendment. Then in March. Then in April, the Board votes to add three routes that were "omitted from the original resolution" — another $1.85 million, same generic language.

By now you have a chain that looks like this:

```
June 2024:  Original award — $1.85M, 12 vendors, 5-page spreadsheet attached
   ↓
Aug 2024:   Amendment — references "Resolution 10.16" — no vendor list
   ↓
Nov 2024:   Amendment — references "Resolution 10.16" — no vendor list
   ↓
Dec 2024:   Amendment — references "Resolution 10.16" — no vendor list
   ↓
Mar 2025:   Amendment — references "Resolution 10.16" — no vendor list
   ↓
Apr 2025:   New routes added — $1.85M — "multiple vendors" — no vendor list
```

Each link in the chain only makes sense if you can see the link before it. But the only meeting that actually names the vendors is the first one. Every subsequent amendment is a dead end unless you know to go back to June 2024.

### Why This Matters

I found this pattern across **121 amendments and renewals** — 32% of all contract items. It's not limited to transportation. The same thing happens with:

- **Special education services** — contracts renewed year after year, each renewal referencing the original award but never re-attaching the vendor agreement
- **Construction projects** — change orders that add hundreds of thousands of dollars, referencing the original bid resolution but not the original contract
- **Software licenses** — annual renewals that reference a prior resolution instead of attaching the current license agreement

The result is that the Board's public record becomes a maze of cross-references. Each individual item looks fine — "approved per Resolution 8.07" — but no single meeting gives you the full picture. The institutional memory lives in the chain, and the chain is broken.

### What Would Fix This

This is exactly what a Proposal Lifecycle Metadata (PLM) system solves. In a PLM system, every amendment is linked to its parent contract. When you look at the August amendment, the system automatically shows you: here's the original June award, here are the 12 vendors, here are their rates, and here's what this amendment changes. No digging. No cross-referencing. No broken chains.

I effectively built a static version of this system for this investigation. My scripts crawl every meeting, identify every contract, trace amendment references back to their originals, and surface the gaps. The fact that I found what I found — using the same public data anyone can access — proves that the infrastructure to solve this problem already exists. It just needs to be built into the process, not bolted on after the fact.

---

## The Big Picture: Follow the Money

### Where the Money Goes

The district's total General Fund expenditures for 2024-25 were **$911.8 million**. Here's how some of that breaks down based on the encumbrances (committed spending) I found:

| Category | Amount |
|---|---|
| Capital Outlay (construction, equipment) | $16.7 million |
| Operations and Maintenance | $4.2 million |
| Tuition (out-of-district placements) | $776,812 |
| Transportation | $732,357 |
| Transfer to Charter Schools | ~$174.6 million |

The district is also sitting on an **$80.5 million excess surplus** — money collected from taxpayers but not spent or allocated to a specific purpose.

### Enrollment Is Down, Spending Is Up

Student enrollment dropped **2.3%** from 29,710 to 29,037 in 2024-25 — that's 673 fewer students. Yet the district continues to approve hundreds of millions in new contracts.

Meanwhile, the pass-through to charter schools jumped **29.8%** in one year (from $168M in 2023-24 to $174.6M in 2024-25), even though charter enrollment only grew by 0.76%.

### Which Types of Spending Have the Worst Documentation?

I categorized all 374 contracts by what they're actually for. The results reveal clear patterns in where documentation is missing:

**Worst gap rates (how often docs are missing):**

| Category | Gap Rate | Gaps | Undocumented $ |
|---|---|---|---|
| Employment Contracts | 100% | 3/3 | $593,240 |
| Legal Services | 80% | 4/5 | $600,000 |
| Transportation | 61% | 17/28 | $4.6M |
| Instructional | 19% | 5/27 | $2.7M |
| Security | 17% | 1/6 | $60,000 |
| Facilities & Maintenance | 8% | 4/52 | $8.5M |

*Facilities & Maintenance includes HVAC/mechanical work. Undocumented figure calculated after removing re-voted items (see note above).*

**Biggest dollar exposure (most money without documentation):**

| Category | Undocumented $ | Gap Rate | Items |
|---|---|---|---|
| Facilities & Maintenance | $8.5M | 8% | 4/52 |
| Transportation | $4.6M | 61% | 17/28 |
| Instructional | $2.7M | 19% | 5/27 |
| Software / IT | $2.6M | 11% | 4/36 |
| Community Programs | $896K | 11% | 3/28 |
| Legal Services | $600K | 80% | 4/5 |

**Fully documented categories** (0% gap): Food Service (33 items), Construction (12 items), Architecture/Engineering (7 items), Insurance/Benefits (7 items), Equipment Repair (7 items), Supplies (7 items), Auditing (3 items). *Note: "fully documented" here means an attachment exists — not that the attachment is the actual signed contract. As shown above, most attachments are PO forms or proposals, not the agreements themselves.*

Three patterns jump out:

1. **Legal services and employment contracts are almost never documented.** The district's outside law firms (Adams Lattiboudere for labor law, Machado Law Group for special ed law) were approved for a combined $600,000 across 4 items over two years — none with contracts attached. The Superintendent's and Business Administrator's employment contracts were approved without documentation, which the auditors also flagged.

2. **Transportation has the highest gap rate among major categories (61%).** 17 of 28 transportation items — including multi-vendor route awards and special education transport amendments — have no documentation. This is where the amendment chain problem is most severe: the original vendor list exists in one meeting's attachment, but every subsequent amendment is a dead end.

3. **Facilities & Maintenance has the biggest dollar exposure ($8.5M undocumented).** This category includes HVAC/mechanical work and totals $61.8M across 52 unique items after removing re-votes. Pennetta Industrial Automation is the primary driver — handling capital reserve projects, boiler replacements, cooling units, HVAC repair services, brick and refractory services, and systems equipment inspection. Pennetta totals $12.1M across 10 unique items, with $7.3M undocumented. Their largest item — a $7.26M capital reserve withdrawal for boiler replacements — was voted on at two separate meetings (Feb 29 and Mar 19, 2024) with no documentation at either. Sal Electric also has one undocumented item ($800K). The remaining facilities vendors (William J. Guarini, Mak Group, Vanderbeck, Fox Fence, In-Line AGM) are fully documented. *Note: 7 items from the February 29, 2024 regular meeting were re-voted with identical resolution text at the March 19, 2024 special budget meeting. These represent the same spending commitments approved twice, not separate contracts. Dollar exposure figures are calculated without double-counting these re-votes.*

### Who Gets the Contracts?

My vendor analysis identified 345 out of 374 contract recipients. Some notable patterns:

**Repeat vendors with documentation gaps:**
- **Pennetta Industrial Automation** — $12.1 million across 10 unique facilities and maintenance contracts (after removing re-votes). Their largest single item ($7.26 million capital reserve withdrawal for boiler replacements) was voted on at two separate meetings with no documentation at either. $7.3M of their work is undocumented. Pennetta also won a competitive bid for $2.07M in cooling units (4 vendors competed), but even there, only a bid tabulation sheet is attached — not the signed contract.
- **Hewlett Packard** — $2.06 million in software/hardware maintenance, approved twice with identical amounts, no contract documentation either time.
- **Adams Lattiboudere** (law firm) — $450,000 in legal services, undocumented at both meetings.
- **Machado Law Group** — $150,000 in special education legal services, undocumented at both meetings.

**The transportation ecosystem:** Special education transportation alone involves 15+ small vendors (Amity Bus, E-Z Bell, Mayor Transportation, NW Transport, VAF Trans, etc.) splitting millions in route-by-route awards. The vendor lists only exist in spreadsheet attachments from the original award meeting. Any subsequent amendment — and there are many — references the original resolution without re-attaching the vendor list. A citizen looking at the amendment would see "$1.85 million to multiple vendors" with no way to know who those vendors are without digging through a different meeting from months earlier.

---

## The 17% Tax Increase — And $183 Million in Reserves

In March 2026, the Board voted 6-3 to submit a preliminary FY2027 budget of **$1.027 billion** that includes a roughly **17% increase to the local tax levy** — approximately $452 million from Jersey City property taxpayers.

The Board says the increase is driven by $98 million in lost state equalization aid. That's a real funding challenge. But the district's own audited financial statements raise questions about whether the full increase is necessary.

### What the District Is Sitting On

The ACFR — that's the Annual Comprehensive Financial Report, basically the district's official, auditor-verified financial records — for the fiscal year ended June 30, 2025 shows a General Fund balance of **$284.4 million**. That's the total amount of money the district had in its main operating accounts at year-end.

Here's where that money is:

| Category | Amount | What It Means (Plain English) |
|---|---|---|
| Reserved for Encumbrances | $24.8M | Money already promised to vendors through purchase orders — think of it as checks that have been written but not yet cashed |
| Capital Reserve | $12.7M | A savings account specifically for building repairs and construction projects |
| Designated for FY2026 | $102.7M | Money the district planned to carry over and spend during the current school year |
| Assigned for FY2026 | $46.2M | Additional money earmarked for this year, but with more flexibility in how it's used |
| **Unassigned Fund Balance** | **$98.0M** | **Money sitting in the district's accounts with no specific plan for how to spend it** |
| **Excess Surplus** | **$80.5M** | **The amount over what NJ law says a district is allowed to hold in reserve (see below)** |

**What "excess surplus" means:** New Jersey has a rule that says school districts can't stockpile too much money — the cap is 2% of their total spending. For JCPS, 2% works out to $17.4 million. The district is holding **$80.5 million above that legal limit**. By law, they're required to spend or allocate that excess in next year's budget — they can't just keep sitting on it.

**The big picture:** The total reserves entering FY2026 were **$183 million** ($102.7M designated + $80.5M excess). To put that in perspective, that's nearly 20% of the entire budget sitting in accounts while taxpayers are being asked to pay 17% more in property taxes.

### Growing Costs, Cancelled Projects

The ACFR also reveals cost trends that compound the picture:

- **Workers compensation claims nearly doubled** — from $13.8 million to $22.8 million in one year. The auditors flagged in both FY2024 and FY2025 that the district didn't get a required actuarial report for this self-insurance plan. The district is carrying $22.8 million in workers comp liability without a professional estimate of what it should actually cost.

- **Health insurance claims up 22%** — from $9.5 million to $11.6 million in unpaid claims. The new budget shows health/benefits spending jumping 15% to $168.9 million — the single largest spending increase.

- **$5.2 million in capital spending was cancelled during the audit** — projects that were budgeted and encumbered (committed) for schools, then reversed. The total capital budget was $16.7 million, but $5.2 million was pulled back. That's money that was supposed to go to school buildings and didn't.

- **Enrollment dropped 2.3%** — 673 fewer students — yet the budget continues to grow. Charter school pass-through jumped 29.8% in one year (to $174.6M) even though charter enrollment grew by less than 1%.

### The Question for April 30th

The Board has said a corrective action plan based on the audit recommendations will be presented publicly at the April 30 meeting. Superintendent Fernandez and SBA Luce have committed to this timeline. Three questions deserve answers:

1. **How much of the $183 million in reserves was actually spent in FY2026?** If the designated funds weren't fully used, the surplus may be even larger entering FY2027 — which weakens the case for a 17% tax increase.

2. **Why were $5.2 million in capital projects cancelled?** These were already approved and encumbered. What happened? Were the schools that were supposed to benefit from these projects told?

3. **What does the excess surplus corrective plan look like?** NJ law requires the district to appropriate the excess above 2%. How is the $80.5 million being deployed, and does the FY2027 budget draw it down — or does it grow further while taxes go up?

The state aid loss is real. But asking taxpayers for 17% more while holding $183 million in reserves, cancelling school construction, and unable to produce the contracts for 95% of current spending is a credibility gap that the corrective action plan needs to address.

---

## Why This Matters

This isn't about accusing anyone of wrongdoing. It's about a basic question: **Can you, as a resident of Jersey City, verify how your tax dollars are being spent?**

Right now, the answer is mostly no. Here's what's broken:

1. **The public portal is not doing its job.** BoardDocs is supposed to be the place where residents can see what the Board is voting on. But attaching a PO form instead of a contract is like giving someone a receipt instead of a menu — it tells you money was spent, but not what was agreed to.

2. **Amendments break the chain.** When a contract is amended to spend more money, the amendment should include or reference the original agreement. Instead, amendments reference a resolution number from a different meeting, and the resident has to go hunt for it themselves.

3. **The auditors confirmed the problem.** This isn't just my opinion. The district's own certified public accountants identified 13 findings, including missing contract documentation, missing employment contracts, backdated checks, and failures to notify the State about large contracts.

4. **The documentation gap is systemic.** It's not one or two contracts that slipped through. I did find 20 actual contracts — but those covered just $7.2 million out of $389.7 million in total approvals. The other 347 unique spending commitments (95%) were backed by internal forms, proposals, or nothing at all. The contracts that *are* provided tend to be smaller, lower-profile agreements (healthcare providers, engineering firms), while the largest expenditures go undocumented.

---

## What Can You Do?

### File an OPRA Request
New Jersey's Open Public Records Act (OPRA) gives you the right to request any public record. If a contract isn't on BoardDocs, you can file a request directly with the district. The JCBOE has an [online OPRA form](https://www.jcboe.org/apps/pages/index.jsp?uREC_ID=1537092&type=d&pREC_ID=1667639).

Priority contracts to request (highest-dollar undocumented items):
1. Pennetta Industrial Automation — $7.26M capital reserve/boiler contracts
2. Edmentum Inc. — $2.13M tutoring services
3. Hewlett Packard — $1.03M software/hardware (x2)
4. Special Ed Transportation routes — $933K (Dec 2025), $1.85M (June 2024)

### Attend Board Meetings
The Board meets regularly at 346 Claremont Avenue, Jersey City. Meeting schedules are posted on BoardDocs. During public comment periods, you can ask the Board to explain why contract documentation is not being attached to agenda items.

### Use This Dashboard
I built an [interactive dashboard](https://github.com/Othmangba/GMS-JCBOE) that lets you explore all 374 contracts, see which vendors have documentation gaps, and track the gap rate over time. Download `dashboard.html` and open it in any browser — no installation needed.

### Share This Report
The more residents who understand these findings, the more likely the district is to improve its practices. Share this report with your neighbors, your PTA, your local news outlet, or your Board representative.

---

## About This Project

This investigation is part of OCC Research's Governance Memory System (GMS) — a framework for building institutional memory infrastructure that makes governance cumulative, queryable, and accountable.

Two of the five GMS layers are directly demonstrated in this investigation, both built and applied by me:

**Proposal Lifecycle Metadata (PLM):** My scripts track every contract from proposal through approval, amendment, and payment — flagging when required documentation is missing at any stage. The amendment chain analysis, the vendor extraction pipeline, and the document classifier are all components of a static PLM Agent. A live version would do this in real time, blocking incomplete proposals from advancing rather than flagging them after the fact.

**Outcome Review Anchors (ORA):** The cross-reference between my findings and the official Lerch, Vinci & Bliss audits is an ORA in action. An Outcome Review Anchor asks: "did what was decided actually produce the expected result?" The Board decided to approve 374 contracts. The expected outcome is that each contract would be publicly documented, properly executed, and reported to the State where required. The ORA — anchored to the auditor's independent findings — shows that outcome was not achieved. And by comparing the FY2024 and FY2025 audits side by side, the ORA reveals something even more important: the Board was told about 19 problems, and 10 of them came back the next year unchanged. The decisions to fix those problems didn't produce outcomes either. That's a second-order governance failure — not just failing to document contracts, but failing to fix the failure.

The tools I built for this investigation are a proof of concept: a static PLM + ORA system that does retrospectively what a live system would do in real time — track every contract from proposal to payment, anchor outcomes to independent verification, and surface the gaps before they become repeat audit findings.

My name is Othman Gbadamassi. I'm the founder of OCC Research and a product of the Jersey City Public School system — McNair Academic High School, Class of 2017. This isn't an outsider's critique. I'm a long time Jersey City resident who went through these schools, benefited from the teachers and programs they fund, and came back to ask a simple question: can the community see how the money is being spent?

The answer, right now, is mostly no. But it doesn't have to stay that way.

[Full PDF Report](https://occresearch.org/gms-jcboe-report.pdf) | [Interactive Dashboard](https://github.com/Othmangba/GMS-JCBOE) | [occresearch.org](https://occresearch.org)

**Governance that remembers. Institutional Memory as a Service.**

---

*Data sourced entirely from public records. No private or restricted information was accessed. This report represents independent analysis and does not constitute legal advice or formal allegations of wrongdoing.*
---

## Methodology

### Data Sources
- **BoardDocs** (go.boarddocs.com/nj/jcps/Board.nsf) — all meeting agendas and attachments from Jan 2024 through Mar 2026
- **JCBOE Annual Comprehensive Financial Report** (ACFR) — fiscal year ended June 30, 2025
- **Auditor's Management Report on Administrative Findings, FY2024** — Lerch, Vinci & Bliss, LLP, dated February 27, 2025 (19 findings)
- **Auditor's Management Report on Administrative Findings, FY2025** — Lerch, Vinci & Bliss, LLP, dated February 24, 2026 (13 findings)
- **OpenGov e-Procurement Portal** (procurement.opengov.com/portal/jcboe) — manually reviewed high-value solicitations and those indicating contract documentation

### Tools and Process
1. **API mapping** — Identified BoardDocs API endpoints and tested rate limits
2. **Contract detection** — Regex-based identification of contract approval language in agenda items, with personnel/HR items excluded
3. **PDF analysis** — Downloaded 362 PDFs; classified using text extraction (PyMuPDF), OCR (Tesseract), and a 7-category classifier with 20 content signals
4. **Vendor extraction** — Multi-pass extraction: regex patterns on resolution text (8 patterns), PD# cross-referencing against original meeting agendas, OCR of attached PO forms, and manual normalization of duplicate names
5. **Procurement portal review** — Created an account on the district's OpenGov e-Procurement portal to manually inspect what documentation was available behind the registration wall, focusing on high-value solicitations and those that indicated contracts should be present
6. **Cross-referencing** — Compared GMS findings against the official audit report to identify corroborating evidence

### Limitations
- Vendor names could not be extracted for 29 of 374 items (8%) where the resolution uses generic language ("lowest responsible bidder") and the vendor is named only in attached spreadsheets
- PDF classification relies on text signals and may miscategorize documents with unusual formatting
- I did not analyze meeting minutes (which may contain additional context about votes and discussion)
- My contract value figures use the maximum amount stated in the resolution, which may differ from actual expenditures

### Reproducibility
All code, data, and methodology are published at [github.com/Othmangba/GMS-JCBOE](https://github.com/Othmangba/GMS-JCBOE). Anyone can run the same analysis and verify my findings.

