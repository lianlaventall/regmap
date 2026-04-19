import os
import json
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from anthropic import Anthropic, RateLimitError

TAXONOMY_PATH = Path(__file__).parent.parent / "config" / "taxonomy.yaml"


def _load_taxonomy() -> dict:
    with open(TAXONOMY_PATH) as f:
        return yaml.safe_load(f)


def _build_system_prompt(taxonomy: dict) -> str:
    tiers = taxonomy["tiers"]
    context_verbs = taxonomy["context_patterns"]["verbs"]
    qualifiers = taxonomy["qualifiers"]["phrases"]
    dead_end_signals = taxonomy["dead_ends"]["signals"]["phrases"]
    domains = taxonomy["domains"]["values"]

    domain_lines = [f"- {k}: {v['description']}" for k, v in domains.items()]

    return f"""You are a compliance analyst extracting and classifying obligation clauses from donor agreement documents.

TAXONOMY — NGO OBLIGATION LADDER
---------------------------------
Classify each NGO-facing clause into one of four tiers:

- RESTRICTION: Mandatory obligation. Trigger words: must, will, shall, required, binding, obliged, mandatory.
- QUALIFIED_RESTRICTION: A RESTRICTION trigger word is present but softened by a qualifying phrase (see QUALIFIERS). The obligation still exists. Record the matched qualifier in notes.
- GUIDED_DISCRETION: Non-mandatory language where the donor has stated a preference. NGO has genuine discretion — no mandate, no prior approval required. Two strengths:
    strong — trigger words: should, ideally. Soft obligation; audit-adjacent. Donor expects this behavior and may raise it in a review.
    soft — trigger words: recommended, suggested, encouraged, strongly encouraged, it is recommended, it is advisable, is advised, it is good practice, it is helpful. Genuine preference; deviation carries no direct enforcement risk.
  Set preference_strength accordingly. Set preference_signal to the substance of what the donor prefers.
- DECISION: Permissive language, no preference stated. Trigger words: may, can. Set decision_type to one of:
    DISCRETIONARY_AUTONOMY — NGO actor, no approval required. Real NGO choice, no strings.
    CONDITIONAL_FLEXIBILITY — NGO actor nominally, but prior donor approval is required before NGO may proceed. Look for "subject to [donor]'s prior agreement", "if an exception is approved", "with the agreement of".
    null — when tier is not DECISION.

DONOR POWER — SEPARATE AXIS
-----------------------------
DONOR_RIGHT is NOT part of the NGO obligation ladder. Use it when the entire clause describes a power the donor holds over the NGO or the agreement. The NGO is the object, not an actor.

Set tier to DONOR_RIGHT and set donor_right_type to one of:
- AUDIT_RIGHT — donor or third party entitled to inspect, examine, or investigate records, accounts, or operations. Look for: "entitled to inspect", "may conduct investigations", "auditors appointed by", "right to examine".
- SUSPENSION_RIGHT — donor may halt or pause disbursements or the agreement. Look for: "may suspend", "reserves the right to suspend", "may withhold".
- TERMINATION_RIGHT — donor may revoke, terminate, or cancel the grant. Look for: "may revoke", "may terminate", "reserves the right to revoke".
- INTERVENTION_RIGHT — donor may intervene in operations, staffing, or procurement. Look for: "may require replacement of", "may direct", "may require the Contracting Authority to".

MIXED CLAUSES (NGO obligation + embedded donor power)
------------------------------------------------------
When a single clause contains both an NGO obligation AND donor power language, classify by the primary NGO-facing obligation tier. Then set:
- contains_donor_right: true
- donor_right_type: the appropriate DONOR_RIGHT sub-type embedded in the clause

QUALIFIERS
----------
If a clause has a RESTRICTION trigger word AND contains one of these phrases, classify as QUALIFIED_RESTRICTION:
{', '.join(qualifiers)}

CONTEXT PATTERNS
----------------
If a clause begins with one of these verbs (even without a modal word), set context_flag to true:
{', '.join(context_verbs)}

ACTOR CLASSIFICATION
--------------------
Set actor to "DONOR" when the clause describes an action by the granting authority, the Commission, or the donor itself.
Set actor to "NGO" for all other clauses (default).

NGO DEPENDENCY
--------------
Set creates_ngo_dependency to true when the NGO's ability to act or proceed is contingent on the donor completing an action first.
Set creates_ngo_dependency to false otherwise.

DEAD ENDS — RESTRICTION AND QUALIFIED_RESTRICTION ONLY
-------------------------------------------------------
Dead ends apply only to RESTRICTION and QUALIFIED_RESTRICTION clauses. Always set dead_end to false for GUIDED_DISCRETION, DECISION, and DONOR_RIGHT.

If a RESTRICTION or QUALIFIED_RESTRICTION clause contains any of these signals, set dead_end to true:
{', '.join(dead_end_signals)}

When dead_end is true, set dead_end_type:
- UNCONDITIONAL: no conditional language visible in the clause (no if/when/provided that). Pooling candidate — applies regardless of any upstream decision.
- CONDITIONAL: conditional language visible in the clause (if, when, provided that, in cases where). Fires only on a specific branch. Permanent pooling exclusion.
- AMBIGUOUS: genuine unresolved legal carve-out in the clause text (e.g. "prohibited except in exceptional circumstances" where exceptional is undefined). Record the ambiguous phrase in notes. Excluded from pooling.

When dead_end is false, set dead_end_type to null.

DOMAINS
-------
Assign one primary domain:
{chr(10).join(domain_lines)}

INSTRUCTIONS
------------
1. Read each page of text provided by the user.
2. Identify every sentence or clause that contains a trigger word or context pattern verb.
3. For each clause, extract all fields below.
4. Return ONLY a valid JSON array of clause objects. No markdown, no explanation.

JSON shape for each clause (do not include clause_id — it will be added later):
{{
  "text": "<full sentence>",
  "page": <int>,
  "trigger_word": "<word>",
  "tier": "<RESTRICTION|QUALIFIED_RESTRICTION|GUIDED_DISCRETION|DECISION|DONOR_RIGHT>",
  "context_flag": <true|false>,
  "actor": "<NGO|DONOR>",
  "decision_type": "<DISCRETIONARY_AUTONOMY|CONDITIONAL_FLEXIBILITY|null>",
  "donor_right_type": "<AUDIT_RIGHT|SUSPENSION_RIGHT|TERMINATION_RIGHT|INTERVENTION_RIGHT|null>",
  "contains_donor_right": <true|false>,
  "preference_signal": "<string|null>",
  "preference_strength": "<strong|soft|null>",
  "creates_ngo_dependency": <true|false>,
  "dead_end": <true|false>,
  "dead_end_type": "<UNCONDITIONAL|CONDITIONAL|AMBIGUOUS|null>",
  "domain": "<PROCUREMENT|REPORTING|RECORD_KEEPING|ELIGIBILITY_ACTOR|ELIGIBILITY_COMMODITY|ELIGIBILITY_ASSET|INTEGRITY|FINANCIAL|SAFEGUARDING>",
  "notes": "<string>"
}}"""


