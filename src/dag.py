"""
dag.py — Build decision flow DAG visualization.

Layout: Root (Donor) → Domain → Clause → Branch outcomes
  - RESTRICTION clauses: grouped per domain (count + tooltip)
  - UNCONDITIONAL dead ends: separate highlighted group per domain
  - DECISION / HIGH_RISK / QUALIFIED_RESTRICTION: shown individually with branches

Output: output/dag.html
"""

import json
from collections import defaultdict
from pathlib import Path

OUTPUT_DIR = Path("output")
DAG_PATH = OUTPUT_DIR / "dag.html"

DOMAIN_ORDER = [
    "PROCUREMENT", "ELIGIBILITY", "REPORTING",
    "FINANCIAL", "RECORD_KEEPING", "SAFEGUARDING", "SCOPE",
]


def short(text, n=90):
    return text[:n] + "…" if len(text) > n else text


def build_tree(donor: str, clauses: list) -> dict:
    by_domain = defaultdict(list)
    for c in clauses:
        by_domain[c.get("domain", "UNKNOWN")].append(c)

    domain_nodes = []
    for domain in sorted(by_domain.keys(), key=lambda d: DOMAIN_ORDER.index(d) if d in DOMAIN_ORDER else 99):
        cs = by_domain[domain]
        children = []

        # ── UNCONDITIONAL dead ends ──────────────────────────────────────────
        unconditional = [c for c in cs if c.get("dead_end_type") == "UNCONDITIONAL"]
        if unconditional:
            children.append({
                "name": f"UNCONDITIONAL ({len(unconditional)})",
                "type": "unconditional_group",
                "count": len(unconditional),
                "clauses": [{"clause_id": c["clause_id"], "text": c["text"]} for c in unconditional],
            })

        # ── RESTRICTION group (excluding unconditionals already shown) ───────
        restrictions = [
            c for c in cs
            if c.get("tier") == "RESTRICTION" and c.get("dead_end_type") != "UNCONDITIONAL"
        ]
        if restrictions:
            children.append({
                "name": f"RESTRICTION ({len(restrictions)})",
                "type": "restriction_group",
                "count": len(restrictions),
                "clauses": [{"clause_id": c["clause_id"], "text": c["text"],
                              "dead_end_type": c.get("dead_end_type")} for c in restrictions],
            })

        # ── Individual non-restriction clauses ───────────────────────────────
        for c in cs:
            tier = c.get("tier")
            if tier == "RESTRICTION":
                continue

            node = {
                "name": short(c["text"]),
                "full_text": c["text"],
                "type": tier.lower().replace("qualified_restriction", "qualified"),
                "clause_id": c["clause_id"],
                "dead_end_type": c.get("dead_end_type"),
                "trigger_word": c.get("trigger_word", ""),
                "children": [],
            }

            if tier == "DECISION":
                node["children"] = [
                    {"name": "Comply / Proceed",          "type": "outcome_yes"},
                    {"name": "Non-compliance / Escalate", "type": "outcome_no"},
                ]
            elif tier == "HIGH_RISK":
                node["children"] = [
                    {"name": "Flag for audit review", "type": "outcome_audit"},
                ]
            elif tier == "QUALIFIED_RESTRICTION":
                trigger = c.get("trigger_word", "condition")
                node["children"] = [
                    {"name": f"Condition met → Allowed",      "type": "outcome_yes"},
                    {"name": "Condition not met → Restriction", "type": "outcome_no"},
                ]

            children.append(node)

        domain_nodes.append({
            "name": domain,
            "type": "domain",
            "children": children,
        })

    return {
        "name": donor,
        "type": "root",
        "children": domain_nodes,
    }


def build_dag_data() -> dict:
    trees = {}
    for path in sorted(OUTPUT_DIR.glob("*.json")):
        if path.name in ("flow_data.json",):
            continue
        raw = json.loads(path.read_text())
        donor = raw["donor"]
        trees[donor] = build_tree(donor, raw["clauses"])
        print(f"  {donor}: tree built")
    return trees


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>regmap — Decision Flow</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #0f1117; color: #e0e0e0; overflow: hidden; }

header {
  display: flex; align-items: center; gap: 16px;
  padding: 12px 24px; background: #1a1d27; border-bottom: 1px solid #2a2d3e;
  position: fixed; top: 0; left: 0; right: 0; z-index: 50;
}
header h1 { font-size: 1.05rem; font-weight: 600; letter-spacing: .03em; }
select {
  background: #2a2d3e; color: #e0e0e0; border: 1px solid #3a3d4e;
  padding: 5px 12px; border-radius: 6px; font-size: .85rem; cursor: pointer;
}
#stats { font-size: .75rem; color: #666; margin-left: auto; }

