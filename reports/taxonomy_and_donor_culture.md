# Taxonomy Reference, Donor Culture Analysis, and Harmonization Framing

*Based on 4 donors processed: DOS (USAID), ECHO (EU), GFFO (Germany), AFD (France). 667 total clauses.*

---

## Part 1 — The Taxonomy

### The Core Binary

Donor agreement language reduces to two fundamental categories:

- **Obligation** — the NGO must comply. Choice is not available.
- **Discretion** — the NGO or donor may act. Choice exists.

Everything in the taxonomy is a shade of one of these two. The tiers exist to capture meaningful gradations within each category.

---

### The Full Tier Ladder

**RESTRICTION**
Hard mandate. No qualifying language, no conditions, no escape clause. The NGO is required to do this.
Trigger words: `must`, `shall`, `will`, `required`, `obliged`, `mandatory`
> *"The grantee shall submit quarterly financial reports."*

**QUALIFIED_RESTRICTION**
The obligation exists but a softening phrase acknowledges that real-world constraints may make full compliance impossible. The NGO is still expected to comply — the qualifier provides cover, not permission to ignore.
Softeners: `where possible`, `as far as possible`, `where feasible`, `to the extent possible`
> *"Where possible, priority must be given to local procurement."*
Key distinction: if a `must` or `shall` exists anywhere in the clause, it is QUALIFIED_RESTRICTION — not GUIDED_DISCRETION — regardless of how much softening language surrounds it.

**HIGH_RISK**
Recommendatory language with compliance risk. No explicit mandate, but non-compliance creates audit exposure. The NGO is not technically required to comply, but deviation invites scrutiny and may trigger a finding.
Trigger words: `should`, `recommended`, `suggested`, `ideally`
> *"Financial records should be retained for seven years."*

**GUIDED_DISCRETION** *(added in current revision)*
The NGO genuinely decides — no mandate, no approval required. But the donor has stated what they prefer. The NGO is free to deviate; the preference is on record. Carries no compliance risk in isolation, but a pattern of deviation from stated preferences may accumulate reputational or relational risk.
Signals: `encouraged`, `strongly encouraged`, `it is recommended`, `it is advisable`, `is advised`, `it is good practice` — when paired with permissive framing and no underlying mandate.
> *"Country teams are strongly encouraged to recruit a dedicated Tender Officer for procurement-heavy projects."*
> *"It is recommended to request a bid security for works contracts."*

**DECISION**
Genuinely permissive. No obligation, no approval required, no preference signal. Broken into sub-types that must be read in context:

| Sub-type | Who decides | Approval needed | What it means |
|---|---|---|---|
| `DISCRETIONARY_AUTONOMY` | NGO | No | Real NGO choice, no strings |
| `GUIDED_DISCRETION` | NGO | No | Real NGO choice, donor preference stated |
| `CONDITIONAL_FLEXIBILITY` | NGO nominally | Yes — prior donor approval | Looks like discretion; the real decision is the donor's |
| `DONOR_RESERVED` | Donor | N/A | Donor retains a right to act; not an NGO choice at all |

`DONOR_RESERVED` clauses should be excluded from any analysis of NGO decision space — they are donor enforcement powers, not NGO flexibility, and are misread by treating them as equivalent to `DISCRETIONARY_AUTONOMY`.

---

### Boundary Cases

**QUALIFIED_RESTRICTION vs. GUIDED_DISCRETION:**
The test is whether a mandate exists. `"Whenever possible and advisable, priority must be given to local procurement"` is QUALIFIED_RESTRICTION — the softener doesn't remove the `must`. `"It is recommended to use standard bidding documents"` is GUIDED_DISCRETION — there is no underlying obligation.

**HIGH_RISK vs. GUIDED_DISCRETION:**
HIGH_RISK is about compliance risk — the consequence of non-compliance is audit exposure. GUIDED_DISCRETION is about operational preference — the donor is signaling a lean with no enforcement attached. `"Should retain records for 7 years"` is HIGH_RISK. `"Strongly encouraged to recruit a Tender Officer"` is GUIDED_DISCRETION.

---

### The Schema Fields That Matter Most

| Field | What it captures | Why it matters |
|---|---|---|
| `tier` | RESTRICTION / QUALIFIED_RESTRICTION / HIGH_RISK / GUIDED_DISCRETION / DECISION | Primary classification |
| `actor` | NGO / DONOR | Distinguishes DONOR_RESERVED from NGO discretion |
| `decision_type` | DISCRETIONARY_AUTONOMY / CONDITIONAL_FLEXIBILITY / DONOR_RESERVED / null | Sub-types DECISION clauses; null for all other tiers |
| `preference_signal` | Text string / null | What the donor prefers; populated for GUIDED_DISCRETION only |
| `domain` | PROCUREMENT / REPORTING / RECORD_KEEPING / ELIGIBILITY_ACTOR / ELIGIBILITY_COMMODITY / ELIGIBILITY_ASSET / FINANCIAL / INTEGRITY / SAFEGUARDING / SCOPE | Enables cross-donor domain comparison |
| `dead_end` + `dead_end_type` | UNCONDITIONAL / CONDITIONAL / AMBIGUOUS | Identifies poolable baseline requirements |
| `creates_ngo_dependency` | Boolean | DONOR actor clauses where NGO cannot act until donor completes action |

