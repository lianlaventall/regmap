"""
sankey.py — Build cross-donor Sankey flow visualization.

Flow: Donor → Domain (donor-specific) → Tier (shared)

The shared tier nodes on the right show where both donors converge —
the visual representation of overlapping restrictions.

Output: output/sankey.html
"""

import json
from collections import Counter
from pathlib import Path

OUTPUT_DIR = Path("output")
SANKEY_PATH = OUTPUT_DIR / "sankey.html"

TIER_COLORS = {
    "RESTRICTION":          "#c0392b",
    "HIGH_RISK":            "#d35400",
    "DECISION":             "#2980b9",
    "QUALIFIED_RESTRICTION":"#8e44ad",
}
DONOR_COLORS = {
    "BHA":  "#1abc9c",
    "ECHO": "#e67e22",
}
DOMAIN_ORDER = [
    "PROCUREMENT", "ELIGIBILITY", "REPORTING",
    "FINANCIAL", "RECORD_KEEPING", "SAFEGUARDING", "SCOPE"
]
TIER_ORDER = ["RESTRICTION", "HIGH_RISK", "QUALIFIED_RESTRICTION", "DECISION"]


def build_sankey_data() -> dict:
    nodes = []
    links = []
    node_index = {}

    def get_or_add(name, layer, color, meta=None):
        if name not in node_index:
            node_index[name] = len(nodes)
            entry = {"name": name, "layer": layer, "color": color}
            if meta:
                entry.update(meta)
            nodes.append(entry)
        return node_index[name]

    donor_files = sorted(OUTPUT_DIR.glob("*.json"))
    donor_data = {}
    for path in donor_files:
        if path.name in ("flow_data.json",):
            continue
        raw = json.loads(path.read_text())
        donor_data[raw["donor"]] = raw["clauses"]

    # Layer 0: donor nodes (ordered BHA first, then ECHO)
    for donor in sorted(donor_data.keys()):
        get_or_add(donor, 0, DONOR_COLORS.get(donor, "#aaa"))

    # Layer 1: domain nodes (donor-specific, ordered by DOMAIN_ORDER)
    for donor in sorted(donor_data.keys()):
        clauses = donor_data[donor]
        domains_present = sorted(
            set(c.get("domain") for c in clauses if c.get("domain")),
            key=lambda d: DOMAIN_ORDER.index(d) if d in DOMAIN_ORDER else 99,
        )
        for domain in domains_present:
            get_or_add(
                f"{donor}·{domain}", 1,
                DONOR_COLORS.get(donor, "#aaa"),
                {"donor": donor, "domain": domain},
            )

    # Layer 2: tier nodes (shared, ordered by TIER_ORDER)
    for tier in TIER_ORDER:
        # only add if referenced
        pass  # added on demand below

    # Build links + tier nodes
    for donor in sorted(donor_data.keys()):
        clauses = donor_data[donor]
        di = node_index[donor]

        domain_counts = Counter(c.get("domain") for c in clauses if c.get("domain"))
        domain_tier_counts = Counter(
            (c.get("domain"), c.get("tier"))
            for c in clauses if c.get("domain") and c.get("tier")
        )

        # collect clause snippets per domain×tier for tooltips
        domain_tier_clauses = {}
        for c in clauses:
            key = (c.get("domain"), c.get("tier"))
            if key not in domain_tier_clauses:
                domain_tier_clauses[key] = []
            domain_tier_clauses[key].append({
                "clause_id": c.get("clause_id", ""),
                "text": (c.get("text") or "")[:180],
                "dead_end_type": c.get("dead_end_type"),
            })

        # donor → domain links
        for domain, count in sorted(domain_counts.items(), key=lambda x: DOMAIN_ORDER.index(x[0]) if x[0] in DOMAIN_ORDER else 99):
            links.append({
                "source": donor, "target": f"{donor}·{domain}",
                "value": count,
                "color": DONOR_COLORS.get(donor, "#aaa"),
                "donor": donor, "domain": domain,
                "label": f"{donor} → {domain}: {count} clauses",
                "clauses": [],
            })

        # domain → tier links
        for (domain, tier), count in sorted(domain_tier_counts.items()):
            if not domain or not tier:
                continue
            get_or_add(tier, 2, TIER_COLORS.get(tier, "#888"))
            links.append({
                "source": f"{donor}·{domain}", "target": tier,
                "value": count,
                "color": TIER_COLORS.get(tier, "#888"),
                "donor": donor, "domain": domain, "tier": tier,
                "label": f"{donor} · {domain} → {tier}: {count} clauses",
                "clauses": domain_tier_clauses.get((domain, tier), [])[:5],
            })

    return {"nodes": nodes, "links": links}


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>regmap — Sankey</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #0f1117; color: #e0e0e0; }

