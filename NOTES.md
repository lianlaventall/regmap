# Session Notes — regmap

## Session 2026-04-14 — DECISION sub-typing, GUIDED_DISCRETION, schema + taxonomy changes

### Analytical work

Full review of all 64 DECISION clauses across 4 donors (DOS: 3, ECHO: 5, GFFO: 8, AFD: 48).

**Core finding:** DECISION as a tier conflates three structurally different things — NGO autonomy, approval-gated flexibility, and donor enforcement rights. Raw DECISION counts are not a reliable measure of NGO decision space.

**DECISION sub-types defined:**

| Sub-type | Who decides | Approval needed | Notes |
|---|---|---|---|
| `DISCRETIONARY_AUTONOMY` | NGO | No | Real NGO choice, no strings |
| `CONDITIONAL_FLEXIBILITY` | NGO nominally | Yes — prior donor approval | Approval-gated; real decision is donor's |
| `DONOR_RESERVED` | Donor | N/A | Donor enforcement/intervention right; not NGO choice |

**Real NGO decision space** (DISCRETIONARY_AUTONOMY only, estimated pre-rerun):

| Donor | Raw DECISION | Est. real NGO discretion |
|---|---|---|
| DOS | 3 | ~1 |
| ECHO | 5 | ~5 |
| GFFO | 8 | ~2 |
| AFD | 48 | ~15–20 |

**GUIDED_DISCRETION — new tier identified:**

Pattern found in ~13 clauses (11 AFD, 1 DOS, 1 ECHO): NGO has genuine discretion, no approval required, but donor has stated a preference. Currently misclassified as HIGH_RISK (9 clauses) or QUALIFIED_RESTRICTION (2 clauses).

Distinct from HIGH_RISK (which implies audit risk on non-compliance) and from DECISION (which has no preference signal). Sits on the discretion side of the taxonomy but with a donor lean attached.

ECHO-020 edge case: "whenever possible and advisable, priority must be given..." → QUALIFIED_RESTRICTION, not GUIDED_DISCRETION. The `must` makes it a restriction regardless of the softener. Resolved — no impact on data.

**GUIDED_DISCRETION is almost entirely an AFD phenomenon** in this dataset, concentrated in PROCUREMENT. Signals AFD uses soft recommendation as a governance tool — institutional views stated without formal mandate.

**Full tier ladder (obligation → discretion):**
```
RESTRICTION              → must, no choice
QUALIFIED_RESTRICTION    → must, softened by context
HIGH_RISK                → should, audit risk if ignored
GUIDED_DISCRETION        → may, donor preference stated
DECISION                 → may, genuinely free choice
```

### Donor culture analysis

Key profiles derived from data:
- **DOS** — compliance is the relationship. 97.3% obligation. DECISION clauses are all approval-gated.
- **ECHO** — we set the floor; you run the operation. 19.2% real discretion, nearly all DISCRETIONARY_AUTONOMY.
- **GFFO** — binary and legalistic. Zero QUALIFIED_RESTRICTION, zero HIGH_RISK. Hard mandates or free choice, no gray zones.
- **AFD** — procedural depth with embedded preference culture. Most complex dataset, highest GUIDED_DISCRETION density.

INTEGRITY clause density = proxy for donor risk culture (institutional trust vs. distrust of implementers). High count signals preoccupation with fraud risk. Analytically distinct from general RESTRICTION count.

Full analysis + harmonization framing written to `reports/taxonomy_and_donor_culture.md`.

### Taxonomy changes applied (`config/taxonomy.yaml`)

1. **GUIDED_DISCRETION** — new tier added with trigger signals, three required conditions, boundary rule against QUALIFIED_RESTRICTION, instruction to populate `preference_signal`
2. **DECISIONS** — expanded with explicit sub-type classification instructions for the classifier (DISCRETIONARY_AUTONOMY / CONDITIONAL_FLEXIBILITY / DONOR_RESERVED)
3. **HIGH_RISK** — tightened with boundary rule: if deviation carries no audit/enforcement risk → GUIDED_DISCRETION. Removed `recommended`/`encouraged`/`suggested` from trigger words.

