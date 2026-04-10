"""
report.py — Structured analytical report from classified donor obligation data.

Asks 7 analytical questions of the corpus and writes findings to
reports/analysis_<YYYY-MM-DD>.md.

Usage:
    python -m src.report
"""

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

OUTPUT_DIR = Path("output")
REPORTS_DIR = Path("reports")

TIERS = ["RESTRICTION", "QUALIFIED_RESTRICTION", "HIGH_RISK", "DECISION"]
DOMAIN_ORDER = [
    "PROCUREMENT", "ELIGIBILITY", "REPORTING",
    "FINANCIAL", "RECORD_KEEPING", "SAFEGUARDING", "SCOPE",
]
DEAD_END_TYPES = ["UNCONDITIONAL", "CONDITIONAL", "AMBIGUOUS"]


# ── data loading ──────────────────────────────────────────────────────────────

def load_donor_data() -> dict[str, dict]:
    """Returns {donor_name: raw_doc_dict} for all output JSONs except flow_data."""
    donors = {}
    for path in sorted(OUTPUT_DIR.glob("*.json")):
        if path.name == "flow_data.json":
            continue
        raw = json.loads(path.read_text())
        donors[raw["donor"]] = raw
    return donors


# ── section helpers ───────────────────────────────────────────────────────────

