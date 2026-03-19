import os
import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

TAXONOMY_PATH = Path(__file__).parent.parent / "config" / "taxonomy.yaml"


def _load_taxonomy() -> dict:
    with open(TAXONOMY_PATH) as f:
        return yaml.safe_load(f)


def _build_system_prompt(taxonomy: dict) -> str:
    tiers = taxonomy["tiers"]
    context_verbs = taxonomy["context_patterns"]["verbs"]

    tier_lines = []
    for tier_name, tier_data in tiers.items():
        words = ", ".join(tier_data["trigger_words"])
        tier_lines.append(f"- {tier_name}: {words}  ({tier_data['description']})")

    return f"""You are a compliance analyst extracting and classifying obligation clauses from donor agreement documents.

TAXONOMY
--------
Classify each clause into one of three tiers based on its modal language:

{chr(10).join(tier_lines)}

CONTEXT PATTERNS
----------------
If a clause begins with one of these verbs (even without a modal word), set context_flag to true:
{', '.join(context_verbs)}

INSTRUCTIONS
------------
1. Read each page of text provided by the user.
2. Identify every sentence or clause that contains a trigger word or context pattern verb.
3. For each clause, extract:
   - The full sentence (text)
   - The 1-based page number (page)
   - The trigger word or context verb (trigger_word)
   - The tier: RESTRICTION, DECISION, or HIGH_RISK
   - context_flag: true if triggered by a context_pattern verb, false otherwise
   - notes: any ambiguity or analyst note (empty string if none)
4. Return ONLY a valid JSON array of clause objects. No markdown, no explanation.

JSON shape for each clause (do not include clause_id — it will be added later):
{{
  "text": "<full sentence>",
  "page": <int>,
  "trigger_word": "<word>",
  "tier": "<RESTRICTION|DECISION|HIGH_RISK>",
  "context_flag": <true|false>,
  "notes": "<string>"
}}"""


def classify(pages: list[dict], donor: str, filename: str) -> dict:
    """Send extracted page text to Claude and return a structured output dict.

    Args:
        pages: list of dicts with keys page_num, text, needs_ocr
        donor: donor/funder identifier (e.g. "ECHO")
        filename: original PDF filename

    Returns:
        dict matching output_schema.json
    """
    taxonomy = _load_taxonomy()
    system_prompt = _build_system_prompt(taxonomy)

    # Build the user message: one block per page
    page_blocks = []
    for p in pages:
        if p["text"].strip():
            page_blocks.append(f"--- PAGE {p['page_num']} ---\n{p['text']}")

    user_message = "\n\n".join(page_blocks) if page_blocks else "(no text extracted)"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if Claude wrapped the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    clauses_raw: list[dict] = json.loads(raw)

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
