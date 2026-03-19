"""
main.py — Build decision flow structures from extracted clause JSONs
and render an interactive D3.js visualization.

Outputs:
  output/flow_data.json  — structured flow graph per donor
  output/flow_viz.html   — single-file D3 visualization with donor dropdown
"""

import json
import re
from pathlib import Path

TIERS = ["RESTRICTION", "QUALIFIED_RESTRICTION", "HIGH_RISK", "DECISION"]

OUTPUT_DIR = Path("output")
FLOW_DATA_PATH = OUTPUT_DIR / "flow_data.json"
FLOW_VIZ_PATH = OUTPUT_DIR / "flow_viz.html"


# ---------------------------------------------------------------------------
# Flow structure builder
# ---------------------------------------------------------------------------

def _node_id(clause_id: str) -> str:
    return clause_id.replace("-", "_").lower()


def build_flow(donor: str, document: str, clauses: list) -> dict:
    """Convert a flat clause list into a hierarchical flow graph.

    Node types
    ----------
    root            — synthetic entry point for the donor
    restriction     — dead end; no NGO choice
    decision        — branches into yes/no child nodes
    high_risk       — flagged audit branch
    qualified       — branches with a condition extracted from the clause text
    """
    nodes = []
    edges = []

    root_id = f"{donor.lower()}_root"
    nodes.append({
        "id": root_id,
        "type": "root",
        "label": f"{donor} Obligations",
        "donor": donor,
    })

    for clause in clauses:
        nid = _node_id(clause["clause_id"])
        tier = clause["tier"]
        text = clause["text"]
        label = text[:80] + ("…" if len(text) > 80 else "")

        base = {
            "id": nid,
            "clause_id": clause["clause_id"],
            "donor": donor,
            "label": label,
            "full_text": text,
            "page": clause["page"],
            "trigger_word": clause["trigger_word"],
            "actor": clause.get("actor", ""),
            "creates_ngo_dependency": clause.get("creates_ngo_dependency", False),
            "notes": clause.get("notes", ""),
            "context_flag": clause.get("context_flag", False),
        }

        if tier == "RESTRICTION":
            base["type"] = "restriction"
            base["branches"] = []          # dead end

        elif tier == "DECISION":
            yes_id = nid + "_yes"
            no_id = nid + "_no"
            base["type"] = "decision"
            base["branches"] = [
                {"edge": "yes", "target": yes_id, "label": "Comply / Proceed"},
                {"edge": "no",  "target": no_id,  "label": "Non-compliance / Escalate"},
            ]
            nodes.append({"id": yes_id, "type": "outcome", "label": "Comply / Proceed",   "donor": donor})
            nodes.append({"id": no_id,  "type": "outcome", "label": "Non-compliance / Escalate", "donor": donor})
            edges.append({"source": nid, "target": yes_id, "label": "yes"})
            edges.append({"source": nid, "target": no_id,  "label": "no"})

        elif tier == "HIGH_RISK":
            audit_id = nid + "_audit"
            base["type"] = "high_risk"
            base["audit_flag"] = True
            base["branches"] = [
                {"edge": "audit", "target": audit_id, "label": "Flag for audit review"},
            ]
            nodes.append({"id": audit_id, "type": "audit", "label": "Audit / Review Required", "donor": donor})
            edges.append({"source": nid, "target": audit_id, "label": "audit risk"})

        elif tier == "QUALIFIED_RESTRICTION":
            # Try to extract the condition from the text (phrase after trigger word)
            trigger = clause.get("trigger_word", "where")
            match = re.search(
                rf'\b{re.escape(trigger)}\b(.{{0,120}}?)(?:[,;.]|$)',
                text, re.IGNORECASE
            )
            condition = match.group(1).strip() if match else "condition applies"
            condition = condition[:80] + ("…" if len(condition) > 80 else "")

            met_id = nid + "_met"
            not_met_id = nid + "_not_met"
            base["type"] = "qualified"
            base["condition"] = condition
            base["branches"] = [
                {"edge": "condition_met",     "target": met_id,     "label": f"If {condition}"},
                {"edge": "condition_not_met", "target": not_met_id, "label": "Condition not met"},
            ]
            nodes.append({"id": met_id,     "type": "outcome", "label": f"Allowed: {condition[:60]}", "donor": donor})
            nodes.append({"id": not_met_id, "type": "outcome", "label": "Restriction applies",        "donor": donor})
            edges.append({"source": nid, "target": met_id,     "label": f"if {trigger}"})
            edges.append({"source": nid, "target": not_met_id, "label": "otherwise"})

        nodes.append(base)
        edges.append({"source": root_id, "target": nid, "label": tier.lower()})

    return {
        "donor": donor,
        "document": document,
        "nodes": nodes,
        "edges": edges,
    }