The most analytically powerful combination: `tier` × `actor` × `decision_type` × `domain`. This is what reveals whether a given clause actually constrains the NGO, and in what area of operations.

---

## Part 2 — What the Data Says About Donor Culture

### Tier Distribution

| Donor | Obligation (R+QR+HR) | GUIDED_DISCRETION | DECISION | Total |
|---|---|---|---|---|
| DOS | 160 (93.0%) | 5 (2.9%) | 7 (4.1%) | 172 |
| ECHO | 24 (77.4%) | 0 (0%) | 7 (22.6%) | 31 |
| GFFO | 48 (82.8%) | 0 (0%) | 10 (17.2%) | 58 |
| AFD | 423 (82.9%) | 20 (3.9%) | 67 (13.1%) | 510 |

*Updated 2026-04-14 following pipeline rerun with revised taxonomy, schema, and extractor improvements.*

*Note: AFD's DECISION count includes ~21 DONOR_RESERVED clauses and ~15 CONDITIONAL_FLEXIBILITY clauses. Real NGO discretion (DISCRETIONARY_AUTONOMY + GUIDED_DISCRETION) is meaningfully smaller. Post-rerun numbers will reflect this.*

Every donor agreement in this dataset is primarily a constraint document. This is not a surprise, but it is worth naming: **the instrument of donor-NGO engagement is structurally built around restriction, not partnership.**

---

### Per-Donor Culture Profiles

**DOS (USAID) — Control through eligibility and approval gates**
88.4% RESTRICTION, 172 total clauses. Only 1 `DISCRETIONARY_AUTONOMY` clause — everything else is either a hard mandate, approval-gated, or `DONOR_RESERVED`. 5 `GUIDED_DISCRETION` clauses now detected, all in PROCUREMENT (advisory vendor list references, negotiation guidance). Dominant domain is `ELIGIBILITY_COMMODITY` (97 clauses, 56%) — DOS regulates *what* can be procured more than any other dimension. Donor culture reads as: *compliance is the relationship*.

**ECHO (EU) — Operational autonomy as a design principle**
The outlier. 31 clauses total — smallest dataset but highest discretion ratio. 5 DECISION clauses, all `DISCRETIONARY_AUTONOMY` — genuine NGO choice without approval or preference signal. Zero `GUIDED_DISCRETION`. ECHO's restrictions are real but the document explicitly carves out spaces where the NGO decides. Dominant domain is PROCUREMENT (12 clauses) and ELIGIBILITY_COMMODITY (8). Donor culture reads as: *we set the floor; you run the operation*.

**GFFO (Germany) — Binary and legalistic**
58 clauses. The most structurally simple donor in the dataset — 2 QUALIFIED_RESTRICTIONs, zero HIGH_RISK, zero GUIDED_DISCRETION. Every clause is either a hard mandate or a choice. DECISION clauses split 4 `DISCRETIONARY_AUTONOMY` vs 6 `DONOR_RESERVED` — revocation rights, audit rights, interest charges. Dominant domain is REPORTING (23 clauses, 40%). Donor culture reads as: *the rules are clear; the relationship is formal*.

**AFD (France) — Procedural depth with embedded preference culture**
510 clauses — by far the largest dataset. 20 `GUIDED_DISCRETION` clauses, all in PROCUREMENT, each with a captured `preference_signal` (e.g. "use AFD standard bidding documents", "maximise use of ex-post reviews", "recruit a dedicated Tender Officer"). DECISION sub-typing: 34 `DISCRETIONARY_AUTONOMY`, 20 `DONOR_RESERVED`, 13 `CONDITIONAL_FLEXIBILITY` — raw DECISION count of 67 overstates NGO flexibility by 2x. Dominant domain is PROCUREMENT (316 clauses, 62%). Donor culture reads as: *we have strong institutional views on process, and we will make them known even when we can't mandate them*.

---

### What INTEGRITY Clause Density Reveals

INTEGRITY clauses (conflict of interest, anti-corruption certifications, falsification prohibitions) are a proxy for a donor's institutional risk culture — specifically, how much the donor trusts the implementing organization to self-regulate.

High INTEGRITY clause density signals institutional distrust of implementers. It reflects a donor that views the implementing partner as a compliance risk rather than a programmatic partner. This is worth tracking explicitly as more donors are processed, because it predicts how burdensome due diligence and audit processes will be in practice.

---

### The Real NGO Decision Space

Once `DONOR_RESERVED` and `CONDITIONAL_FLEXIBILITY` clauses are stripped out, the actual space where an NGO makes a free, unencumbered choice is much smaller than raw DECISION counts suggest:

