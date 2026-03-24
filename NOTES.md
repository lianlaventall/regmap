# Session Notes — regmap

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