#canvas {
  position: fixed; top: 49px; left: 0; right: 0; bottom: 0;
}
svg { width: 100%; height: 100%; }

/* ── nodes ── */
.node { cursor: default; }

.node circle, .node rect {
  transition: filter .15s;
}
.node:hover circle, .node:hover rect {
  filter: brightness(1.4);
  cursor: pointer;
}

/* root */
.node-root circle    { fill: #1a1d27; stroke: #aaa; stroke-width: 2; r: 14; }
.node-root text      { font-size: 13px; font-weight: 700; fill: #e0e0e0; }

/* domain */
.node-domain rect    { fill: #1e2235; stroke: #3a3d4e; stroke-width: 1.5; rx: 5; }
.node-domain text    { font-size: 11px; font-weight: 600; fill: #aaa; text-anchor: middle; }

/* restriction group */
.node-restriction_group rect { fill: #2a1515; stroke: #c0392b; stroke-width: 1; rx: 4; }
.node-restriction_group text { font-size: 10px; fill: #e74c3c; text-anchor: middle; }

/* unconditional group */
.node-unconditional_group rect { fill: #2a1010; stroke: #e74c3c; stroke-width: 2; rx: 4; stroke-dasharray: 4 2; }
.node-unconditional_group text { font-size: 10px; fill: #ff6b6b; font-weight: 600; text-anchor: middle; }

/* decision */
.node-decision circle { fill: #1a3a5c; stroke: #3498db; stroke-width: 2; }
.node-decision text   { font-size: 9px; fill: #ccc; }

/* high_risk */
.node-high_risk circle { fill: #3a2010; stroke: #e67e22; stroke-width: 2; }
.node-high_risk text   { font-size: 9px; fill: #ccc; }

/* qualified */
.node-qualified circle { fill: #2a1540; stroke: #9b59b6; stroke-width: 2; }
.node-qualified text   { font-size: 9px; fill: #ccc; }

/* outcomes */
.node-outcome_yes   circle { fill: #0e2a1a; stroke: #2ecc71; stroke-width: 1.5; }
.node-outcome_yes   text   { font-size: 9px; fill: #2ecc71; }
.node-outcome_no    circle { fill: #2a0e0e; stroke: #e74c3c; stroke-width: 1.5; }
.node-outcome_no    text   { font-size: 9px; fill: #e74c3c; }
.node-outcome_audit circle { fill: #2a1a00; stroke: #f39c12; stroke-width: 1.5; }
.node-outcome_audit text   { font-size: 9px; fill: #f39c12; }

/* links */
.link {
  fill: none; stroke-width: 1.5px;
  stroke: #2a2d3e;
}
.link-decision        { stroke: #3498db55; }
.link-high_risk       { stroke: #e67e2255; }
.link-qualified       { stroke: #9b59b655; }
.link-restriction_group { stroke: #c0392b33; }
.link-unconditional_group { stroke: #e74c3c55; stroke-dasharray: 4 2; }
.link-outcome         { stroke: #2a2d3e; }

/* tooltip */
#tooltip {
  position: fixed; background: #1a1d27; border: 1px solid #3a3d4e;
  border-radius: 8px; padding: 12px 16px; font-size: .76rem;
  max-width: 400px; pointer-events: none; opacity: 0;
  transition: opacity .15s; z-index: 200; line-height: 1.6;
}
#tooltip .tt-tier   { font-weight: 700; margin-bottom: 6px; font-size: .8rem; }
#tooltip .tt-id     { font-size: .68rem; color: #666; margin-bottom: 4px; }
#tooltip .tt-text   { color: #ccc; margin-bottom: 6px; }
#tooltip .tt-clause { color: #bbb; margin-bottom: 5px; border-left: 2px solid #3a3d4e; padding-left: 8px; font-size: .73rem; }
#tooltip .tt-de     { font-size: .68rem; color: #e74c3c; margin-top: 2px; }

/* legend */
#legend {
  position: fixed; bottom: 16px; left: 16px;
  background: #1a1d27cc; border: 1px solid #2a2d3e;
  border-radius: 8px; padding: 10px 14px; font-size: .72rem;
  backdrop-filter: blur(4px);
}
#legend h3 { font-size: .65rem; color: #555; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 7px; }
.li { display: flex; align-items: center; gap: 7px; margin-bottom: 4px; color: #888; }
.ld { width: 10px; height: 10px; border-radius: 50%; border: 2px solid; flex-shrink: 0; }
</style>
</head>
<body>

<header>
  <h1>regmap — Decision Flow</h1>
  <select id="donor-select"></select>
  <span id="stats"></span>
</header>

<div id="canvas"><svg id="svg"></svg></div>
<div id="tooltip"></div>

<div id="legend">
  <h3>Node types</h3>
  <div class="li"><div class="ld" style="background:#1a3a5c;border-color:#3498db"></div>Decision</div>
  <div class="li"><div class="ld" style="background:#3a2010;border-color:#e67e22"></div>High Risk</div>
  <div class="li"><div class="ld" style="background:#2a1540;border-color:#9b59b6"></div>Qualified Restriction</div>
  <div class="li"><div class="ld" style="background:#2a1515;border-color:#c0392b"></div>Restriction group</div>
  <div class="li"><div class="ld" style="background:#2a1010;border-color:#e74c3c"></div>Unconditional dead ends</div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const TREES = __DAG_DATA__;

const TIER_COLORS = {
  decision:             "#3498db",
  high_risk:            "#e67e22",
  qualified:            "#9b59b6",
  restriction_group:    "#c0392b",
  unconditional_group:  "#e74c3c",
  outcome_yes:          "#2ecc71",
  outcome_no:           "#e74c3c",
  outcome_audit:        "#f39c12",
  domain:               "#3a3d4e",
  root:                 "#aaa",
};

const tooltip = document.getElementById("tooltip");
const select  = document.getElementById("donor-select");
const stats   = document.getElementById("stats");

Object.keys(TREES).forEach(d => {
  const opt = document.createElement("option");
  opt.value = d; opt.textContent = d;
  select.appendChild(opt);
});

// ── tooltip helpers ──────────────────────────────────────────────────────────
function showClauseTooltip(e, d) {
  const data = d.data;
  if (["root","domain","outcome_yes","outcome_no","outcome_audit"].includes(data.type)) return;

  let html = "";
  if (data.type === "restriction_group" || data.type === "unconditional_group") {
    const label = data.type === "unconditional_group" ? "UNCONDITIONAL DEAD ENDS" : "RESTRICTIONS";
    html = `<div class="tt-tier" style="color:${TIER_COLORS[data.type]}">${label} — ${data.count} clauses</div>`;
    (data.clauses || []).slice(0, 5).forEach(c => {
      html += `<div class="tt-clause">
        <div class="tt-id">${c.clause_id}${c.dead_end_type ? ` · <span class="tt-de">${c.dead_end_type}</span>` : ""}</div>
        ${c.text.slice(0,180)}
      </div>`;
    });
    if ((data.clauses||[]).length > 5)
      html += `<div style="color:#555;font-size:.68rem">+${data.clauses.length - 5} more</div>`;
  } else {
    const color = TIER_COLORS[data.type] || "#aaa";
    html = `
      <div class="tt-id">${data.clause_id || ""} · trigger: ${data.trigger_word || ""}</div>
      <div class="tt-tier" style="color:${color}">${data.type.toUpperCase().replace("_"," ")}</div>
      <div class="tt-text">${data.full_text || data.name}</div>
      ${data.dead_end_type ? `<div class="tt-de">Dead end: ${data.dead_end_type}</div>` : ""}
    `;
  }

  tooltip.innerHTML = html;
  tooltip.style.opacity = 1;
  positionTooltip(e);
}

function positionTooltip(e) {
  tooltip.style.left = (e.clientX + 16) + "px";
  tooltip.style.top  = (e.clientY - 10) + "px";
}

// ── render ────────────────────────────────────────────────────────────────────
let currentZoom = null;

function render(donorKey) {
  const treeData = TREES[donorKey];

  const svg    = d3.select("#svg");
  const canvas = document.getElementById("canvas");
  const W = canvas.clientWidth;
  const H = canvas.clientHeight;

  svg.selectAll("*").remove();

  const g = svg.append("g");
  const zoom = d3.zoom().scaleExtent([0.1, 3]).on("zoom", e => g.attr("transform", e.transform));
  svg.call(zoom);

  const root = d3.hierarchy(treeData);

  // node sizing
  const nodeW = (d) => {
    if (d.data.type === "domain") return 110;
    if (d.data.type === "restriction_group" || d.data.type === "unconditional_group") return 110;
    return 0; // circles
  };
  const nodeH = (d) => {
    if (d.data.type === "domain") return 28;
    if (d.data.type === "restriction_group" || d.data.type === "unconditional_group") return 24;
    return 0;
  };

  const treeLayout = d3.tree()
    .nodeSize([34, 260])
    .separation((a, b) => a.parent === b.parent ? 1.1 : 1.6);

  treeLayout(root);

  // ── links ──────────────────────────────────────────────────────────────────
  const linkClass = (d) => {
    const t = d.target.data.type;
    if (t.startsWith("outcome")) return "link link-outcome";
    return `link link-${t}`;
  };

  g.append("g").selectAll("path")
    .data(root.links())
    .join("path")
      .attr("class", d => linkClass(d))
      .attr("d", d3.linkHorizontal()
        .x(d => d.y)
        .y(d => d.x));

  // ── nodes ──────────────────────────────────────────────────────────────────
  const node = g.append("g").selectAll("g")
    .data(root.descendants())
    .join("g")
      .attr("class", d => `node node-${d.data.type}`)
      .attr("transform", d => `translate(${d.y},${d.x})`)
      .on("mouseover", showClauseTooltip)
      .on("mousemove", positionTooltip)
      .on("mouseout", () => { tooltip.style.opacity = 0; });

  // rect nodes (domain, restriction_group, unconditional_group)
  node.filter(d => ["domain","restriction_group","unconditional_group"].includes(d.data.type))
    .append("rect")
      .attr("x", d => -nodeW(d) / 2)
      .attr("y", d => -nodeH(d) / 2)
      .attr("width",  d => nodeW(d))
      .attr("height", d => nodeH(d))
      .attr("rx", 4);

  node.filter(d => ["domain","restriction_group","unconditional_group"].includes(d.data.type))
    .append("text")
      .attr("dy", "0.35em")
      .text(d => d.data.name);

  // circle nodes (root, decision, high_risk, qualified, outcomes)
  const circleR = d => {
    if (d.data.type === "root")           return 14;
    if (["decision","high_risk","qualified"].includes(d.data.type)) return 10;
    return 7;
  };

  node.filter(d => !["domain","restriction_group","unconditional_group"].includes(d.data.type))
    .append("circle")
      .attr("r", circleR);

  // labels for circle nodes
  node.filter(d => d.data.type === "root")
    .append("text")
      .attr("dy", "0.35em")
      .attr("x", 20)
      .text(d => d.data.name);

  node.filter(d => ["decision","high_risk","qualified"].includes(d.data.type))
    .append("text")
      .attr("dy", "0.35em")
      .attr("x", 14)
      .attr("text-anchor", "start")
      .attr("font-size", "9px")
      .attr("fill", "#aaa")
      .text(d => d.data.name);

  node.filter(d => d.data.type.startsWith("outcome"))
    .append("text")
      .attr("dy", "0.35em")
      .attr("x", 11)
      .attr("text-anchor", "start")
      .attr("font-size", "9px")
      .text(d => d.data.name);

  // ── fit to view ─────────────────────────────────────────────────────────────
  const bounds  = g.node().getBBox();
  const padding = 60;
  const scale   = Math.min(
    (W - padding * 2) / bounds.width,
    (H - padding * 2) / bounds.height,
    1.0
  );
  const tx = (W - bounds.width  * scale) / 2 - bounds.x * scale;
  const ty = (H - bounds.height * scale) / 2 - bounds.y * scale;

  svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));

  // stats
  const clauses = root.descendants().filter(d =>
    ["decision","high_risk","qualified","restriction_group","unconditional_group"].includes(d.data.type)
  );
  stats.textContent = `${root.descendants().length} nodes · scroll/pinch to zoom · drag to pan`;
}

select.addEventListener("change", () => render(select.value));
render(Object.keys(TREES)[0]);
</script>
</body>
</html>
"""


def build_viz(trees: dict) -> None:
    html = HTML_TEMPLATE.replace("__DAG_DATA__", json.dumps(trees))
    DAG_PATH.write_text(html)
    print(f"Written: {DAG_PATH}")


if __name__ == "__main__":
    print("Building DAG data…")
    trees = build_dag_data()
    print("Building visualization…")
    build_viz(trees)
    print("Done.")
