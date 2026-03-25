# Plan: regmap

## Purpose
Extract, classify, and compare obligation clauses from donor agreement PDFs. Help humanitarian specialists understand donor regulation complexity — what is mandatory, what is discretionary, where donors converge, and where they diverge.

---

## Current State (as of 2026-03-25)

### Pipeline (complete)
```
input/*.pdf
  → src/extractor.py     # pdfplumber → pages with needs_ocr flag
  → src/ocr.py           # pdf2image + pytesseract for scanned pages
  → src/classifier.py    # Claude (claude-sonnet-4-6) → structured JSON per clause
  → src/writer.py        # output/<filename>.json
```

### Analysis (complete)
```
output/*.json
  → src/compare.py       # N-way tier distribution comparison (CLI)
```

### Visualizations (complete)
```
output/*.json
  → src/flow.py          # per-donor D3 force-directed graph → output/flow_viz.html
  → src/heatmap.py       # cross-donor domain × tier density + dead-end analysis → output/heatmap.html
  → src/sankey.py        # cross-donor Donor → Domain → Tier flow → output/sankey.html
  → src/dag.py           # hierarchical decision DAG per donor → output/dag.html
```

Run any visualization independently:
```bash
python -m src.{flow,heatmap,sankey,dag}
```

### Donors processed
| Donor | Clauses | Dominant domains |
|---|---|---|
| BHA (USAID) | 114 | PROCUREMENT, ELIGIBILITY |
| ECHO (EU) | 27 | PROCUREMENT |
| GFFO (Germany) | 43 | REPORTING, FINANCIAL |

---

## Taxonomy (`config/taxonomy.yaml`)

### Tiers
| Tier | Description | Trigger words |
|---|---|---|
| RESTRICTION | Hard mandatory obligations | must, will, shall, required, binding, obliged, mandatory |
| QUALIFIED_RESTRICTION | Mandatory softened by a qualifier phrase | RESTRICTION trigger + qualifier phrase |
| HIGH_RISK | Soft obligations with compliance risk | recommended, suggested, encouraged, should, ideally |
| DECISION | Permissive language — discretion granted | may, can |

### Qualifiers
Phrases that downgrade RESTRICTION → QUALIFIED_RESTRICTION:
`where possible`, `where feasible`, `where appropriate`, `as far as possible`, `to the extent possible`, `if applicable`, `unless otherwise specified`, `subject to availability`

### Context patterns
Verb-first clauses that signal obligation regardless of modal word:
`submit`, `ensure`, `verify`, `demonstrate`, `confirm`, `provide`, `notify`, `comply`, `maintain`, `retain` → sets `context_flag: true`

### Dead ends
Terminal restrictions that stop a decision path:

| Type | Meaning |
|---|---|
| UNCONDITIONAL | Applies regardless of upstream decisions — cross-donor pooling candidate |
| CONDITIONAL | Reachable only via a specific decision branch |
| AMBIGUOUS | Looks absolute but has unresolved scope — flagged for human audit |

Signal phrases: `must not`, `shall not`, `not permitted`, `not allowed`, `cannot be`, `only from`, `no exceptions`, `not acceptable`

### Domains
| Domain | Description |
|---|---|
| PROCUREMENT | Sourcing, vendor selection, supply chain rules |
| REPORTING | Monitoring, indicators, progress reports |
| RECORD_KEEPING | Documentation retention and audit trails |
| ELIGIBILITY | Who/what qualifies — commodity, actor, or geography restrictions |
| FINANCIAL | Budget management, expenditure rules, audit rights |
| SAFEGUARDING | Protection, do-no-harm, beneficiary welfare |
| SCOPE | Geographic, sectoral, or thematic coverage boundaries |

---

## Key analytical findings (3-donor baseline)

### Tier profiles
- **BHA** — 88.6% RESTRICTION; most prescriptive; discretion is approval-gated not genuine
- **ECHO** — 18.5% DECISION; structural outlier; grants genuine operational autonomy via HPC mechanisms
- **GFFO** — 86% RESTRICTION, zero HIGH_RISK; obligations are binary (mandatory or permissive); DECISION clauses are donor-reserved audit rights, not implementer freedoms

