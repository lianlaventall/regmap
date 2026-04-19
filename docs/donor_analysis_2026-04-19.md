# Donor Analysis Report — 2026-04-19
### regmap · Post-taxonomy redesign rerun · 4 donors · 703 clauses

---

## Corpus Overview

| Donor | Clauses | Prior Count | Change |
|---|---|---|---|
| ECHO (EU) | 28 | 31 | -3 |
| GFFO (Germany) | 54 | 58 | -4 |
| DOS (USAID) | 174 | 172 | +2 |
| AFD (France) | 447 | 510 | -63 |
| **Total** | **703** | **771** | **-68** |

> Clause count changes reflect taxonomy corrections: DONOR_RIGHT now separated from DECISION, HIGH_RISK merged into GUIDED_DISCRETION.

---

## Cross-Donor Tier Comparison

| Tier | ECHO | GFFO | DOS | AFD |
|---|---|---|---|---|
| RESTRICTION | 19 (68%) | 44 (81%) | 151 (87%) | 313 (70%) |
| QUALIFIED_RESTRICTION | 2 (7%) | 1 (2%) | 2 (1%) | 29 (6%) |
| GUIDED_DISCRETION | 2 (7%) | 0 (0%) | 11 (6%) | 46 (10%) |
| DECISION | 4 (14%) | 2 (4%) | 7 (4%) | 35 (8%) |
| DONOR_RIGHT | 1 (4%) | 7 (13%) | 3 (2%) | 24 (5%) |

---

## Cross-Donor Domain Distribution

| Domain | ECHO | GFFO | DOS | AFD |
|---|---|---|---|---|
| PROCUREMENT | 12 | 1 | 27 | 280 |
| REPORTING | 2 | 22 | 24 | 35 |
| RECORD_KEEPING | 2 | 10 | 4 | 20 |
| ELIGIBILITY_ACTOR | 1 | 0 | 16 | 21 |
| ELIGIBILITY_COMMODITY | 9 | 0 | 90 | 3 |
| ELIGIBILITY_ASSET | 0 | 3 | 4 | 1 |
| INTEGRITY | 2 | 1 | 0 | 39 |
| FINANCIAL | 0 | 17 | 5 | 29 |
| SAFEGUARDING | 0 | 0 | 4 | 19 |

---

## Donor Power (DONOR_RIGHT)

### Summary

| Donor | Total DONOR_RIGHT | AUDIT | SUSPENSION | TERMINATION | INTERVENTION | Mixed Clauses |
|---|---|---|---|---|---|---|
| ECHO | 1 | 1 | 0 | 0 | 0 | 1 |
| GFFO | 7 | 3 | 0 | 3 | 1 | 2 |
| DOS | 3 | 1 | 2 | 0 | 0 | 2 |
| AFD | 24 | 9 | 1 | 1 | 13 | 10 |

> DONOR_RIGHT = power the donor holds over the NGO, separate from the obligation ladder. High count = significant reserved control.

### Key examples by sub-type

**AUDIT_RIGHT**
| Donor | Example |
|---|---|
| ECHO | "The Commission performs periodic on-site examinations to verify compliance." |
| GFFO | "The Federal Court of Audit is entitled to audit the grant recipient." |
| DOS | "All medical commodities are reviewed for appropriateness for the activity." |
| AFD | "AFD may conduct prior reviews to ensure the procurement process complies." |

**TERMINATION_RIGHT**
| Donor | Example |
|---|---|
| GFFO | "The grant-awarding agency reserves the right to revoke the grant notification." |
| GFFO | "A revocation with retrospective effect may be considered if the grant recipient does not use the grant immediately." |
| AFD | "AFD may suspend or definitively terminate its financing to a Beneficiary." |

**INTERVENTION_RIGHT** *(AFD only)*
| Example |
|---|
| "AFD may provide technical assistance with the procurement process." |
| "The procurement process may be subject to post review, if AFD so requests." |

**SUSPENSION_RIGHT**
| Donor | Example |
|---|---|
| DOS | "BHA cannot approve your application until the decision has been made regarding the proposed vendor." |
| AFD | "AFD may suspend or definitively terminate its financing to a Beneficiary." |

---

## NGO Decision Space