BATCH_SIZE = 5   # pages per API call
MAX_RETRIES = 4  # retries on rate limit (exponential backoff)


def _call_claude(client: Anthropic, system_prompt: str, page_blocks: list[str]) -> list[dict]:
    user_message = "\n\n".join(page_blocks) if page_blocks else "(no text extracted)"
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=16384,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            return json.loads(raw)
        except RateLimitError:
            wait = 60 * (attempt + 1)
            print(f"    Rate limit — waiting {wait}s (retry {attempt + 1}/{MAX_RETRIES})...")
            time.sleep(wait)
        except json.JSONDecodeError:
            wait = 10 * (attempt + 1)
            print(f"    Malformed JSON — waiting {wait}s and retrying (retry {attempt + 1}/{MAX_RETRIES})...")
            time.sleep(wait)
        if attempt == MAX_RETRIES - 1:
            raise RuntimeError(f"Failed to get valid response after {MAX_RETRIES} attempts")


def classify(pages: list[dict], donor: str, filename: str) -> dict:
    """Send extracted page text to Claude and return a structured output dict.

    Args:
        pages: list of dicts with keys page_num, text, needs_ocr
        donor: donor/funder identifier (e.g. "ECHO")
        filename: original PDF filename

    Returns:
        dict matching output_schema.json
    """
    client = Anthropic()
    taxonomy = _load_taxonomy()
    system_prompt = _build_system_prompt(taxonomy)

    # Build one block per non-empty page
    page_blocks = [
        f"--- PAGE {p['page_num']} ---\n{p['text']}"
        for p in pages
        if p["text"].strip()
    ]

    # Process in batches to handle large documents
    clauses_raw = []
    n_batches = -(-len(page_blocks) // BATCH_SIZE)
    for i in range(0, len(page_blocks), BATCH_SIZE):
        batch = page_blocks[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Classifying pages batch {batch_num}/{n_batches}...")
        clauses_raw.extend(_call_claude(client, system_prompt, batch))

    # Assign clause IDs
    clauses = []
    for idx, clause in enumerate(clauses_raw, start=1):
        clause["clause_id"] = f"{donor}-{idx:03d}"
        clauses.append(clause)

    return {
        "donor": donor,
        "document": filename,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "pages_processed": len(pages),
        "clauses": clauses,
    }
