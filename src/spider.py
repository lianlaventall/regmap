"""
spider.py — Radar/spider chart comparing donor profiles across 6 dimensions.

Axes (all expressed as 0–100 percentages):
  1. Obligation Rate       — % RESTRICTION + QUALIFIED_RESTRICTION + HIGH_RISK
  2. Real NGO Autonomy     — % DISCRETIONARY_AUTONOMY of total clauses
  3. Preference Signaling  — % GUIDED_DISCRETION of total clauses
  4. Risk Culture          — % clauses in INTEGRITY domain
  5. Domain Breadth        — domains covered as % of 10 possible
  6. Approval Gating       — % of DECISION clauses that are CONDITIONAL_FLEXIBILITY or DONOR_RESERVED

Output: output/spider.html
"""

import json
from pathlib import Path

import plotly.graph_objects as go

OUTPUT_DIR = Path("output")
SPIDER_PATH = OUTPUT_DIR / "spider.html"
ALL_DOMAINS = [
    "PROCUREMENT", "ELIGIBILITY_ACTOR", "ELIGIBILITY_COMMODITY", "ELIGIBILITY_ASSET",
    "INTEGRITY", "REPORTING", "FINANCIAL", "RECORD_KEEPING", "SAFEGUARDING", "SCOPE"
]
DONOR_COLORS = {
    "DOS":  "#1abc9c",
    "ECHO": "#e67e22",
    "GFFO": "#9b59b6",
    "AFD":  "#f39c12",
}
OBLIGATION_TIERS = {"RESTRICTION", "QUALIFIED_RESTRICTION", "HIGH_RISK"}
AXES = [
    "Obligation Rate",
    "Real NGO Autonomy",
    "Preference Signaling",
    "Risk Culture (INTEGRITY)",
    "Domain Breadth",
    "Approval Gating",
]


def compute_metrics(clauses: list[dict]) -> dict:
    n = len(clauses)
    if n == 0:
        return {ax: 0.0 for ax in AXES}

    obligation = sum(1 for c in clauses if c.get("tier") in OBLIGATION_TIERS)
    autonomy   = sum(1 for c in clauses if c.get("decision_type") == "DISCRETIONARY_AUTONOMY")
    guided     = sum(1 for c in clauses if c.get("tier") == "GUIDED_DISCRETION")
    integrity  = sum(1 for c in clauses if c.get("domain") == "INTEGRITY")

    domains_covered = len({c.get("domain") for c in clauses if c.get("domain")})

    decision_clauses = [c for c in clauses if c.get("tier") == "DECISION"]
    n_decision = len(decision_clauses)
    gated = sum(
        1 for c in decision_clauses
        if c.get("decision_type") in {"CONDITIONAL_FLEXIBILITY", "DONOR_RESERVED"}
    )
    approval_gating = (gated / n_decision * 100) if n_decision > 0 else 0.0

    return {
        "Obligation Rate":            round(obligation / n * 100, 1),
        "Real NGO Autonomy":          round(autonomy   / n * 100, 1),
        "Preference Signaling":       round(guided     / n * 100, 1),
        "Risk Culture (INTEGRITY)":   round(integrity  / n * 100, 1),
        "Domain Breadth":             round(domains_covered / len(ALL_DOMAINS) * 100, 1),
        "Approval Gating":            round(approval_gating, 1),
    }


def build_spider() -> go.Figure:
    donor_files = sorted(OUTPUT_DIR.glob("*.json"))
    traces = []

    for path in donor_files:
        if path.name == "flow_data.json":
            continue
        raw = json.loads(path.read_text())
        donor   = raw["donor"]
        clauses = raw["clauses"]
        metrics = compute_metrics(clauses)

        values = [metrics[ax] for ax in AXES]
        # close the polygon
        values_closed = values + [values[0]]
        axes_closed   = AXES   + [AXES[0]]

        color = DONOR_COLORS.get(donor, "#aaaaaa")
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fill_color = f"rgba({r},{g},{b},0.15)"

        traces.append(go.Scatterpolar(
            r=values_closed,
            theta=axes_closed,
            name=donor,
            fill="toself",
            fillcolor=fill_color,
            line=dict(color=color, width=2),
            opacity=1.0,
            hovertemplate=(
                "<b>" + donor + "</b><br>" +
                "<br>".join(f"{ax}: {v}%" for ax, v in zip(AXES, values)) +
                "<extra></extra>"
            ),
        ))

        # solid outline trace (no fill opacity issue)
        traces.append(go.Scatterpolar(
            r=values_closed,
            theta=axes_closed,
            name=donor,
            line=dict(color=color, width=2.5),
            mode="lines+markers",
            marker=dict(size=6, color=color),
            showlegend=False,
            hoverinfo="skip",
        ))

    fig = go.Figure(traces)
    fig.update_layout(
        polar=dict(
            bgcolor="#1a1d27",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                tickfont=dict(size=10, color="#666"),
                gridcolor="#2a2d3e",
                linecolor="#2a2d3e",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#aaa"),
                gridcolor="#2a2d3e",
                linecolor="#2a2d3e",
            ),
        ),
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(family="system-ui, sans-serif", color="#e0e0e0"),
        title=dict(
            text="Donor Profile Comparison",
            font=dict(size=16, color="#e0e0e0"),
            x=0.5,
        ),
        legend=dict(
            bgcolor="#1a1d27",
            bordercolor="#2a2d3e",
            borderwidth=1,
            font=dict(size=12),
            x=1.08, y=0.5,
        ),
        margin=dict(l=80, r=180, t=80, b=80),
    )
    return fig


if __name__ == "__main__":
    print("Building spider chart…")
    fig = build_spider()
    fig.write_html(
        str(SPIDER_PATH),
        include_plotlyjs="cdn",
        full_html=True,
        config={"displayModeBar": True, "responsive": True},
    )
    print(f"Written: {SPIDER_PATH}")