| Donor | Raw DECISION | DISCRETIONARY_AUTONOMY | GUIDED_DISCRETION | Real NGO space | % of total |
|---|---|---|---|---|---|
| DOS | 7 | 1 | 5 | 6 | 3.5% |
| ECHO | 7 | 5 | 0 | 5 | 16.1% |
| GFFO | 10 | 4 | 0 | 4 | 6.9% |
| AFD | 67 | 34 | 20 | 54 | 10.6% |

*Updated 2026-04-14 with post-rerun actuals.*

ECHO has the highest ratio of real discretion to total clauses and the cleanest decision space — all `DISCRETIONARY_AUTONOMY`, no approval gating. DOS has almost none. AFD's 54-clause real NGO space is the largest in absolute terms but is embedded in a 510-clause document, and 20 of those 54 are preference-signaled rather than truly free.

---

## Part 3 — Harmonization and Partnership Framing

### The Pooling Problem

A common assumption in multi-donor program design is that restriction convergence means reduced compliance burden — that where donors agree, the NGO only has to comply once. The data challenges this in two ways:

1. **Donors regulate different domains.** DOS concentrates in PROCUREMENT and ELIGIBILITY. GFFO in REPORTING and FINANCIAL. AFD in PROCUREMENT at scale. When a program runs on DOS + GFFO funding simultaneously, the NGO faces additive burden across different domains, not equivalent requirements in the same domain.

2. **Same domain, different substance.** Even when two donors both regulate PROCUREMENT, their requirements may be procedurally incompatible — different thresholds, different vendor qualification processes, different documentation standards. Overlap in domain does not mean harmonization in practice.

The analysis unit for harmonization advocacy should be **domain × requirement**, not tier counts.

---

### Where Harmonization Is Achievable

The clearest targets are UNCONDITIONAL dead-end clauses — restrictions that apply regardless of any upstream decision, with no conditional carve-outs. These are the baseline requirements every implementer must meet for every donor in every context. Where donors share UNCONDITIONAL restrictions in the same domain, that is a genuine harmonization opportunity: one standard, one set of documentation, one audit trail.

The next clearest target is ELIGIBILITY_ACTOR — sanctions lists, debarment registers, nationality rules. These have the most legitimate cross-donor standardization rationale (shared blacklists, MDB-wide debarment systems) and the highest cost of duplication for implementers.

---

### The Advocacy Case

The data makes a structural argument that is harder to dismiss than anecdote:

**Mandate inflation reduces operational quality.** When 97% of an agreement is obligation and 3% is discretion, the implementing NGO has effectively been reduced to a delivery mechanism. Operational judgment — the thing that makes humanitarian response effective in unpredictable contexts — has no formal space in the agreement. This is not a compliance problem; it is a design problem.

**ECHO demonstrates an alternative is possible.** A 20% discretion rate with clearly defined floors (RESTRICTION), explicit NGO authority (DISCRETIONARY_AUTONOMY), and minimal approval-gating is achievable within a rigorous donor framework. It is not a lack of accountability — it is a different theory of what accountability means.

**GUIDED_DISCRETION is an underused tool.** AFD's preference signaling approach — stating institutional views without mandating compliance — preserves NGO flexibility while communicating donor priorities. This is a more honest instrument than converting soft expectations into formal restrictions, which is what HIGH_RISK language often does in practice.

**The CONDITIONAL_FLEXIBILITY problem.** When approval-gated choices are counted as NGO discretion, the agreement presents an illusion of flexibility. In practice, every `CONDITIONAL_FLEXIBILITY` clause is a restriction with extra steps — the NGO cannot proceed without donor action, and the donor's decision cannot be predicted or planned for. Surfacing this pattern explicitly makes the case for pre-agreed standing approvals or broader derogation frameworks (as ECHO does with its HPC procurement clauses).

---

### A Proposed Framing for Harmonization Conversations

Rather than leading with "donors should reduce restrictions" (which donors will resist as an accountability argument), the data supports a different entry point:

> *The complexity that matters for implementers is not restriction count — it is domain overlap with incompatible requirements and the unpredictability of approval-gated discretion. Harmonization doesn't mean fewer rules; it means fewer contradictory rules and fewer points of artificial uncertainty.*

This reframes harmonization as a quality and predictability argument, not a burden reduction argument. It also gives donors a path to participate: align UNCONDITIONAL requirements in shared domains, standardize ELIGIBILITY_ACTOR lists, and convert ambiguous CONDITIONAL_FLEXIBILITY clauses into explicit pre-approved derogations where the programmatic case is clear.

---

*Report reflects analysis as of 2026-04-14. All 4 donors rerun with revised taxonomy (ELIGIBILITY split, INTEGRITY domain, GUIDED_DISCRETION tier), updated schema (decision_type, preference_signal fields), and improved extractor (table handling, annotation layer, header/footer stripping, text normalization). Total corpus: 771 clauses across DOS (172), AFD (510), ECHO (31), GFFO (58).*
