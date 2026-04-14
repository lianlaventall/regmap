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

    tier_lines = []
    for tier_name, tier_data in tiers.items():
        words = ", ".join(tier_data["trigger_words"])
        tier_lines.append(f"- {tier_name}: {words}  ({tier_data['description']})")

    domain_lines = [f"- {k}: {v['description']}" for k, v in domains.items()]

    return f"""You are a compliance analyst extracting and classifying obligation clauses from donor agreement documents.

TAXONOMY
--------
Classify each clause into one of five tiers based on its modal language:

{chr(10).join(tier_lines)}
- QUALIFIED_RESTRICTION: A RESTRICTION trigger word is present but the clause is softened by a qualifying phrase (see QUALIFIERS below). Record the matched qualifier in the notes field.

BOUNDARY RULES
--------------
HIGH_RISK vs GUIDED_DISCRETION: Ask — does deviation from this clause create audit or enforcement risk? If yes → HIGH_RISK. If no, the donor is stating a preference with no enforcement attached → GUIDED_DISCRETION.
QUALIFIED_RESTRICTION vs GUIDED_DISCRETION: If a must/shall/required exists anywhere in the clause — even softened by "whenever possible" or "where advisable" — classify as QUALIFIED_RESTRICTION, not GUIDED_DISCRETION. A mandate anywhere in the clause means the obligation exists.

QUALIFIERS
----------
If a clause has a RESTRICTION trigger word AND contains one of these phrases, classify it as QUALIFIED_RESTRICTION instead of RESTRICTION:
{', '.join(qualifiers)}

CONTEXT PATTERNS
----------------
If a clause begins with one of these verbs (even without a modal word), set context_flag to true:
{', '.join(context_verbs)}

ACTOR CLASSIFICATION
--------------------
Set actor to "DONOR" when the clause describes an action by the granting authority, the Commission, or the donor itself.
Set actor to "NGO" for all other clauses (default).

DECISION SUB-TYPING
-------------------
When tier is DECISION, set decision_type to one of:
- DISCRETIONARY_AUTONOMY: actor is NGO, no approval required, no preference signal. Real NGO choice with no strings.
- CONDITIONAL_FLEXIBILITY: actor is NGO nominally, but the clause requires prior donor approval before the NGO may proceed. Look for "subject to [donor]'s prior agreement", "if an exception is approved", "with the agreement of", "provided [donor] agrees".
- DONOR_RESERVED: actor is DONOR. The donor retains a right to act or intervene. Look for "reserves the right to", "is entitled to", "may declare", "may suspend", "may revoke", "may require".
When tier is not DECISION, set decision_type to null.

NGO DEPENDENCY
--------------
Set creates_ngo_dependency to true when actor is "DONOR" and the NGO's ability to act or proceed is contingent on the donor completing that action first.
Set creates_ngo_dependency to false when the clause is purely internal donor process with no downstream impact on the NGO.
When actor is "NGO", always set creates_ngo_dependency to false.

GUIDED DISCRETION PREFERENCE SIGNAL
------------------------------------
When tier is GUIDED_DISCRETION, set preference_signal to a short phrase capturing what the donor prefers or recommends (e.g. "use standard bidding documents", "recruit a dedicated Tender Officer", "request a bid security for works contracts").
When tier is not GUIDED_DISCRETION, set preference_signal to null.

DEAD ENDS
---------
A dead end is a terminal restriction that stops a decision path rather than redirecting it.
If the clause contains any of these signals, set dead_end to true:
{', '.join(dead_end_signals)}

When dead_end is true, also set dead_end_type:
- UNCONDITIONAL: applies regardless of any upstream decision (no "if", "when", or conditional framing)
- CONDITIONAL: reachable only via a specific decision branch (contains "if", "when", "in case of", etc.)
- AMBIGUOUS: looks absolute but contains unresolved scope or undefined carve-outs; record the ambiguous phrase in notes

When dead_end is false, set dead_end_type to null.

DOMAINS
-------
Assign one primary domain that best describes what the clause is about:
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
  "tier": "<RESTRICTION|QUALIFIED_RESTRICTION|DECISION|HIGH_RISK|GUIDED_DISCRETION>",
  "context_flag": <true|false>,
  "actor": "<NGO|DONOR>",
  "decision_type": "<DISCRETIONARY_AUTONOMY|CONDITIONAL_FLEXIBILITY|DONOR_RESERVED|null>",
  "preference_signal": "<string|null>",
  "creates_ngo_dependency": <true|false>,
  "dead_end": <true|false>,
  "dead_end_type": "<UNCONDITIONAL|CONDITIONAL|AMBIGUOUS|null>",
  "domain": "<PROCUREMENT|REPORTING|RECORD_KEEPING|ELIGIBILITY_ACTOR|ELIGIBILITY_COMMODITY|ELIGIBILITY_ASSET|INTEGRITY|FINANCIAL|SAFEGUARDING|SCOPE>",
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
