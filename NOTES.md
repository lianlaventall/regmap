# Session Notes — regmap

## Session 2026-03-25

### Goal
Run GFFO through the pipeline and validate N-donor scaling with a 3-way comparison (BHA / ECHO / GFFO).

### Pipeline run — GFFO
- Input: `input/GFFO ANBest-P 2019_Annotated.pdf` (6 pages, 1 batch)
- Output: `output/GFFO ANBest-P 2019_Annotated.json` — **43 clauses**

### Tier comparison — all three donors

| Tier | BHA (n=114) | ECHO (n=27) | GFFO (n=43) | Δ ECHO vs BHA | Δ GFFO vs BHA |
|---|---|---|---|---|---|
| RESTRICTION | 88.6% | 70.4% | 86.0% | -18.2 | -2.6 |
| QUALIFIED_RESTRICTION | 0.9% | 7.4% | 2.3% | +6.5 | +1.4 |
| HIGH_RISK | 7.0% | 3.7% | 0.0% | -3.3 | -7.0 |
| DECISION | 3.5% | 18.5% | 11.6% | +15.0 | +8.1 |

Key findings:
- **GFFO clusters with BHA** — both ~87% RESTRICTION; ECHO is the outlier granting far more discretion
- **GFFO has zero HIGH_RISK** — no soft-obligation language at all; obligations are either hard or permissive, nothing in between
- **ECHO retains its outlier profile** — 5× more DECISION than BHA, highest QUALIFIED_RESTRICTION; operates differently from both

### Domain-level breakdown

**Clause count by domain:**

| Domain | BHA | ECHO | GFFO |
|---|---|---|---|
| PROCUREMENT | 41 | 18 | 1 |
| REPORTING | 24 | 2 | 19 |
| RECORD_KEEPING | 6 | 3 | 6 |
| ELIGIBILITY | 30 | 4 | 2 |
| FINANCIAL | 8 | 0 | 14 |
| SAFEGUARDING | 5 | 0 | 0 |
| SCOPE | 0 | 0 | 1 |

Key findings:
- **GFFO is reporting-heavy** — 19 of 43 clauses (44%) are REPORTING vs BHA's 21% and ECHO's 7%
- **GFFO is financial-heavy** — 14 clauses (33%) vs BHA's 7% and ECHO's 0%
- **BHA and ECHO are procurement-heavy** — 36% and 67% respectively; GFFO has almost none (1 clause)
- **BHA dominates ELIGIBILITY** — 30 clauses vs 4 (ECHO) and 2 (GFFO); pharmaceutical hard walls
- **SAFEGUARDING and SCOPE** remain sparse — SAFEGUARDING BHA-only; SCOPE 0–1 across all donors

**UNCONDITIONAL dead ends by domain:**

| Domain | BHA | ECHO | GFFO | Shared |
|---|---|---|---|---|
| PROCUREMENT | 5 | 1 | 0 | BHA+ECHO |
| REPORTING | 1 | 0 | 0 | — |
| ELIGIBILITY | 3 | 0 | 1 | BHA+GFFO |
| FINANCIAL | 1 | 0 | 3 | BHA+GFFO |

Key findings:
- **No domain has UNCONDITIONAL dead ends across all three donors** — pooling baseline is still pairwise
- **PROCUREMENT** (BHA+ECHO): same overlap as before; GFFO has no procurement clauses, so not applicable
- **ELIGIBILITY and FINANCIAL** are new pairwise overlaps between BHA and GFFO — candidate domains for BHA/GFFO cross-donor analysis
- **ECHO is a dead-end outlier** — only 1 UNCONDITIONAL across all domains; its obligations are largely conditional

**Dead end type totals:**

| Type | BHA | ECHO | GFFO |
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
| BHA | Approval-gated — discretion only after exception granted | "If an exception is approved, you may proceed"; "you may select a different prequalified vendor" |
| ECHO | Genuine procedural autonomy tied to context | May use negotiated single-offer via HPC; may skip pre-qualification; may award directly under €300k |
| GFFO | Largely donor-reserved rights, not implementer freedom | Agency may revoke grant; Federal Court of Audit entitled to inspect; one implementer-side clause: budget line flexibility ±20% |

BHA and GFFO have DECISION clauses in name only — BHA's are conditional on prior approval, GFFO's are the donor protecting its oversight position. ECHO is the only donor granting genuine operational discretion.

### N-donor scaling verdict
Confirmed working. All four visualizations extended cleanly to 3 donors without changes.

### Next steps
- Add more donor documents; next meaningful threshold is 5+ donors for matrix view
- Build cross-donor matrix view (rows = domain, columns = donor, cells = UNCONDITIONAL present/absent)
- Investigate SCOPE domain: GFFO has 1 clause now but BHA/ECHO still 0 — classifier may be underassigning
- Investigate SAFEGUARDING gap: BHA-only so far; likely a humanitarian-specific domain not present in GFFO/ECHO docs
- Consider phrasing normalization for ELIGIBILITY and FINANCIAL pairwise dead ends (BHA+GFFO)

---

## Session 2026-03-24 (continued)

### Goal
Build the analysis and visualization layer on top of the enriched pipeline output (dead_end, dead_end_type, domain fields). Three new visualizations plus a formal analysis report.

### Analysis
- Re-ran pipeline on BHA (114 clauses) and ECHO (27 clauses) with enriched fields confirmed in output.
- Key findings (all scaled/normalized):
  - BHA is 89% RESTRICTION vs ECHO 70% — BHA is far more restrictive
  - ECHO has ~5x more DECISION-tier clauses proportionally (19% vs 4%) — ECHO grants condition-triggered autonomy, BHA is permission-seeking
  - BHA ELIGIBILITY domain has 60% dead-end rate — pharmaceutical-specific hard walls
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
- Cross-donor pooling baseline: PROCUREMENT is the only domain with UNCONDITIONAL dead ends in both donors. BHA's are commodity-specific; ECHO's is a structural channel requirement (HPC or pre-certified). Different in nature but complementary.
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
- Completed runs: ECHO (27 clauses) and BHA (114 clauses) with enriched dead_end/domain fields
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
