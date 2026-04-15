"""
scorecard.py — Donor compliance scorecard.

A color-coded table showing key metrics per donor.
Rows = metrics, Columns = donors.

Output: output/scorecard.html
"""

import json
from pathlib import Path
from collections import Counter

import plotly.graph_objects as go

OUTPUT_DIR  = Path("output")
SCORECARD_PATH = OUTPUT_DIR / "scorecard.html"

ALL_DOMAINS = [
    "PROCUREMENT", "ELIGIBILITY_ACTOR", "ELIGIBILITY_COMMODITY", "ELIGIBILITY_ASSET",
    "INTEGRITY", "REPORTING", "FINANCIAL", "RECORD_KEEPING", "SAFEGUARDING", "SCOPE"
]
OBLIGATION_TIERS = {"RESTRICTION", "QUALIFIED_RESTRICTION", "HIGH_RISK"}
DONOR_COLORS = {
    "DOS":  "#1abc9c",
    "ECHO": "#e67e22",
    "GFFO": "#9b59b6",
    "AFD":  "#f39c12",
}
DONOR_ORDER = ["DOS", "ECHO", "GFFO", "AFD"]


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _scale_color(value: float, low_color: str, high_color: str) -> str:
    """Interpolate between two hex colors based on a 0–100 value."""
    t = max(0.0, min(1.0, value / 100))
    r1, g1, b1 = int(low_color[1:3],16), int(low_color[3:5],16), int(low_color[5:7],16)
    r2, g2, b2 = int(high_color[1:3],16), int(high_color[3:5],16), int(high_color[5:7],16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"rgba({r},{g},{b},0.55)"


GREEN  = "#27ae60"
RED    = "#c0392b"
AMBER  = "#f39c12"
BLUE   = "#2980b9"
PURPLE = "#8e44ad"
NEUTRAL = "#1a1d27"


def compute_metrics(clauses: list[dict]) -> dict:
    n = len(clauses)
    if n == 0:
        return {}

    obligation    = sum(1 for c in clauses if c.get("tier") in OBLIGATION_TIERS)
    restriction   = sum(1 for c in clauses if c.get("tier") == "RESTRICTION")
    autonomy      = sum(1 for c in clauses if c.get("decision_type") == "DISCRETIONARY_AUTONOMY")
    guided        = sum(1 for c in clauses if c.get("tier") == "GUIDED_DISCRETION")
    integrity     = sum(1 for c in clauses if c.get("domain") == "INTEGRITY")
    ngo_deps      = sum(1 for c in clauses if c.get("creates_ngo_dependency"))

    domains_covered = len({c.get("domain") for c in clauses if c.get("domain")})

    decision_clauses = [c for c in clauses if c.get("tier") == "DECISION"]
    n_decision = len(decision_clauses)
    gated = sum(
        1 for c in decision_clauses
        if c.get("decision_type") in {"CONDITIONAL_FLEXIBILITY", "DONOR_RESERVED"}
    )
    approval_gating = round(gated / n_decision * 100, 1) if n_decision > 0 else 0.0

    domain_counts = Counter(c.get("domain") for c in clauses if c.get("domain"))
    top_domain = domain_counts.most_common(1)[0][0].replace("_", "<br>") if domain_counts else "—"

    return {
        "total":            n,
        "obligation_rate":  round(obligation  / n * 100, 1),
        "restriction_rate": round(restriction / n * 100, 1),
        "autonomy_rate":    round(autonomy    / n * 100, 1),
        "guided_rate":      round(guided      / n * 100, 1),
        "integrity_rate":   round(integrity   / n * 100, 1),
        "domain_breadth":   domains_covered,
        "approval_gating":  approval_gating,
        "ngo_deps":         ngo_deps,
        "top_domain":       top_domain,
    }


# Metric definitions: (label, key, format_fn, color_fn)
# color_fn receives the value and returns a cell bg color string
def _pct(v):    return f"{v}%"
def _count(v):  return str(v)
def _text(v):   return str(v)

METRICS = [
    # (row label, key, format, color function)
    ("Total Clauses",          "total",            _count,
     lambda v, _: NEUTRAL),

    ("Obligation Rate",        "obligation_rate",  _pct,
     lambda v, vals: _scale_color(v, GREEN, RED)),

    ("Hard Restriction Rate",  "restriction_rate", _pct,
     lambda v, vals: _scale_color(v, GREEN, RED)),

    ("Real NGO Autonomy",      "autonomy_rate",    _pct,
     lambda v, vals: _scale_color(v, RED, GREEN)),

    ("Preference Signaling",   "guided_rate",      _pct,
     lambda v, vals: _scale_color(v, NEUTRAL, AMBER)),

    ("INTEGRITY Density",      "integrity_rate",   _pct,
     lambda v, vals: _scale_color(v, NEUTRAL, AMBER)),

    ("Domain Breadth",         "domain_breadth",   lambda v: f"{v} / {len(ALL_DOMAINS)}",
     lambda v, vals: _scale_color(v / len(ALL_DOMAINS) * 100, NEUTRAL, BLUE)),

    ("Approval Gating",        "approval_gating",  _pct,
     lambda v, vals: _scale_color(v, GREEN, RED)),

    ("NGO Dependencies",       "ngo_deps",         _count,
     lambda v, vals: _scale_color(
         v / max(vals) * 100 if max(vals) > 0 else 0, NEUTRAL, AMBER)),

    ("Top Domain",             "top_domain",       _text,
     lambda v, _: NEUTRAL),
]


def build_scorecard() -> go.Figure:
    # Load donors in order
    donor_data = {}
    for path in sorted(OUTPUT_DIR.glob("*.json")):
        if path.name == "flow_data.json":
            continue
        raw = json.loads(path.read_text())
        donor_data[raw["donor"]] = compute_metrics(raw["clauses"])

    donors = [d for d in DONOR_ORDER if d in donor_data]

    # Build table data
    row_labels  = []
    cell_values = [[] for _ in donors]   # one list per donor column
    cell_colors = [[] for _ in donors]

    for label, key, fmt, color_fn in METRICS:
        row_labels.append(f"<b>{label}</b>")
        raw_vals = [donor_data[d].get(key, 0) for d in donors]
        # numeric values for color scaling comparisons
        numeric = [v for v in raw_vals if isinstance(v, (int, float))]

        for i, (donor, raw_val) in enumerate(zip(donors, raw_vals)):
            cell_values[i].append(fmt(raw_val))
            cell_colors[i].append(color_fn(raw_val, numeric))

    # Header colors from donor palette
    header_colors = ["#13151f"] + [
        _hex_to_rgba(DONOR_COLORS.get(d, "#aaa"), 0.4) for d in donors
    ]

    fig = go.Figure(go.Table(
        columnwidth=[2.2] + [1.2] * len(donors),
        header=dict(
            values=["<b>Metric</b>"] + [f"<b>{d}</b>" for d in donors],
            fill_color=header_colors,
            font=dict(size=13, color=[
                "#888"
            ] + [DONOR_COLORS.get(d, "#aaa") for d in donors]),
            align=["left"] + ["center"] * len(donors),
            line_color="#2a2d3e",
            height=40,
        ),
        cells=dict(
            values=[row_labels] + cell_values,
            fill_color=["#13151f"] + cell_colors,
            font=dict(size=12, color="#e0e0e0"),
            align=["left"] + ["center"] * len(donors),
            line_color="#2a2d3e",
            height=36,
        ),
    ))

    fig.update_layout(
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(family="system-ui, sans-serif", color="#e0e0e0"),
        title=dict(
            text="Donor Compliance Scorecard",
            font=dict(size=16, color="#e0e0e0"),
            x=0.5,
        ),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


if __name__ == "__main__":
    print("Building scorecard…")
    fig = build_scorecard()
    fig.write_html(
        str(SCORECARD_PATH),
        include_plotlyjs="cdn",
        full_html=True,
        config={"displayModeBar": False, "responsive": True},
    )
    print(f"Written: {SCORECARD_PATH}")