# ---------------------------------------------------------------------------
# Load + write flow_data.json
# ---------------------------------------------------------------------------

def build_flow_data() -> dict:
    flows = {}
    for path in sorted(OUTPUT_DIR.glob("*.json")):
        if path.name in ("flow_data.json",):
            continue
        data = json.loads(path.read_text())
        donor = data["donor"]
        flows[donor] = build_flow(donor, data["document"], data["clauses"])
        print(f"  {donor}: {len(data['clauses'])} clauses → {len(flows[donor]['nodes'])} nodes, {len(flows[donor]['edges'])} edges")

    FLOW_DATA_PATH.write_text(json.dumps(flows, indent=2))
    print(f"Written: {FLOW_DATA_PATH}")
    return flows


# ---------------------------------------------------------------------------
# HTML visualization
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>regmap — Decision Flow</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #0f1117; color: #e0e0e0; }
  header {
    display: flex; align-items: center; gap: 16px;
    padding: 14px 24px; background: #1a1d27; border-bottom: 1px solid #2a2d3e;
  }
  header h1 { font-size: 1.1rem; font-weight: 600; letter-spacing: .03em; }
  select {
    background: #2a2d3e; color: #e0e0e0; border: 1px solid #3a3d4e;
    padding: 6px 12px; border-radius: 6px; font-size: .9rem; cursor: pointer;
  }
  #stats { font-size: .8rem; color: #888; margin-left: auto; }

  #canvas { width: 100%; height: calc(100vh - 55px); overflow: hidden; }
  svg { width: 100%; height: 100%; }

  .link { fill: none; stroke-width: 1.5px; }
  .link-restriction     { stroke: #e74c3c; }
  .link-decision        { stroke: #3498db; }
  .link-high_risk       { stroke: #e67e22; }
  .link-qualified       { stroke: #9b59b6; }
  .link-yes             { stroke: #2ecc71; }
  .link-no              { stroke: #e74c3c; }
  .link-audit           { stroke: #e67e22; stroke-dasharray: 5 3; }
  .link-condition_met   { stroke: #2ecc71; }
  .link-condition_not_met { stroke: #e74c3c; }

  .node circle {
    stroke-width: 2px; cursor: pointer;
    transition: r .15s, filter .15s;
    filter: drop-shadow(0 0 4px rgba(0,0,0,.6));
  }
  .node circle:hover { filter: drop-shadow(0 0 8px rgba(255,255,255,.3)); }

  .node-root         circle { fill: #1a1d27; stroke: #aaa; }
  .node-restriction  circle { fill: #c0392b; stroke: #e74c3c; }
  .node-decision     circle { fill: #2980b9; stroke: #3498db; }
  .node-high_risk    circle { fill: #d35400; stroke: #e67e22; }
  .node-qualified    circle { fill: #8e44ad; stroke: #9b59b6; }
  .node-outcome      circle { fill: #27ae60; stroke: #2ecc71; }
  .node-audit        circle { fill: #e67e22; stroke: #f39c12; }

  .node text {
    font-size: 9px; fill: #ccc; pointer-events: none;
    text-anchor: middle; dominant-baseline: central;
  }

  .edge-label {
    font-size: 8px; fill: #777; pointer-events: none;
  }

  #tooltip {
    position: fixed; background: #1a1d27; border: 1px solid #3a3d4e;
    border-radius: 8px; padding: 12px 16px; font-size: .8rem;
    max-width: 380px; pointer-events: none; opacity: 0;
    transition: opacity .15s; z-index: 100; line-height: 1.5;
  }
  #tooltip .tt-id    { font-size: .7rem; color: #888; margin-bottom: 4px; }
  #tooltip .tt-tier  { font-weight: 700; margin-bottom: 6px; }
  #tooltip .tt-text  { color: #ccc; margin-bottom: 6px; }
  #tooltip .tt-notes { color: #888; font-style: italic; }

  .tier-restriction  { color: #e74c3c; }
  .tier-decision     { color: #3498db; }
  .tier-high_risk    { color: #e67e22; }
  .tier-qualified    { color: #9b59b6; }

  #legend {
    position: fixed; bottom: 20px; left: 20px;
    background: #1a1d27; border: 1px solid #2a2d3e;
    border-radius: 8px; padding: 12px 16px; font-size: .78rem;
  }
  #legend h3 { font-size: .75rem; color: #888; margin-bottom: 8px; text-transform: uppercase; letter-spacing: .05em; }
  .legend-item { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
  .legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
</style>
</head>
<body>

<header>
  <h1>regmap</h1>
  <select id="donor-select"></select>
  <span id="stats"></span>
</header>

<div id="canvas"><svg id="svg"></svg></div>
<div id="tooltip"></div>

<div id="legend">
  <h3>Node types</h3>
  <div class="legend-item"><div class="legend-dot" style="background:#c0392b;border:2px solid #e74c3c"></div>Restriction (dead end)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#2980b9;border:2px solid #3498db"></div>Decision (yes / no)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#d35400;border:2px solid #e67e22"></div>High Risk (audit flag)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#8e44ad;border:2px solid #9b59b6"></div>Qualified restriction</div>
  <div class="legend-item"><div class="legend-dot" style="background:#27ae60;border:2px solid #2ecc71"></div>Outcome</div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const FLOW_DATA = __FLOW_DATA__;

const donors = Object.keys(FLOW_DATA);
const select = document.getElementById("donor-select");
donors.forEach(d => {
  const opt = document.createElement("option");
  opt.value = d; opt.textContent = d;
  select.appendChild(opt);
});

const tooltip = document.getElementById("tooltip");
const stats   = document.getElementById("stats");

let simulation, svg, g;

function tierClass(type) {
  return { restriction: "tier-restriction", decision: "tier-decision",
           high_risk: "tier-high_risk", qualified: "tier-qualified" }[type] || "";
}

function render(donor) {
  const flow = FLOW_DATA[donor];
  const nodeMap = Object.fromEntries(flow.nodes.map(n => [n.id, n]));

  // node radius by type
  const radius = { root: 18, restriction: 10, decision: 10, high_risk: 10,
                   qualified: 10, outcome: 8, audit: 8 };

  const w = document.getElementById("canvas").clientWidth;
  const h = document.getElementById("canvas").clientHeight;

  // clear
  d3.select("#svg").selectAll("*").remove();
  if (simulation) simulation.stop();

  svg = d3.select("#svg");
  g   = svg.append("g");

  svg.call(
    d3.zoom().scaleExtent([0.15, 3])
      .on("zoom", e => g.attr("transform", e.transform))
  );

  // build link data
  const links = flow.edges.map(e => ({
    source: e.source, target: e.target, label: e.label
  }));

  // build node data with initial positions
  const nodes = flow.nodes.map(n => ({
    ...n,
    r: radius[n.type] || 8,
    x: n.type === "root" ? w / 2 : w / 2 + (Math.random() - .5) * 400,
    y: n.type === "root" ? 60     : 60 + Math.random() * (h - 120),
  }));

  // arrowhead markers
  const markerColors = {
    default: "#555", yes: "#2ecc71", no: "#e74c3c",
    audit: "#e67e22", condition_met: "#2ecc71", condition_not_met: "#e74c3c"
  };
  const defs = svg.append("defs");
  Object.entries(markerColors).forEach(([key, color]) => {
    defs.append("marker")
      .attr("id", `arrow-${key}`)
      .attr("viewBox", "0 -5 10 10").attr("refX", 18).attr("refY", 0)
      .attr("markerWidth", 6).attr("markerHeight", 6).attr("orient", "auto")
      .append("path").attr("d", "M0,-5L10,0L0,5").attr("fill", color);
  });

  function markerKey(label) {
    if (["yes","no","audit","condition_met","condition_not_met"].includes(label)) return label;
    return "default";
  }

  // links
  const linkSel = g.append("g").selectAll("line")
    .data(links).join("line")
    .attr("class", d => `link link-${d.label}`)
    .attr("marker-end", d => `url(#arrow-${markerKey(d.label)})`);

  const edgeLabelSel = g.append("g").selectAll("text")
    .data(links).join("text")
    .attr("class", "edge-label")
    .text(d => d.label);

  // nodes
  const nodeSel = g.append("g").selectAll("g")
    .data(nodes).join("g")
    .attr("class", d => `node node-${d.type}`)
    .call(
      d3.drag()
        .on("start", (e, d) => { if (!e.active) simulation.alphaTarget(.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
    )
    .on("mouseover", (e, d) => {
      if (!d.full_text) return;
      tooltip.style.opacity = 1;
      tooltip.innerHTML = `
        <div class="tt-id">${d.clause_id || ""} · page ${d.page || ""} · trigger: <em>${d.trigger_word || ""}</em></div>
        <div class="tt-tier ${tierClass(d.type)}">${d.type.toUpperCase().replace("_"," ")}</div>
        <div class="tt-text">${d.full_text}</div>
        ${d.notes ? `<div class="tt-notes">${d.notes}</div>` : ""}
        ${d.actor ? `<div style="margin-top:6px;font-size:.75rem;color:#666">Actor: ${d.actor} · NGO dependency: ${d.creates_ngo_dependency}</div>` : ""}
      `;
    })
    .on("mousemove", e => {
      tooltip.style.left = (e.clientX + 14) + "px";
      tooltip.style.top  = (e.clientY - 10) + "px";
    })
    .on("mouseout", () => { tooltip.style.opacity = 0; });

  nodeSel.append("circle").attr("r", d => d.r);
  nodeSel.append("text").text(d => d.type === "root" ? d.label : (d.clause_id || ""));

  // force simulation
  simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(120).strength(.6))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(w / 2, h / 2))
    .force("collide", d3.forceCollide(d => d.r + 12))
    .on("tick", () => {
      linkSel
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      edgeLabelSel
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2);
      nodeSel.attr("transform", d => `translate(${d.x},${d.y})`);
    });

  const clauseNodes = flow.nodes.filter(n => n.clause_id);
  stats.textContent = `${clauseNodes.length} clauses · ${flow.nodes.length} nodes · ${flow.edges.length} edges`;
}

select.addEventListener("change", () => render(select.value));
render(donors[0]);
</script>
</body>
</html>
"""


def build_viz(flows: dict) -> None:
    flow_json = json.dumps(flows)
    html = HTML_TEMPLATE.replace("__FLOW_DATA__", flow_json)
    FLOW_VIZ_PATH.write_text(html)
    print(f"Written: {FLOW_VIZ_PATH}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Building flow structures…")
    flows = build_flow_data()
    print("Building visualization…")
    build_viz(flows)
    print("Done.")
