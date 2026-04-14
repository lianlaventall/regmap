---
title: "regmap — Taxonomy Analysis"
subtitle: "Coverage gaps, Claude's reasoning behaviour, and recommended updates"
date: "2026-04-13"
---

# Taxonomy Analysis — regmap

**Date:** 2026-04-13
**Donors analysed:** DOS (110 clauses), ECHO (26), GFFO (56), AFD (475)
**Total clauses:** 667

---

## 1. Purpose of This Document

This document analyses the `config/taxonomy.yaml` file that drives the regmap classifier. It answers two questions:

1. **Does the taxonomy capture everything?** — What language patterns appear in the data that are not accounted for in the taxonomy?
2. **How does Claude go beyond the taxonomy?** — Where is Claude reasoning semantically rather than pattern-matching against the taxonomy?

The findings are drawn from inspecting trigger words, notes, context flags, and domain assignments across all four processed donors.

---

## 2. What the Taxonomy Currently Does

The taxonomy provides four structures that are injected into Claude's system prompt at classification time:

| Structure | Purpose |
|---|---|
| **Tiers** | Four obligation levels: RESTRICTION, QUALIFIED_RESTRICTION, HIGH_RISK, DECISION |
| **Qualifiers** | Phrases that downgrade RESTRICTION → QUALIFIED_RESTRICTION |
| **Dead ends** | Signal phrases that mark terminal restrictions (UNCONDITIONAL / CONDITIONAL / AMBIGUOUS) |
| **Domains** | Seven semantic buckets for cross-donor grouping |

The taxonomy functions as a **calibration frame**, not a complete ruleset. It defines the conceptual structure and output schema; Claude fills in the rest using its understanding of regulatory language.

---

## 3. Trigger Word Gaps

### 3.1 Compound Restrictive Modals

The taxonomy lists `may` as a DECISION trigger — but `may` combined with a limiting word becomes a restriction. These compound patterns are not handled:

| Pattern | Example | Correct tier |
|---|---|---|
| `may only` | "The grant may only be requested insofar as it is needed..." | RESTRICTION |
| `may not` | "Higher salaries...may not exceed those set down in TVöD" | RESTRICTION |
| `only permitted` | "Only permitted under exceptional circumstances" | RESTRICTION / dead end |

**Risk:** Clauses using these patterns could be misclassified as DECISION. Claude currently handles them correctly through semantic reasoning, but the taxonomy does not protect against this if model behaviour changes.

### 3.2 Obligation Constructions Without Modal Verbs

German-style regulatory English frequently uses `is to be` / `are to be` constructions that carry mandatory force without a modal verb. Examples from GFFO:

- *"The grant is to be used efficiently and economically."*
- *"All income...is to be applied to the grant purpose."*
- *"Interim reports are to be submitted within..."*

None of these trigger words (`is to be`, `are to be`, `to be`) appear in the taxonomy. Claude correctly classifies them as RESTRICTION, but only through semantic understanding.

### 3.3 Missing Context Pattern Verbs

The taxonomy's `context_patterns` list is incomplete. The following obligation verbs appear in the data but are absent:

| Missing verb | Occurrences | Donor |
|---|---|---|
| `certify` | 15 | AFD |
| `undertake` / `undertakes` | 10 | AFD |
| `requires` | 7 | AFD, DOS |
| `ensures` / `ensuring` | 3 | AFD, ECHO |
| `recommends` | 1 | AFD |

Note: these are also morphological variants (`requiring` vs `required`, `ensuring` vs `ensure`). The taxonomy lists root forms only and does not account for conjugations.

### 3.4 Prohibition Phrases Not in Dead End Signals

The following absolute prohibition phrases appear in the data but are not in the `dead_ends.signals` list:

- `prohibited`
- `in no case`
- `under no circumstances`
- `forbidden`
- `ineligible`
- `only permitted`

All of these function as UNCONDITIONAL dead ends in practice.

### 3.5 Donor Rights Language

The taxonomy has no vocabulary for clauses that grant rights or discretion to the **donor** rather than the implementer. These appear frequently, especially in GFFO and AFD:

| Trigger word | Example | Classification |
|---|---|---|
| `entitled` | "The Federal Court of Audit is entitled to audit..." | DECISION (donor-side) |
| `reserves the right` | "The agency reserves the right to revoke the grant..." | DECISION (donor-side) |

Claude correctly classifies these as DECISION but assigns them to the donor actor. The taxonomy has no guidance on this distinction, meaning it relies entirely on Claude's judgment.

---

## 4. Qualifier Gaps

The qualifiers list covers common softening phrases but is missing several that appear frequently in humanitarian donor documents:

| Missing phrase | Why it matters |
|---|---|
| `unless otherwise agreed` | Common bilateral softener in AFD and ECHO agreements |
| `as appropriate` | Very common in humanitarian regulatory language |
| `to the extent practicable` | Variant of `to the extent possible` (already in taxonomy) |
| `in exceptional circumstances` | Used in ECHO to create narrow carve-outs |

**Note:** `in no case` looks like a qualifier but is actually an **intensifier** — it signals an UNCONDITIONAL dead end, not a softened restriction. It should be added to `dead_ends.signals`, not `qualifiers`.

---

## 5. Domain Gaps

### 5.1 ELIGIBILITY Is Too Broad

With AFD added as the fourth donor, ELIGIBILITY became the first domain with UNCONDITIONAL dead ends across multiple donors (AFD: 18, DOS: 8, ECHO: 1, GFFO: 1). However, the dead ends mean entirely different things:

| Donor | ELIGIBILITY dead end nature |
|---|---|
| **AFD** | *Actor eligibility* — sanctions, debarment, conflict of interest, MDB blacklists, embargo compliance |
| **DOS** | *Commodity eligibility* — pharmaceutical hard walls (specific drugs restricted to specific indications) |
| **ECHO** | *Standard eligibility* — quality assurance floor on medical supplies, no derogation possible |
| **GFFO** | *Asset eligibility* — grant-funded assets must not be repurposed during binding period |

**Implication:** Reporting "shared UNCONDITIONAL ELIGIBILITY" is technically true but analytically misleading. These represent three distinct compliance obligations that a humanitarian specialist would experience as entirely separate burdens.

**Recommended split:**

| New domain | Covers |
|---|---|
| `ELIGIBILITY_ACTOR` | Who can participate — sanctions, debarment, conflict of interest, nationality rules |
| `ELIGIBILITY_COMMODITY` | What can be procured — commodity restrictions, pharmaceutical indications, quality floors |
| `ELIGIBILITY_ASSET` | How funded assets can be used — purpose restrictions, binding periods |

### 5.2 Missing INTEGRITY Domain

AFD has approximately 30 clauses covering conflict of interest, anti-corruption certifications, sanctions compliance, and MDB blacklists. These are currently absorbed into ELIGIBILITY but represent a distinct compliance domain with its own regulatory logic. Suggested addition:

| New domain | Description |
|---|---|
| `INTEGRITY` | Anti-corruption, conflict of interest, sanctions compliance, debarment, and procurement integrity rules |

This would also allow cross-donor analysis of integrity requirements specifically — a high-value view for compliance teams.

---

## 6. How Claude Goes Beyond the Taxonomy

The trigger word data reveals that Claude is operating as a semantic reasoner, not a pattern matcher. Evidence:

### 6.1 Compound Modal Understanding

Claude correctly resolves the semantic category of compound modals that the taxonomy does not define:

- `may only` → RESTRICTION (not DECISION)
- `may not` → RESTRICTION / dead end
- `does not require` → inverse obligation (absence of restriction)
- `no derogation may be granted` → UNCONDITIONAL dead end

### 6.2 Structural Pattern Recognition

Claude identifies obligation force from sentence structure, not vocabulary. `is to be used`, `are to be submitted` carry mandatory force in German regulatory translation — Claude correctly reads this from syntax.

### 6.3 Semantic Notes as Reasoning Evidence

453 of 475 AFD clauses (95%) contain substantive notes. These are not reformulations of the clause — they are Claude's reasoning about what the clause *means* in compliance terms. Examples:

> *"Absolute prohibition on nationality-based restrictions in shortlist preparation."*

> *"`Only` signals a dead end; NGO cannot apply exclusion lists without DONOR prior approval, creating NGO dependency."*

> *"Dead end: provisional review creates no financing commitment; internal donor process with no direct NGO dependency."*

This reasoning goes well beyond what the taxonomy instructs. Claude is independently inferring compliance implications.

### 6.4 Actor Inference

The taxonomy instructs Claude to assign `actor: DONOR` for clauses describing the granting authority's actions. But it provides no vocabulary for this. Claude infers it from context: `entitled`, `reserves the right`, `may revoke`, `is authorised to` — none in the taxonomy, all correctly assigned to DONOR.

### 6.5 Morphological Generalisation

The taxonomy lists root forms (`ensure`, `required`, `comply`). Claude catches all conjugated forms: `ensuring`, `requires`, `complied`, `complying`. This is semantic generalisation, not string matching.

### 6.6 Inverse Modal Detection

Claude correctly identifies clauses that explicitly *remove* an obligation:

- `does not have to` → absence of restriction (relevant for DECISION or noting implementer latitude)
- `does not require` → same
- `no derogation may be granted` → paradoxically, this removes the possibility of exception — UNCONDITIONAL dead end

---

## 7. Summary of Recommended Taxonomy Updates

### High priority

| Change | Rationale |
|---|---|
| Add `may only`, `may not` to RESTRICTION triggers | Prevents future misclassification if model behaviour changes |
| Add `prohibited`, `in no case`, `under no circumstances`, `forbidden`, `ineligible` to dead end signals | These are UNCONDITIONAL dead ends appearing in the data |
| Add `certify`, `undertake`, `undertakes` to context_patterns | 25 occurrences across AFD alone |
| Split ELIGIBILITY into `ELIGIBILITY_ACTOR`, `ELIGIBILITY_COMMODITY`, `ELIGIBILITY_ASSET` | Shared UNCONDITIONAL detection is misleading without this |

### Medium priority

| Change | Rationale |
|---|---|
| Add `unless otherwise agreed`, `as appropriate`, `to the extent practicable` to qualifiers | Common softeners in humanitarian donor language |
| Add `INTEGRITY` domain | 30+ AFD clauses on sanctions, debarment, conflict of interest have no proper home |
| Add `is to be`, `are to be` to trigger patterns | German regulatory English construction — GFFO-specific but legitimate |

### Low priority (monitor)

| Change | Rationale |
|---|---|
| Add `entitled`, `reserves the right` as DONOR-side trigger vocabulary | Claude handles these correctly but taxonomy provides no guidance |
| Add morphological variants to context_patterns | Claude generalises correctly — low risk, but explicit coverage is cleaner |

---

## 8. Conclusion

The taxonomy is well-designed for its purpose. Its value is in defining the conceptual framework and output schema, not in enumerating every possible trigger phrase. Claude reliably extends beyond the listed vocabulary using semantic understanding of regulatory language.

The highest-risk gap is the **compound modal problem** (`may only`, `may not`) — if model behaviour drifts, clauses using these patterns could be misclassified as DECISION rather than RESTRICTION. Adding them explicitly to the taxonomy would make the classification more robust.

The highest-value structural change is **splitting ELIGIBILITY** — this would materially improve the accuracy of cross-donor pooling analysis, which is a core use case of the tool.
