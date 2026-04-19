# Taxonomy Overview — API Approach
### regmap · 2026-04-19

---

## The Obligation Ladder
*What the NGO must or may do — 4 tiers from most to least restrictive*

| Tier | Trigger Words | Meaning | Example |
|---|---|---|---|
| **RESTRICTION** | must · shall · will · required · binding | Mandatory. No choice, no flexibility. | "All vendors **must** be pre-approved before contract award." |
| **QUALIFIED_RESTRICTION** | must + softening phrase | Mandatory, but context can excuse non-compliance. | "Documentation **must** be submitted **where feasible**." |
| **GUIDED_DISCRETION (strong)** | should · ideally | Soft obligation. Donor expects this; may raise it in an audit. | "Procurement **should** follow competitive tendering principles." |
| **GUIDED_DISCRETION (soft)** | recommended · encouraged · advisable | Genuine preference on record. Deviation carries no enforcement risk. | "It **is recommended** to source from local suppliers." |
| **DECISION** | may · can | Permissive. No mandate, no preference. NGO or donor has explicit discretion. | "The implementing partner **may** select the procurement modality." |

---

## DECISION Sub-types
*Not all "may" clauses are equal*

| Sub-type | Who Really Decides | Example |
|---|---|---|
| **DISCRETIONARY_AUTONOMY** | NGO — genuinely free | "The NGO **may** choose between direct and indirect implementation." |
| **CONDITIONAL_FLEXIBILITY** | Donor — approval required first | "The NGO **may** proceed, **subject to AFD's prior agreement**." |

---

## Donor Power
*Separate axis — what the donor can do to the NGO*

| Sub-type | Meaning | Example |
|---|---|---|
| **AUDIT_RIGHT** | Donor may inspect records or operations | "The Federal Court of Audit **is entitled to** inspect the grant recipient's accounts." |
| **SUSPENSION_RIGHT** | Donor may halt disbursements | "AFD **reserves the right to suspend** disbursements in the event of a material breach." |
| **TERMINATION_RIGHT** | Donor may revoke the grant | "The Agency **may revoke** the grant if conditions are not met." |
| **INTERVENTION_RIGHT** | Donor may intervene in operations | "AFD **may require** replacement of key personnel." |

> These clauses describe donor power, not NGO obligation. They sit outside the tier ladder entirely.

---

## Qualifiers
*Phrases that soften a mandatory clause*

| Qualifier | Effect |
|---|---|
| where possible · where feasible · where appropriate | RESTRICTION → QUALIFIED_RESTRICTION |
| as far as possible · to the extent possible | RESTRICTION → QUALIFIED_RESTRICTION |
| if applicable · unless otherwise specified · subject to availability | RESTRICTION → QUALIFIED_RESTRICTION |

---

## Dead Ends
*Among RESTRICTION clauses — which are absolute?*

| Type | Meaning | Pooling? | Example |
|---|---|---|---|
| **UNCONDITIONAL** | No conditional language in clause. Applies regardless of upstream decisions. | Candidate — requires human verification | "Sanctioned entities are **not permitted** to participate." |
| **CONDITIONAL** | Fires only under a specific condition. | Never — permanent exclusion | "If direct procurement applies, local suppliers **must not** be bypassed." |
| **AMBIGUOUS** | Absolute-looking but contains undefined carve-outs. | Never — until resolved | "Prohibited **except in exceptional circumstances**." |

> Goal: identify UNCONDITIONAL restrictions shared across donors → cross-donor compliance baseline

---

## Domains
*What the clause is about*

| Domain | Covers | Dominant Donor |
|---|---|---|
| **PROCUREMENT** | Sourcing, vendor selection, purchasing rules | AFD (57%) · DOS (36%) |
| **REPORTING** | Data submissions, notifications, reports | GFFO (44%) |
| **RECORD_KEEPING** | Retention, documentation, audit trail | All donors, low density |
| **ELIGIBILITY_ACTOR** | Who can participate — sanctions, debarment, nationality | AFD |
| **ELIGIBILITY_COMMODITY** | What can be procured — drug restrictions, quality floors | DOS |
| **ELIGIBILITY_ASSET** | How funded assets can be used — binding periods, repurposing | GFFO |
| **INTEGRITY** | Fraud prevention, conflict of interest, anti-corruption | AFD (~30 clauses) |
| **FINANCIAL** | Budget, spend, reimbursement, audit rules | GFFO (33%) |
| **SAFEGUARDING** | Protection of beneficiaries, staff, or data | DOS only |

> INTEGRITY clause density = proxy for donor risk culture. High count signals institutional distrust of implementers.

---

## Full Picture — One Clause, All Fields

**Source text:**
> "We shall make our contractual rights available to AFD, for the purposes that AFD or the auditors appointed by it may conduct the necessary verifications."

| Field | Value |
|---|---|
| `tier` | RESTRICTION |
| `domain` | FINANCIAL |
| `actor` | NGO |
| `dead_end` | false |
| `contains_donor_right` | true |
| `donor_right_type` | AUDIT_RIGHT |
| `decision_type` | null |
| `preference_signal` | null |
| `preference_strength` | null |
| `creates_ngo_dependency` | false |
| `notes` | "" |