| Donor | Total DECISION | DISCRETIONARY_AUTONOMY | CONDITIONAL_FLEXIBILITY | Real autonomy rate |
|---|---|---|---|---|
| ECHO | 4 | 4 (100%) | 0 (0%) | 14% of corpus |
| GFFO | 2 | 2 (100%) | 0 (0%) | 4% of corpus |
| DOS | 7 | 4 (57%) | 3 (43%) | 2% of corpus |
| AFD | 35 | 26 (74%) | 9 (26%) | 6% of corpus |

> Real autonomy rate = DISCRETIONARY_AUTONOMY clauses / total clauses. ECHO remains the only donor where DECISION closely approximates genuine operational freedom.

---

## Preference Signaling (GUIDED_DISCRETION)

| Donor | Total | Strong (should/ideally) | Soft (recommended/encouraged) |
|---|---|---|---|
| ECHO | 2 | 2 (100%) | 0 (0%) |
| GFFO | 0 | — | — |
| DOS | 11 | 6 (55%) | 5 (45%) |
| AFD | 46 | 32 (70%) | 14 (30%) |

> GFFO uses zero preference signaling — consistent with binary legalistic drafting culture. AFD has the richest preference culture; 70% of its guidance leans `strong`, signaling audit-adjacent expectations rather than pure suggestions.

### Sample preference signals

**ECHO (strong)**
- "HPCs should conduct themselves with high levels of integrity and transparency."
- "Quality criteria for medical devices should be aligned to risk classification."

**DOS (strong)**
- "Provide evidence demonstrating extensive evaluation of the non-prequalified vendor facility."
- "Conduct a physical inspection of the vendor facility prior to procurement."

**DOS (soft)**
- "Consult the updated Prequalified Pharmaceutical Vendors list before requesting an exception."

**AFD (strong)**
- "Publish Procurement Plan information through a general procurement notice."

**AFD (soft)**
- "Use AFD's standard bidding documents for International Procurement Competitions."
- "Use AFD's standard Procurement Documents available on its website."

---

## Dead-End Analysis
*RESTRICTION and QUALIFIED_RESTRICTION only — terminal compliance states*

### Summary

| Donor | Total dead ends | UNCONDITIONAL | CONDITIONAL | AMBIGUOUS |
|---|---|---|---|---|
| ECHO | 1 | 0 | 0 | 1 |
| GFFO | 9 | 4 | 4 | 1 |
| DOS | 75 | 53 | 20 | 2 |
| AFD | 76 | 49 | 21 | 6 |

### UNCONDITIONAL dead ends by domain
*Candidates for cross-donor pooling — absolute restrictions with no conditional language*

| Domain | ECHO | GFFO | DOS | AFD | Shared |
|---|---|---|---|---|---|
| PROCUREMENT | 0 | 0 | 3 | 21 | DOS + AFD |
| ELIGIBILITY_ACTOR | 0 | 0 | 15 | 10 | DOS + AFD |
| ELIGIBILITY_COMMODITY | 0 | 0 | 33 | 3 | DOS + AFD |
| ELIGIBILITY_ASSET | 0 | 1 | 0 | 0 | GFFO only |
| INTEGRITY | 0 | 0 | 0 | 12 | AFD only |
| FINANCIAL | 0 | 3 | 1 | 1 | GFFO + DOS + AFD |
| SAFEGUARDING | 0 | 0 | 0 | 2 | AFD only |
| REPORTING | 0 | 0 | 1 | 0 | DOS only |

> FINANCIAL is the only domain with UNCONDITIONAL dead ends across 3 donors (GFFO, DOS, AFD) — strongest cross-donor pooling candidate. PROCUREMENT and ELIGIBILITY_ACTOR shared between DOS and AFD.

---

## Individual Donor Profiles

---

### ECHO (EU) — 28 clauses

| Metric | Value |
|---|---|
| Total clauses | 28 |
| Obligation rate | 82% (23 clauses) |
| Hard restriction rate | 68% (19 RESTRICTION) |
| Real NGO autonomy | 14% (4 DISCRETIONARY_AUTONOMY) |
| Donor power | 4% (1 DONOR_RIGHT) |
| Preference signaling | 7% (2 GUIDED_DISCRETION, all strong) |
| Dominant domain | PROCUREMENT (43%) |
| UNCONDITIONAL dead ends | 0 |

**Character:** We set the floor; you run the operation. ECHO has the lowest obligation rate and the highest real NGO autonomy. All 4 DECISION clauses are DISCRETIONARY_AUTONOMY — no approval-gating. Minimal donor power (1 AUDIT_RIGHT). ECHO's control is through standards, not surveillance.