### Schema changes applied (`schemas/output_schema.json`)

1. `tier` enum — added `GUIDED_DISCRETION`
2. `domain` enum — replaced `ELIGIBILITY` with `ELIGIBILITY_ACTOR`, `ELIGIBILITY_COMMODITY`, `ELIGIBILITY_ASSET`; added `INTEGRITY` (bug fix — schema was stale since last taxonomy revision)
3. `decision_type` — new required field: `DISCRETIONARY_AUTONOMY | CONDITIONAL_FLEXIBILITY | DONOR_RESERVED | null`
4. `preference_signal` — new required field: string (donor's stated preference) or null. GUIDED_DISCRETION only.

### Classifier changes applied (`src/classifier.py`)

- Updated to five tiers
- Added BOUNDARY RULES section (HIGH_RISK vs GUIDED_DISCRETION, QUALIFIED_RESTRICTION vs GUIDED_DISCRETION)
- Added DECISION SUB-TYPING section with lookup phrases for each sub-type
- Added GUIDED DISCRETION PREFERENCE SIGNAL section
- Updated JSON shape: added `decision_type`, `preference_signal`; fixed `tier` and `domain` enums
- Committed and pushed to main (96ee66b)

### Extractor improvements (`src/extractor.py`) — committed 67e221b

Rewrote extractor with four improvements, all contained to `extractor.py`. Pipeline interface unchanged.

**1. Table-aware extraction**
pdfplumber's `find_tables()` detects table regions per page. Non-table text extracted separately via `page.filter()` to exclude table bboxes. Tables formatted as pipe-delimited `[TABLE]...[/TABLE]` blocks and appended to page text. Falls back to plain `extract_text()` on failure. Confirmed working on ECHO: 3 tables detected on pages 4, 8, 12.

**2. Annotation layer extraction**
Extracts PDF sticky notes and comments via `page.annots` → `data.Contents`. Appended as `[ANNOTATIONS]` block. GFFO "Annotated" filename refers to image annotations (not PDF layer) — handled gracefully with no output.

**3. Text normalization**
- Fixes hyphenation at line breaks (`obli-\ngation` → `obligation`)
- Strips standalone page number lines (`- 12 -`, `Page 3 of 45`)
- Strips visual separator lines (`----`, `====`)
- Collapses 3+ blank lines to one

**4. Header/footer stripping**
After all pages extracted, counts line frequency across pages. Lines appearing on >40% of pages (min 3) are boilerplate and stripped. Reduces token noise on large documents — particularly relevant for AFD.

### Still to do

- Pipeline rerun — all 4 donors stale. ECHO already rerun once (pre-extractor improvements), needs rerun again with new extractor.

---

## Session 2026-04-13 (continued) — Taxonomy revision

### Taxonomy analysis

Ran a full analysis of `config/taxonomy.yaml` against the 4-donor dataset. Two questions: (1) does it capture everything? (2) how does Claude go beyond it?

Full analysis saved to `reports/taxonomy_analysis_2026-04-13.txt`.

**Key finding — taxonomy functions as a calibration frame, not a ruleset.**
Claude extends well beyond the listed trigger words through semantic reasoning (compound modals, structural patterns, morphological generalisation). Strengthening trigger words has low analytical value because Claude already handles them correctly.

**Higher-value changes are in domains**, where taxonomy gaps produce false positives in cross-donor pooling analysis.

### Taxonomy changes applied

**Domains — ELIGIBILITY split (3 → 1 new)**

`ELIGIBILITY` was too broad — it was grouping three distinct compliance concerns into one domain, producing misleading "shared UNCONDITIONAL" signals:

| Old | New | What it covers |
|---|---|---|
| ELIGIBILITY | `ELIGIBILITY_ACTOR` | Who can participate: sanctions, debarment, MDB blacklists, nationality rules |
| ELIGIBILITY | `ELIGIBILITY_COMMODITY` | What can be procured: commodity restrictions, pharmaceutical indications, quality floors |
| ELIGIBILITY | `ELIGIBILITY_ASSET` | How funded assets can be used: purpose restrictions, binding periods |

**Domains — INTEGRITY added**

New domain capturing procurement integrity and fraud prevention: conflict of interest, anti-corruption certifications, falsification prohibitions, competition distortion rules.

**Why:** Regulation exists largely to prevent fraud. INTEGRITY clause density is a direct proxy for donor risk culture — a donor with 30 INTEGRITY clauses signals deep institutional distrust of implementers; one with 2 signals a partnership model. This is a distinct analytical lens that general RESTRICTION count does not provide.

AFD has ~30 clauses that were previously misclassified as ELIGIBILITY that belong here.

**Dead end signals — 6 phrases added**

Added: `prohibited`, `in no case`, `under no circumstances`, `forbidden`, `ineligible`, `only permitted`

These appear in the data and signal UNCONDITIONAL dead ends but were absent from the signals list. Adding them makes dead-end detection more robust across donor languages.

**What was NOT changed (and why)**

Trigger words and qualifiers were left unchanged. Claude already handles compound modals (`may only`, `may not`), obligation constructions (`is to be`), and morphological variants correctly through semantic reasoning. Adding them to the taxonomy is defensive but has near-zero impact on current output.

### Pipeline re-run

Not yet run. Existing output JSONs still use old `ELIGIBILITY` domain. Re-run all 4 donors before next analysis pass.

---

## Session 2026-04-13

### Goal
Rerun pipeline on all donors with clean naming (DOS replacing BHA/USAID), add AFD as a new 4-donor.

### Pipeline changes
- Created `src/pipeline.py` — single entry point for extract → classify → write. Supports single PDFs and donor folders (multi-PDF merge).
- Added dedup step to pipeline for multi-PDF donors: removes near-duplicate clauses (≥0.85 similarity) produced by overlapping source documents. Only runs when >1 PDF.
- Reduced `BATCH_SIZE` from 10 → 5 pages per API call (prevents JSON truncation on large docs).
- Added retry logic to classifier: rate limit errors back off 60s × attempt; malformed JSON retries after 10s × attempt.
- Removed fixed inter-batch delay (was slowing runs unnecessarily — retry logic handles limits).

### Donors re-run (all output renamed to clean donor IDs)
| Donor | Clauses | vs. prior run |
|---|---|---|
| DOS (was BHA) | 110 | -4 (minor classifier variance + smaller batch size) |
| ECHO | 26 | -1 (effectively identical) |
| GFFO | 56 | +13 (previous run was dropping clauses due to batch density — new count more complete) |
| AFD (new) | 475 | — |

### AFD profile
- 2 PDFs merged: `AFD-R0097 - Directives PM - 2024-v2_va.pdf` (59 pages) + `Specific AFD Rules and Procedures.pdf` (7 pages)
- 495 extracted, 20 deduped → **475 clauses**
- 72.8% RESTRICTION, 10.1% DECISION, 8.6% QUALIFIED_RESTRICTION, 8.4% HIGH_RISK
- PROCUREMENT-dominant (271/475, 57%) — makes sense given AFD-R0097 is procurement guidelines
- SAFEGUARDING: 32 clauses — first donor after DOS with meaningful safeguarding presence
- 12 null-domain clauses patched manually post-run (PROCUREMENT, ELIGIBILITY, FINANCIAL)

### Key finding: ELIGIBILITY domain is too broad
With AFD added, ELIGIBILITY became the first domain with UNCONDITIONAL dead ends across multiple donors (AFD: 18, DOS: 8, ECHO: 1, GFFO: 1). But the substance is entirely different per donor:
- **AFD** — *actor eligibility*: sanctions, debarment, conflict of interest, MDB blacklists, embargo
- **DOS** — *commodity eligibility*: pharmaceutical hard walls (specific drugs restricted to specific indications)
- **ECHO** — *standard eligibility*: quality assurance floor on medical supplies, no derogation
- **GFFO** — *asset eligibility*: grant-funded assets must not be repurposed during binding period

**Implication:** "Shared UNCONDITIONAL ELIGIBILITY" is technically true but analytically misleading. These are three distinct sub-domains — actor eligibility, commodity eligibility, asset eligibility — that warrant separate taxonomy entries in a future taxonomy revision.

### Taxonomy debt flagged
- ELIGIBILITY should be split into: `ELIGIBILITY_ACTOR`, `ELIGIBILITY_COMMODITY`, `ELIGIBILITY_ASSET`
- This would make cross-donor pooling analysis more precise and prevent false positives in the shared UNCONDITIONAL domain detection



## Session 2026-03-25

### Goal
Run GFFO through the pipeline and validate N-donor scaling with a 3-way comparison (DOS / ECHO / GFFO).

### Pipeline run — GFFO
- Input: `input/GFFO ANBest-P 2019_Annotated.pdf` (6 pages, 1 batch)
- Output: `output/GFFO ANBest-P 2019_Annotated.json` — **43 clauses**

### Tier comparison — all three donors

| Tier | DOS (n=114) | ECHO (n=27) | GFFO (n=43) | Δ ECHO vs DOS | Δ GFFO vs DOS |
|---|---|---|---|---|---|
| RESTRICTION | 88.6% | 70.4% | 86.0% | -18.2 | -2.6 |
| QUALIFIED_RESTRICTION | 0.9% | 7.4% | 2.3% | +6.5 | +1.4 |
| HIGH_RISK | 7.0% | 3.7% | 0.0% | -3.3 | -7.0 |
| DECISION | 3.5% | 18.5% | 11.6% | +15.0 | +8.1 |

Key findings:
- **GFFO clusters with DOS** — both ~87% RESTRICTION; ECHO is the outlier granting far more discretion
- **GFFO has zero HIGH_RISK** — no soft-obligation language at all; obligations are either hard or permissive, nothing in between
- **ECHO retains its outlier profile** — 5× more DECISION than DOS, highest QUALIFIED_RESTRICTION; operates differently from both

### Domain-level breakdown

**Clause count by domain:**

| Domain | DOS | ECHO | GFFO |
|---|---|---|---|
| PROCUREMENT | 41 | 18 | 1 |
| REPORTING | 24 | 2 | 19 |
| RECORD_KEEPING | 6 | 3 | 6 |
| ELIGIBILITY | 30 | 4 | 2 |
| FINANCIAL | 8 | 0 | 14 |
| SAFEGUARDING | 5 | 0 | 0 |
| SCOPE | 0 | 0 | 1 |

Key findings:
- **GFFO is reporting-heavy** — 19 of 43 clauses (44%) are REPORTING vs DOS's 21% and ECHO's 7%
- **GFFO is financial-heavy** — 14 clauses (33%) vs DOS's 7% and ECHO's 0%
- **DOS and ECHO are procurement-heavy** — 36% and 67% respectively; GFFO has almost none (1 clause)
- **DOS dominates ELIGIBILITY** — 30 clauses vs 4 (ECHO) and 2 (GFFO); pharmaceutical hard walls
- **SAFEGUARDING and SCOPE** remain sparse — SAFEGUARDING DOS-only; SCOPE 0–1 across all donors

**UNCONDITIONAL dead ends by domain:**

| Domain | DOS | ECHO | GFFO | Shared |
|---|---|---|---|---|
| PROCUREMENT | 5 | 1 | 0 | DOS+ECHO |
| REPORTING | 1 | 0 | 0 | — |
| ELIGIBILITY | 3 | 0 | 1 | DOS+GFFO |
| FINANCIAL | 1 | 0 | 3 | DOS+GFFO |

Key findings:
- **No domain has UNCONDITIONAL dead ends across all three donors** — pooling baseline is still pairwise
- **PROCUREMENT** (DOS+ECHO): same overlap as before; GFFO has no procurement clauses, so not applicable
- **ELIGIBILITY and FINANCIAL** are new pairwise overlaps between DOS and GFFO — candidate domains for DOS/GFFO cross-donor analysis
- **ECHO is a dead-end outlier** — only 1 UNCONDITIONAL across all domains; its obligations are largely conditional

**Dead end type totals:**

| Type | DOS | ECHO | GFFO |
|---|---|---|---|
| UNCONDITIONAL | 10 | 1 | 4 |
| CONDITIONAL | 17 | 1 | 2 |
| AMBIGUOUS | 1 | 1 | 0 |

### Visualizations
All four regenerated to include GFFO:
- `output/flow_viz.html` — 3-donor dropdown; GFFO: 56 nodes, 55 edges
- `output/heatmap.html` — updated domain × tier density and dead-end tabs for all 3 donors
- `output/sankey.html` — 23 nodes, 44 links across 3 donors
- `output/dag.html` — GFFO tree built and added to donor toggle

Note: heatmap reports "Shared UNCONDITIONAL domains: none" — correct, no domain has all three donors.

### DECISION clause character

Pulling the actual DECISION clauses revealed they are qualitatively different across donors — not just more or fewer:

| Donor | DECISION nature | Example |
|---|---|---|
| DOS | Approval-gated — discretion only after exception granted | "If an exception is approved, you may proceed"; "you may select a different prequalified vendor" |
| ECHO | Genuine procedural autonomy tied to context | May use negotiated single-offer via HPC; may skip pre-qualification; may award directly under €300k |
| GFFO | Largely donor-reserved rights, not implementer freedom | Agency may revoke grant; Federal Court of Audit entitled to inspect; one implementer-side clause: budget line flexibility ±20% |

DOS and GFFO have DECISION clauses in name only — DOS's are conditional on prior approval, GFFO's are the donor protecting its oversight position. ECHO is the only donor granting genuine operational discretion.

### N-donor scaling verdict
Confirmed working. All four visualizations extended cleanly to 3 donors without changes.

### Next steps
- Add more donor documents; next meaningful threshold is 5+ donors for matrix view
- Build cross-donor matrix view (rows = domain, columns = donor, cells = UNCONDITIONAL present/absent)
- Investigate SCOPE domain: GFFO has 1 clause now but DOS/ECHO still 0 — classifier may be underassigning
- Investigate SAFEGUARDING gap: DOS-only so far; likely a humanitarian-specific domain not present in GFFO/ECHO docs
- Consider phrasing normalization for ELIGIBILITY and FINANCIAL pairwise dead ends (DOS+GFFO)

---

## Session 2026-03-24 (continued)

### Goal
Build the analysis and visualization layer on top of the enriched pipeline output (dead_end, dead_end_type, domain fields). Three new visualizations plus a formal analysis report.

### Analysis
- Re-ran pipeline on DOS (114 clauses) and ECHO (27 clauses) with enriched fields confirmed in output.
- Key findings (all scaled/normalized):
  - DOS is 89% RESTRICTION vs ECHO 70% — DOS is far more restrictive
  - ECHO has ~5x more DECISION-tier clauses proportionally (19% vs 4%) — ECHO grants condition-triggered autonomy, DOS is permission-seeking
  - DOS ELIGIBILITY domain has 60% dead-end rate — pharmaceutical-specific hard walls
  - PROCUREMENT is the only domain where both donors share UNCONDITIONAL dead ends — the cross-donor pooling candidate
  - Both donors have exactly 1 AMBIGUOUS dead end — flagged for human audit
- Full report written to `reports/analysis_report_2026-03-24.md` (gitignored, local only)

### New files

**`src/flow.py`**
- Extracted all flow visualization logic out of `src/main.py` into its own self-contained module.
- Runs as `python -m src.flow` → writes `output/flow_data.json` + `output/flow_viz.html`
- Updated to include `domain`, `dead_end`, `dead_end_type` in node data
- UNCONDITIONAL dead end nodes render with distinct dark red + dashed border style
- Tooltip now shows domain and dead_end_type
- `src/main.py` deleted — flow.py follows the same parallel pattern as heatmap.py, sankey.py, dag.py

**`src/heatmap.py`**
- Two-tab interactive HTML heatmap (D3.js, self-contained)
- Tab 1: clause density by domain × tier, normalized per donor, side-by-side
- Tab 2: dead end density by domain × dead_end_type, per donor
- Domains with shared UNCONDITIONAL dead ends across both donors highlighted in yellow with "↔ shared" badge
- Cross-donor pooling callout on Tab 2
- Runs as `python -m src.heatmap` → `output/heatmap.html`

**`src/sankey.py`**
- Cross-donor Sankey: Donor → Domain (donor-specific) → Tier (shared)
- Shared tier nodes on the right show where both donors converge
- Gradient links colored source→target; hover shows clause snippets
- Runs as `python -m src.sankey` → `output/sankey.html`

**`src/dag.py`**
- Hierarchical decision flow DAG (left-to-right D3 tree layout)
- RESTRICTION clauses grouped per domain (count + tooltip) to avoid clutter
- UNCONDITIONAL dead ends shown as separate highlighted group per domain
- DECISION / HIGH_RISK / QUALIFIED_RESTRICTION shown individually with branch outcomes
- Donor toggle in header; zoom/pan
- Runs as `python -m src.dag` → `output/dag.html`

### Infrastructure
- `reports/` folder created (gitignored) for local analysis reports
- `output/` and `reports/` both gitignored — all generated artifacts stay local

### Design decisions
- All four visualization scripts are self-contained and parallel in structure — no shared entry point
- Cross-donor pooling baseline: PROCUREMENT is the only domain with UNCONDITIONAL dead ends in both donors. DOS's are commodity-specific; ECHO's is a structural channel requirement (HPC or pre-certified). Different in nature but complementary.
- SCOPE domain has 0 clauses in both documents — either not present in these docs or classifier underassigning. Worth investigating when more donors are added.

### Next steps
- Add more donor documents to test N-donor scaling of all visualizations
- Build cross-donor matrix view (rows = domain, columns = donor, cells = UNCONDITIONAL present/absent) — the pooling baseline visual
- Investigate SCOPE domain gap
- Consider Claude-powered phrasing normalization for UNCONDITIONAL clauses within shared domains

---

## Session 2026-03-24 (morning)

### Goal
Reshape the taxonomy and classifier to support cross-donor pooling and visual comparison — the foundation for a dedicated cross-donor analysis view separate from the per-donor flow visualization.

### Changes made

**`config/taxonomy.yaml`**
- Removed `where possible` from `HIGH_RISK` trigger words — it belongs only in `qualifiers`. Having it in both caused the classifier to misclassify softened mandatory language as HIGH_RISK instead of QUALIFIED_RESTRICTION.
- Added `unless otherwise specified` and `subject to availability` to `qualifiers` — both are common softening phrases in donor/humanitarian regulatory language.
- Added `dead_ends` top-level key with three types (UNCONDITIONAL, CONDITIONAL, AMBIGUOUS) and a set of signal phrases (`must not`, `shall not`, `not permitted`, etc.). UNCONDITIONAL dead ends are the candidates for cross-donor pooling.
- Added `domains` top-level key with 7 semantic buckets (PROCUREMENT, REPORTING, RECORD_KEEPING, ELIGIBILITY, FINANCIAL, SAFEGUARDING, SCOPE). Domain assignment enables grouping equivalent obligations across donors regardless of phrasing variance.

**`src/classifier.py`**
- Extended `_build_system_prompt` to read `dead_ends.signals` and `domains.values` from the taxonomy and inject them into the Claude prompt.
- Claude now outputs `dead_end` (bool), `dead_end_type` (UNCONDITIONAL/CONDITIONAL/AMBIGUOUS/null), and `domain` per clause.

**`schemas/output_schema.json`**
- Added `dead_end`, `dead_end_type`, and `domain` to the required clause fields with enums matching the taxonomy.

### Design decisions
- Cross-donor analysis will be a separate visualization from `flow_viz.html`, which is a per-donor view.
- Pooling logic: group UNCONDITIONAL dead-end clauses by `domain`, then use Claude to normalize phrasing into canonical form within each group. The visual will be a matrix — rows = domain, columns = donor, cells = present/absent.
- AMBIGUOUS dead ends are flagged for human audit before entering any baseline pool.

---

## Project state (as of 2026-03-24)

## Components

| File | Purpose |
|------|---------|
| `src/extractor.py` | Opens PDFs with `pdfplumber`, returns pages as `{page_num, text, needs_ocr}` |
| `src/ocr.py` | Renders flagged pages via `pdf2image`, runs `pytesseract` |
| `src/classifier.py` | Sends page text + taxonomy to Claude (`claude-sonnet-4-6`), returns structured JSON |
| `src/writer.py` | Writes classifier output to `output/<filename>.json` |
| `src/compare.py` | N-way tier distribution comparison across output JSONs; prints counts, percentages, and Δ pct points vs baseline |
| `src/flow.py` | Builds typed flow graph per donor → `output/flow_data.json` + `output/flow_viz.html` (D3.js force-directed, donor dropdown, hover tooltips, UNCONDITIONAL dead end styling) |
| `src/heatmap.py` | Cross-donor heatmap → `output/heatmap.html` (domain × tier density + dead end analysis, shared domain highlighting) |
| `src/sankey.py` | Cross-donor Sankey → `output/sankey.html` (Donor → Domain → Tier flow, shared tier overlap) |
| `src/dag.py` | Decision flow DAG → `output/dag.html` (hierarchical tree, grouped restrictions, individual decision/high_risk/qualified nodes with branches) |
| `config/taxonomy.yaml` | Three-tier modal language taxonomy + dead_ends + domains |
| `schemas/output_schema.json` | JSON Schema for the output format |
| `tests/test_extractor.py` | Mocked unit tests for `extract_pages` |
| `Dockerfile` | `python:3.11-slim` + Tesseract + Poppler |

## What's confirmed working

- Full pipeline: extract → OCR fallback → classify → JSON output
- Completed runs: ECHO (27 clauses) and DOS (114 clauses) with enriched dead_end/domain fields
- N-way comparison via `python -m src.compare <path1> <path2> [...]`
- All four visualizations regenerate independently: `python -m src.{flow,heatmap,sankey,dag}`
- Taxonomy is dynamic — changes to `config/taxonomy.yaml` automatically update what Claude extracts
- `reports/` folder for local analysis output (gitignored)

## Known gaps

- OCR path untested (requires Tesseract locally or Docker)
- No tests for `classifier.py`, `compare.py`, `flow.py`, `heatmap.py`, `sankey.py`, `dag.py`
- SCOPE domain has 0 clauses assigned across both current documents

## Environment notes

- API key in `.env` (gitignored), loaded via `python-dotenv`
- SOCKS proxy must be cleared before running the pipeline: prefix commands with `ALL_PROXY= all_proxy= FTP_PROXY= ftp_proxy= GRPC_PROXY= grpc_proxy=`
- `input/`, `output/`, `reports/`, and `.env` are gitignored