header {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 24px; background: #1a1d27; border-bottom: 1px solid #2a2d3e;
}
header h1 { font-size: 1.1rem; font-weight: 600; letter-spacing: .03em; }
header p  { font-size: .8rem; color: #888; }

#chart { width: 100%; height: calc(100vh - 56px); }

#tooltip {
  position: fixed; background: #1a1d27; border: 1px solid #3a3d4e;
  border-radius: 8px; padding: 12px 16px; font-size: .78rem;
  max-width: 400px; pointer-events: none; opacity: 0;
  transition: opacity .15s; z-index: 100; line-height: 1.6;
}
#tooltip .tt-header { font-weight: 600; margin-bottom: 8px; }
#tooltip .tt-clause {
  color: #ccc; margin-bottom: 5px;
  border-left: 2px solid #3a3d4e; padding-left: 8px;
  font-size: .74rem;
}
#tooltip .tt-cid { color: #666; font-size: .67rem; margin-bottom: 2px; }
#tooltip .tt-de  { color: #e67e22; font-size: .67rem; }

#legend {
  position: fixed; bottom: 20px; left: 20px;
  background: #1a1d27cc; border: 1px solid #2a2d3e;
  border-radius: 8px; padding: 12px 16px; font-size: .75rem;
  backdrop-filter: blur(4px);
}
#legend h3 {
  font-size: .68rem; color: #666; text-transform: uppercase;
  letter-spacing: .08em; margin-bottom: 8px;
}
.legend-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 6px; }
.legend-item { display: flex; align-items: center; gap: 6px; color: #999; }
.legend-dot { width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0; }
.legend-sep { border-top: 1px solid #2a2d3e; margin: 8px 0; }
</style>
</head>
<body>

<header>
  <h1>regmap — Sankey</h1>
  <p>Donor → Domain → Tier &nbsp;·&nbsp; width = clause count &nbsp;·&nbsp; shared tier nodes show overlap</p>
</header>

<svg id="chart"></svg>
<div id="tooltip"></div>

<div id="legend">
  <h3>Donors</h3>
  <div class="legend-row" id="donor-legend"></div>
  <div class="legend-sep"></div>
  <h3>Tiers</h3>
  <div class="legend-row" id="tier-legend"></div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>
<script>
const DATA = __SANKEY_DATA__;

const TIER_COLORS = {
  RESTRICTION:           "#c0392b",
  HIGH_RISK:             "#d35400",
  DECISION:              "#2980b9",
  QUALIFIED_RESTRICTION: "#8e44ad",
};
const DONOR_COLORS = { BHA: "#1abc9c", ECHO: "#e67e22" };

// ── legend ───────────────────────────────────────────────────────────────────
Object.entries(DONOR_COLORS).forEach(([d, c]) => {
  document.getElementById("donor-legend").insertAdjacentHTML("beforeend",
    `<div class="legend-item"><div class="legend-dot" style="background:${c}"></div>${d}</div>`);
});
Object.entries(TIER_COLORS).forEach(([t, c]) => {
  document.getElementById("tier-legend").insertAdjacentHTML("beforeend",
    `<div class="legend-item"><div class="legend-dot" style="background:${c}"></div>${t.replace("_"," ")}</div>`);
});

// ── tooltip ───────────────────────────────────────────────────────────────────
const tooltip = document.getElementById("tooltip");

function showTooltip(e, link) {
  const clauses = link.clauses || [];
  const shown = clauses.slice(0, 4);
  const more  = clauses.length - shown.length;
  tooltip.innerHTML = `
    <div class="tt-header">${link.label}</div>
    ${shown.map(c => `
      <div class="tt-clause">
        <div class="tt-cid">${c.clause_id}${c.dead_end_type ? ` · <span class="tt-de">${c.dead_end_type}</span>` : ""}</div>
        ${c.text}
      </div>`).join("")}
    ${more > 0 ? `<div style="color:#666;font-size:.7rem;margin-top:4px">+${more} more</div>` : ""}
  `;
  tooltip.style.opacity = 1;
  moveTooltip(e);
}

function showNodeTooltip(e, node) {
  tooltip.innerHTML = `<div class="tt-header">${node.name}</div>
    <div style="color:#aaa;font-size:.8rem">Total flow: ${node.value} clauses</div>`;
  tooltip.style.opacity = 1;
  moveTooltip(e);
}

function moveTooltip(e) {
  tooltip.style.left = (e.clientX + 16) + "px";
  tooltip.style.top  = (e.clientY - 10) + "px";
}

function hideTooltip() { tooltip.style.opacity = 0; }

// ── draw ──────────────────────────────────────────────────────────────────────
const svg    = d3.select("#chart");
const width  = document.getElementById("chart").clientWidth;
const height = document.getElementById("chart").clientHeight;
svg.attr("viewBox", `0 0 ${width} ${height}`);

const { sankey, sankeyLinkHorizontal } = d3;

const sankeyLayout = sankey()
  .nodeId(d => d.name)
  .nodeWidth(18)
  .nodePadding(14)
  .extent([[60, 20], [width - 160, height - 20]]);

// deep-clone to avoid mutation
const graph = sankeyLayout({
  nodes: DATA.nodes.map(d => ({ ...d })),
  links: DATA.links.map(d => ({ ...d })),
});

const defs = svg.append("defs");

// gradient per link
graph.links.forEach((link, i) => {
  const id = `grad-${i}`;
  const grad = defs.append("linearGradient")
    .attr("id", id)
    .attr("gradientUnits", "userSpaceOnUse")
    .attr("x1", link.source.x1).attr("x2", link.target.x0);
  grad.append("stop").attr("offset", "0%")
    .attr("stop-color", link.source.color || "#888")
    .attr("stop-opacity", 0.55);
  grad.append("stop").attr("offset", "100%")
    .attr("stop-color", link.color || link.target.color || "#888")
    .attr("stop-opacity", 0.55);
  link._gradId = id;
});

// links
svg.append("g")
  .selectAll("path")
  .data(graph.links)
  .join("path")
    .attr("d", sankeyLinkHorizontal())
    .attr("fill", "none")
    .attr("stroke", d => `url(#${d._gradId})`)
    .attr("stroke-width", d => Math.max(1, d.width))
    .style("cursor", "pointer")
    .on("mouseover", (e, d) => showTooltip(e, d))
    .on("mousemove", moveTooltip)
    .on("mouseout",  hideTooltip);

// nodes
const nodeG = svg.append("g")
  .selectAll("g")
  .data(graph.nodes)
  .join("g")
    .style("cursor", "default")
    .on("mouseover", (e, d) => showNodeTooltip(e, d))
    .on("mousemove", moveTooltip)
    .on("mouseout",  hideTooltip);

nodeG.append("rect")
  .attr("x", d => d.x0)
  .attr("y", d => d.y0)
  .attr("width",  d => d.x1 - d.x0)
  .attr("height", d => Math.max(1, d.y1 - d.y0))
  .attr("fill",   d => d.color || "#aaa")
  .attr("rx", 3);

// labels
nodeG.append("text")
  .attr("x", d => d.layer === 2 ? d.x1 + 8 : d.x0 - 8)
  .attr("y", d => (d.y0 + d.y1) / 2)
  .attr("dy", "0.35em")
  .attr("text-anchor", d => d.layer === 2 ? "start" : "end")
  .attr("font-size", d => d.layer === 0 ? 13 : 11)
  .attr("font-weight", d => d.layer === 0 ? 600 : 400)
  .attr("fill", d => d.layer === 0 ? d.color : "#aaa")
  .text(d => {
    if (d.layer === 0) return d.name;
    if (d.layer === 1) return d.domain;   // strip donor prefix
    return d.name.replace("_", " ");
  });

// value labels on nodes (count)
nodeG.filter(d => (d.y1 - d.y0) > 18)
  .append("text")
  .attr("x", d => (d.x0 + d.x1) / 2)
  .attr("y", d => (d.y0 + d.y1) / 2)
  .attr("dy", "0.35em")
  .attr("text-anchor", "middle")
  .attr("font-size", 9)
  .attr("fill", "rgba(255,255,255,0.7)")
  .text(d => d.value);

// layer labels at top
const layers = [
  { x: graph.nodes.find(n => n.layer === 0)?.x0 ?? 60, label: "Donor" },
  { x: graph.nodes.find(n => n.layer === 1)?.x0 ?? 300, label: "Domain" },
  { x: graph.nodes.find(n => n.layer === 2)?.x0 ?? 600, label: "Tier" },
];
svg.append("g")
  .selectAll("text")
  .data(layers)
  .join("text")
    .attr("x", d => d.x)
    .attr("y", 10)
    .attr("font-size", 9)
    .attr("fill", "#555")
    .attr("text-transform", "uppercase")
    .attr("letter-spacing", "0.08em")
    .text(d => d.label);
</script>
</body>
</html>
"""


def build_viz(data: dict) -> None:
    html = HTML_TEMPLATE.replace("__SANKEY_DATA__", json.dumps(data))
    SANKEY_PATH.write_text(html)
    print(f"Written: {SANKEY_PATH}")


if __name__ == "__main__":
    print("Building Sankey data…")
    data = build_sankey_data()
    print(f"  {len(data['nodes'])} nodes, {len(data['links'])} links")
    print("Building visualization…")
    build_viz(data)
    print("Done.")