---

### GFFO (Germany) — 54 clauses

| Metric | Value |
|---|---|
| Total clauses | 54 |
| Obligation rate | 83% (45 clauses) |
| Hard restriction rate | 81% (44 RESTRICTION) |
| Real NGO autonomy | 4% (2 DISCRETIONARY_AUTONOMY) |
| Donor power | 13% (7 DONOR_RIGHT) |
| Preference signaling | 0% |
| Dominant domain | REPORTING (41%) |
| UNCONDITIONAL dead ends | 4 (FINANCIAL, ELIGIBILITY_ASSET) |

**Character:** Binary and legalistic. Zero GUIDED_DISCRETION — GFFO never states a preference; it either mandates or reserves a right. 7 DONOR_RIGHT clauses (3 AUDIT, 3 TERMINATION, 1 INTERVENTION) represent significant enforcement toolkit held in reserve. The Federal Court of Audit has explicit constitutional audit rights. GFFO's 2 genuine NGO decisions are budget flexibility (±20%) and data storage format.

---

### DOS (USAID) — 174 clauses

| Metric | Value |
|---|---|
| Total clauses | 174 |
| Obligation rate | 94% (164 clauses) |
| Hard restriction rate | 87% (151 RESTRICTION) |
| Real NGO autonomy | 2% (4 DISCRETIONARY_AUTONOMY) |
| Donor power | 2% (3 DONOR_RIGHT) |
| Preference signaling | 6% (11 GUIDED_DISCRETION — 6 strong, 5 soft) |
| Dominant domain | ELIGIBILITY_COMMODITY (52%) |
| UNCONDITIONAL dead ends | 53 |

**Character:** Compliance is the relationship. Highest obligation rate (94%) and most UNCONDITIONAL dead ends (53) of any donor. Control is exercised upfront through rules — DONOR_RIGHT is low (3 clauses) because enforcement is built into the approval process itself (BHA cannot approve until conditions are met). ELIGIBILITY_COMMODITY dominates: pharmaceutical hard walls are DOS's primary regulatory instrument. 11 GUIDED_DISCRETION clauses concentrate around vendor inspection and pharmaceutical management.

---

### AFD (France) — 447 clauses

| Metric | Value |
|---|---|
| Total clauses | 447 |
| Obligation rate | 87% (388 clauses) |
| Hard restriction rate | 70% (313 RESTRICTION) |
| Real NGO autonomy | 6% (26 DISCRETIONARY_AUTONOMY) |
| Donor power | 5% (24 DONOR_RIGHT) |
| Preference signaling | 10% (46 GUIDED_DISCRETION — 32 strong, 14 soft) |
| Dominant domain | PROCUREMENT (63%) |
| UNCONDITIONAL dead ends | 49 |

**Character:** Procedural depth with embedded preference culture and the largest enforcement toolkit. PROCUREMENT dominates at 63% — AFD is fundamentally a procurement regulator. Highest DONOR_RIGHT count (24), dominated by INTERVENTION_RIGHT (13) — AFD reserves the right to direct procurement decisions, conduct prior and post reviews, and provide technical assistance that is effectively oversight. 46 GUIDED_DISCRETION clauses (32 strong) signal a governance style where institutional preferences are stated explicitly and repeatedly. INTEGRITY domain (39 clauses) signals deep institutional preoccupation with fraud and competition distortion.

---

## Summary Comparison — Donor Control Model

| Dimension | ECHO | GFFO | DOS | AFD |
|---|---|---|---|---|
| **Upfront control** (restriction rate) | Low | High | Very high | High |
| **Reserved control** (DONOR_RIGHT rate) | Very low | Medium | Very low | Medium |
| **Preference culture** (GUIDED_DISCRETION) | Minimal | None | Moderate | Rich |
| **NGO autonomy** (DISCRETIONARY_AUTONOMY rate) | High | Very low | Very low | Low |
| **Approval-gating** (CONDITIONAL_FLEXIBILITY) | None | None | Moderate | Low |
| **Primary instrument** | Standards | Mandates + revocation | Pharmaceutical rules | Procurement procedures |
| **Enforcement style** | Trust-based | Constitutional audit rights | Process-embedded | Discretionary intervention |