def pct(n: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{n / total * 100:.1f}%"


def md_table(headers: list[str], rows: list[list]) -> str:
    widths = [len(h) for h in headers]
    str_rows = [[str(c) for c in row] for row in rows]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    header_line = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    lines = [header_line, sep]
    for row in str_rows:
        lines.append("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |")
    return "\n".join(lines)


def clause_bullet(clause: dict, include_notes: bool = False) -> str:
    cid = clause.get("clause_id", "")
    domain = clause.get("domain", "")
    tier = clause.get("tier", "")
    text = (clause.get("text") or "").strip()
    notes = (clause.get("notes") or "").strip()
    line = f"- **{cid}** `{domain}` `{tier}`  \n  > {text}"
    if include_notes and notes:
        line += f"  \n  *{notes}*"
    return line


# ── section 1: compliance burden profile ─────────────────────────────────────

def section_compliance_burden(donors: dict) -> tuple[str, list[str]]:
    rows = []
    tier_pcts = defaultdict(dict)
    for donor, doc in sorted(donors.items()):
        clauses = doc["clauses"]
        total = len(clauses)
        tier_counts = Counter(c.get("tier") for c in clauses)
        row = [donor, str(total)]
        for t in TIERS:
            n = tier_counts.get(t, 0)
            row.append(f"{n} ({pct(n, total)})")
            tier_pcts[donor][t] = n / total * 100 if total else 0
        rows.append(row)

    table = md_table(
        ["Donor", "Total"] + [t.replace("_", " ") for t in TIERS],
        rows,
    )

    # most restrictive = highest RESTRICTION %
    most_restrictive = max(donors, key=lambda d: tier_pcts[d].get("RESTRICTION", 0))
    most_decision = max(donors, key=lambda d: tier_pcts[d].get("DECISION", 0))

    # domain driving restriction for most_restrictive donor
    restr_clauses = [c for c in donors[most_restrictive]["clauses"] if c.get("tier") == "RESTRICTION"]
    domain_driver = Counter(c.get("domain") for c in restr_clauses).most_common(1)
    driver_str = f"{domain_driver[0][0]} ({domain_driver[0][1]} clauses)" if domain_driver else "unknown"

    finding = (
        f"**{most_restrictive}** is the most restrictive donor "
        f"({tier_pcts[most_restrictive]['RESTRICTION']:.1f}% RESTRICTION), "
        f"driven by {driver_str}. "
        f"**{most_decision}** has the highest DECISION share "
        f"({tier_pcts[most_decision]['DECISION']:.1f}%), offering the most apparent flexibility."
    )

    summary = [
        f"Compliance burden: {most_restrictive} most restrictive "
        f"({tier_pcts[most_restrictive]['RESTRICTION']:.1f}% RESTRICTION)"
    ]

    md = f"""## 1. Compliance Burden Profile

{table}

**Key finding:** {finding}
"""
    return md, summary


# ── section 2: domain burden per donor ───────────────────────────────────────

def section_domain_burden(donors: dict) -> tuple[str, list[str]]:
    all_domains = sorted(
        set(c.get("domain") for doc in donors.values() for c in doc["clauses"] if c.get("domain")),
        key=lambda d: DOMAIN_ORDER.index(d) if d in DOMAIN_ORDER else 99,
    )
    donor_list = sorted(donors.keys())

    rows = []
    for domain in all_domains:
        row = [domain]
        for donor in donor_list:
            clauses = [c for c in donors[donor]["clauses"] if c.get("domain") == domain]
            total_donor = len(donors[donor]["clauses"])
            n = len(clauses)
            if n == 0:
                row.append("—")
                continue
            tier_counts = Counter(c.get("tier") for c in clauses)
            breakdown = " / ".join(
                f"{tier_counts[t]}R" if t == "RESTRICTION" else
                f"{tier_counts[t]}QR" if t == "QUALIFIED_RESTRICTION" else
                f"{tier_counts[t]}HR" if t == "HIGH_RISK" else
                f"{tier_counts[t]}D"
                for t in TIERS if tier_counts.get(t, 0) > 0
            )
            row.append(f"{n} ({pct(n, total_donor)}) [{breakdown}]")
        rows.append(row)

    table = md_table(["Domain"] + donor_list, rows)

    # identify heaviest domain per donor
    highlights = []
    for donor in donor_list:
        clauses = donors[donor]["clauses"]
        domain_counts = Counter(c.get("domain") for c in clauses if c.get("domain"))
        if domain_counts:
            top = domain_counts.most_common(1)[0]
            highlights.append(f"**{donor}**: {top[0]} is heaviest ({top[1]} clauses, {pct(top[1], len(clauses))})")

    finding = "; ".join(highlights) + "."

    summary = [f"Domain burden: " + "; ".join(highlights)]

    md = f"""## 2. Domain Burden per Donor

Tier codes: R=RESTRICTION, QR=QUALIFIED_RESTRICTION, HR=HIGH_RISK, D=DECISION

{table}

**Key finding:** {finding}
"""
    return md, summary


# ── section 3: actor split ────────────────────────────────────────────────────

def section_actor_split(donors: dict) -> tuple[str, list[str]]:
    rows = []
    for donor in sorted(donors.keys()):
        clauses = donors[donor]["clauses"]
        total = len(clauses)
        actor_counts = Counter(c.get("actor") for c in clauses)
        ngo = actor_counts.get("NGO", 0)
        donor_actor = actor_counts.get("DONOR", 0)
        other = total - ngo - donor_actor
        rows.append([
            donor,
            str(total),
            f"{ngo} ({pct(ngo, total)})",
            f"{donor_actor} ({pct(donor_actor, total)})",
            str(other) if other else "0",
        ])

    table = md_table(
        ["Donor", "Total", "NGO obligations", "Donor obligations", "Other/None"],
        rows,
    )

    # most donor-obligating
    most_self = max(
        sorted(donors.keys()),
        key=lambda d: Counter(c.get("actor") for c in donors[d]["clauses"]).get("DONOR", 0)
        / len(donors[d]["clauses"]) if donors[d]["clauses"] else 0,
    )
    self_n = Counter(c.get("actor") for c in donors[most_self]["clauses"]).get("DONOR", 0)
    self_total = len(donors[most_self]["clauses"])

    finding = (
        f"The vast majority of obligations across all donors fall on the NGO implementer. "
        f"**{most_self}** places the most obligations on itself "
        f"({self_n} clauses, {pct(self_n, self_total)} of its corpus) — "
        f"these represent procedural donor commitments (approval, review) rather than implementer requirements."
    )

    summary = [f"Actor split: NGO-heavy across all donors; {most_self} has most DONOR obligations"]

    md = f"""## 3. Actor Split — Who Bears the Obligation?

{table}

**Key finding:** {finding}
"""
    return md, summary


# ── section 4: NGO dependency map ────────────────────────────────────────────

def section_ngo_dependency(donors: dict) -> tuple[str, list[str]]:
    all_deps = []
    for donor in sorted(donors.keys()):
        for c in donors[donor]["clauses"]:
            if c.get("creates_ngo_dependency"):
                all_deps.append((donor, c))

    bullets = [clause_bullet(c, include_notes=True) + f" *(donor: {d})*" for d, c in all_deps]
    count = len(all_deps)

    by_donor = Counter(d for d, _ in all_deps)
    donor_summary = ", ".join(f"{d}: {n}" for d, n in sorted(by_donor.items()))

    finding = (
        f"**{count} clauses** create NGO dependency — where implementer progress is blocked "
        f"pending a donor action ({donor_summary}). "
        f"These are operational bottlenecks and should be tracked in project workplans."
    )

    summary = [f"NGO dependencies: {count} blocking clauses ({donor_summary})"]

    body = "\n".join(bullets) if bullets else "_No NGO dependency clauses found._"

    md = f"""## 4. NGO Dependency Map

NGO dependency clauses — where implementer action requires prior donor approval or response:

{body}

**Key finding:** {finding}
"""
    return md, summary


# ── section 5: dead-end profile ───────────────────────────────────────────────

def section_dead_ends(donors: dict) -> tuple[str, list[str]]:
    rows = []
    for donor in sorted(donors.keys()):
        clauses = donors[donor]["clauses"]
        total = len(clauses)
        de_counts = Counter(c.get("dead_end_type") for c in clauses if c.get("dead_end"))
        row = [donor]
        for de in DEAD_END_TYPES:
            n = de_counts.get(de, 0)
            row.append(f"{n} ({pct(n, total)})")
        rows.append(row)

    table = md_table(["Donor"] + DEAD_END_TYPES, rows)

    # cross-donor UNCONDITIONAL domains
    unconditional_domains = defaultdict(set)
    for donor in donors:
        for c in donors[donor]["clauses"]:
            if c.get("dead_end_type") == "UNCONDITIONAL":
                unconditional_domains[c.get("domain", "UNKNOWN")].add(donor)
    shared = {d: ds for d, ds in unconditional_domains.items() if len(ds) == len(donors)}
    shared_str = (
        ", ".join(sorted(shared.keys())) if shared
        else "No domain has UNCONDITIONAL dead ends across all donors"
    )

    # AMBIGUOUS clauses for audit
    ambiguous = []
    for donor in sorted(donors.keys()):
        for c in donors[donor]["clauses"]:
            if c.get("dead_end_type") == "AMBIGUOUS":
                ambiguous.append((donor, c))

    ambig_bullets = [clause_bullet(c) + f" *(donor: {d})*" for d, c in ambiguous]
    ambig_body = "\n".join(ambig_bullets) if ambig_bullets else "_None._"

    finding = (
        f"**Shared UNCONDITIONAL domains (all donors):** {shared_str}. "
        f"**{len(ambiguous)} AMBIGUOUS clauses** flagged for human audit — "
        f"the obligation conditions are unclear and may require legal review."
    )

    summary = [
        f"Dead-ends: {len(ambiguous)} AMBIGUOUS clauses need audit; shared UNCONDITIONAL: {shared_str}"
    ]

    md = f"""## 5. Dead-End Profile

{table}

### AMBIGUOUS clauses flagged for human audit

{ambig_body}

**Key finding:** {finding}
"""
    return md, summary


# ── section 6: DECISION clause inventory ─────────────────────────────────────

def section_decision_inventory(donors: dict) -> tuple[str, list[str]]:
    parts = []
    total_decision = 0
    for donor in sorted(donors.keys()):
        decision_clauses = [c for c in donors[donor]["clauses"] if c.get("tier") == "DECISION"]
        total_decision += len(decision_clauses)
        if not decision_clauses:
            parts.append(f"### {donor}\n\n_No DECISION clauses._\n")
            continue
        bullets = [clause_bullet(c, include_notes=True) for c in decision_clauses]
        parts.append(f"### {donor}\n\n" + "\n".join(bullets) + "\n")

    body = "\n".join(parts)

    finding = (
        f"**{total_decision} DECISION clauses** across the corpus. "
        "Review notes carefully — 'DECISION' indicates the classifier found "
        "explicit flexibility language, but the character varies: "
        "some are genuine implementer autonomy, others are donor-reserved rights "
        "or conditional grants of discretion."
    )

    summary = [f"DECISION inventory: {total_decision} total DECISION clauses across all donors"]

    md = f"""## 6. DECISION Clause Inventory

{body}

**Key finding:** {finding}
"""
    return md, summary


# ── section 7: context flag patterns ─────────────────────────────────────────

def section_context_flags(donors: dict) -> tuple[str, list[str]]:
    all_clauses = [
        (donor, c)
        for donor in donors
        for c in donors[donor]["clauses"]
    ]

    # trigger word frequency
    trigger_counts = Counter(
        c.get("trigger_word", "").strip().lower()
        for _, c in all_clauses
        if c.get("trigger_word")
    )
    top_triggers = trigger_counts.most_common(15)

    trigger_rows = [[w, str(n)] for w, n in top_triggers if w]
    trigger_table = md_table(["Trigger word", "Count"], trigger_rows)

    # context_flag clauses by domain
    context_flag_clauses = [(donor, c) for donor, c in all_clauses if c.get("context_flag")]
    cf_by_domain = Counter(c.get("domain", "UNKNOWN") for _, c in context_flag_clauses)
    cf_domain_rows = sorted(
        [[d, str(n)] for d, n in cf_by_domain.items()],
        key=lambda r: int(r[1]), reverse=True,
    )
    cf_table = md_table(["Domain", "context_flag count"], cf_domain_rows) if cf_domain_rows else "_None._"

    total_cf = len(context_flag_clauses)
    total_all = len(all_clauses)
    top_word = top_triggers[0][0] if top_triggers else "N/A"

    finding = (
        f"**'{top_word}'** is the most common trigger word across all donors. "
        f"**{total_cf} clauses** ({pct(total_cf, total_all)} of corpus) carry a `context_flag`, "
        f"indicating verb-first obligation framing that may signal higher compliance risk. "
        f"These cluster in the domains shown above."
    )

    summary = [
        f"Context flags: {total_cf} flagged clauses; top trigger word: '{top_word}'"
    ]

    md = f"""## 7. Context Flag Patterns

### Top trigger words (across all donors)

{trigger_table}

### context_flag clauses by domain

{cf_table}

**Key finding:** {finding}
"""
    return md, summary


# ── main ──────────────────────────────────────────────────────────────────────

def build_report() -> Path:
    donors = load_donor_data()
    donor_names = sorted(donors.keys())
    total_clauses = sum(len(d["clauses"]) for d in donors.values())
    today = date.today().isoformat()

    print(f"Loaded {len(donors)} donors: {', '.join(donor_names)}")
    print(f"Total clauses: {total_clauses}")
    print()

    sections = [
        section_compliance_burden,
        section_domain_burden,
        section_actor_split,
        section_ngo_dependency,
        section_dead_ends,
        section_decision_inventory,
        section_context_flags,
    ]

    section_mds = []
    all_summaries = []
    section_names = [
        "Compliance Burden Profile",
        "Domain Burden per Donor",
        "Actor Split",
        "NGO Dependency Map",
        "Dead-End Profile",
        "DECISION Clause Inventory",
        "Context Flag Patterns",
    ]

    for i, (fn, name) in enumerate(zip(sections, section_names), 1):
        md, summary = fn(donors)
        section_mds.append(md)
        all_summaries.extend(summary)
        print(f"  [{i}/7] {name}")

    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / f"analysis_{today}.md"

    header = f"""# Donor Obligation Analysis — {today}

**Corpus:** {', '.join(donor_names)} · {total_clauses} classified clauses

---

"""

    report = header + "\n---\n\n".join(section_mds)
    out_path.write_text(report)

    print()
    print("Key findings:")
    for s in all_summaries:
        print(f"  - {s}")
    print()
    print(f"Written: {out_path}")
    return out_path


if __name__ == "__main__":
    build_report()