### DECISION clause character
| Donor | DECISION nature |
|---|---|
| BHA | Narrow, approval-gated — "if exception approved, you may proceed" |
| ECHO | Genuine procedural autonomy — negotiated procedures, skip pre-qualification, direct award under €300k |
| GFFO | Largely donor-reserved rights — agency may revoke, audit, inspect; implementer gets limited budget flexibility (±20%) |

### Dead-end overlap (UNCONDITIONAL)
| Domain | BHA | ECHO | GFFO |
|---|---|---|---|
| PROCUREMENT | 5 | 1 | 0 |
| ELIGIBILITY | 3 | 0 | 1 |
| FINANCIAL | 1 | 0 | 3 |

No domain has UNCONDITIONAL dead ends across all three donors — pooling is pairwise, not universal.

---

## Visualizations — purpose and what to look for

### `flow_viz.html` — per-donor force-directed graph
- Donor dropdown to switch view
- UNCONDITIONAL dead end nodes: dark red + dashed border
- Tooltip shows domain, tier, dead_end_type
- Use to: trace individual clause relationships within a single donor

### `heatmap.html` — cross-donor density matrix
- Tab 1: clause density by domain × tier, normalized, side-by-side per donor
- Tab 2: dead end density by domain × dead_end_type per donor; shared UNCONDITIONAL domains highlighted
- Use to: compare where donors concentrate obligations and where dead ends cluster

### `sankey.html` — cross-donor flow
- Donor → Domain (donor-specific nodes) → Tier (shared nodes on right)
- Shared tier nodes show where all donors converge
- Use to: see the overall flow from donor identity through subject matter to obligation type

### `dag.html` — decision DAG per donor
- Hierarchical left-to-right tree; donor toggle
- RESTRICTION clauses grouped per domain (count + tooltip)
- UNCONDITIONAL dead ends as separate highlighted group per domain
- DECISION / HIGH_RISK / QUALIFIED_RESTRICTION shown individually with branch outcomes
- Use to: map the decision pathway a humanitarian specialist must navigate per donor

---

## Next: app layer for humanitarian specialists

### Goal
Surface the analysis to humanitarian specialists who need to understand donor regulation complexity without running Python. The app should let them explore:
- How restrictive each donor is, and in which domains
- Where donors converge on hard requirements vs. where they differ
- What genuine discretion exists (real DECISION clauses) vs. what is approval-gated or donor-reserved
- Which UNCONDITIONAL dead ends appear across multiple donors (the compliance floor)

### Proposed approach
A lightweight web app (likely Flask or FastAPI backend + simple frontend) that:

1. **Upload / select donor documents** — drop PDFs, trigger the pipeline, store results
2. **Donor profiles** — per-donor summary card: clause count, tier breakdown, domain distribution, dead-end count
3. **Cross-donor comparison** — the heatmap and sankey views embedded/linked, plus the N-way tier table from `compare.py`
4. **Dead-end matrix** — rows = domain, columns = donor, cells = UNCONDITIONAL present/absent; the cross-donor compliance floor view
5. **Clause explorer** — filterable table of clauses by donor, domain, tier, dead_end_type; full clause text on expand
6. **DECISION clause spotlight** — dedicated view surfacing what genuine autonomy exists per donor, labelled by character (approval-gated / procedural autonomy / donor-reserved)

### Open questions before building
- Self-hosted or hosted? (affects auth, infra)
- Who are the primary users — legal/compliance teams, programme officers, both?
- Should the pipeline run in-app (async job) or is pre-processing and loading JSONs sufficient?
- Output format — is the existing JSON schema sufficient or does the app need additional fields?

---

## Known gaps
- OCR path untested end-to-end (requires Tesseract locally or Docker)
- No tests for classifier, compare, or any visualization script
- SCOPE domain: 0–1 clauses across all donors — possibly underassigned by classifier
- SAFEGUARDING: BHA-only so far — may be document-type specific
- Cross-donor phrasing normalization (Claude-powered) not yet built for ELIGIBILITY/FINANCIAL pairwise dead ends
