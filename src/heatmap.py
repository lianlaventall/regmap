"""
heatmap.py — Build cross-donor heatmap visualization.

Outputs:
  output/heatmap.html  — self-contained interactive D3.js heatmap

Two panels:
  1. Clause density heatmap: domain × tier, normalized per donor
  2. Dead end heatmap: domain × dead_end_type, per donor

Cross-donor: domains where both donors share UNCONDITIONAL dead ends are
highlighted in the row header.
"""

import json
from collections import defaultdict
from pathlib import Path

OUTPUT_DIR = Path("output")
HEATMAP_PATH = OUTPUT_DIR / "heatmap.html"

TIERS = ["RESTRICTION", "HIGH_RISK", "DECISION", "QUALIFIED_RESTRICTION"]
DEAD_END_TYPES = ["UNCONDITIONAL", "CONDITIONAL", "AMBIGUOUS"]
DOMAINS = ["PROCUREMENT", "ELIGIBILITY", "REPORTING", "FINANCIAL", "RECORD_KEEPING", "SAFEGUARDING", "SCOPE"]


def build_heatmap_data() -> dict:
    donors = {}

    for path in sorted(OUTPUT_DIR.glob("*.json")):
        if path.name in ("flow_data.json",):
            continue
        raw = json.loads(path.read_text())
        donor = raw["donor"]
        clauses = raw["clauses"]
        n = len(clauses)

        # domain × tier cells
        cells = defaultdict(lambda: defaultdict(lambda: {"count": 0, "pct": 0.0, "clauses": []}))
        # domain × dead_end_type cells
        de_cells = defaultdict(lambda: defaultdict(lambda: {"count": 0, "pct": 0.0, "clauses": []}))
        domain_totals = defaultdict(int)

        for c in clauses:
            domain = c.get("domain") or "UNKNOWN"
            tier = c.get("tier") or "UNKNOWN"
            det = c.get("dead_end_type")

            domain_totals[domain] += 1

            snippet = {
                "clause_id": c.get("clause_id", ""),
                "text": c.get("text", "")[:200],
                "dead_end": c.get("dead_end", False),
                "dead_end_type": det,
            }

            cells[domain][tier]["count"] += 1
            cells[domain][tier]["clauses"].append(snippet)

            if det:
                de_cells[domain][det]["count"] += 1
                de_cells[domain][det]["clauses"].append(snippet)

        # compute pct (of donor total)
        for domain in cells:
            for tier in cells[domain]:
                cells[domain][tier]["pct"] = round(cells[domain][tier]["count"] / n * 100, 1)

        for domain in de_cells:
            dtotal = domain_totals[domain]
            for det in de_cells[domain]:
                de_cells[domain][det]["pct"] = round(de_cells[domain][det]["count"] / dtotal * 100, 1)

        # domains present in this donor
        active_domains = sorted(domain_totals.keys(), key=lambda d: DOMAINS.index(d) if d in DOMAINS else 99)

        donors[donor] = {
            "total": n,
            "cells": {d: dict(cells[d]) for d in active_domains},
            "de_cells": {d: dict(de_cells[d]) for d in active_domains},
            "active_domains": active_domains,
            "domain_totals": dict(domain_totals),
        }

    # cross-donor: domains where BOTH donors have >= 1 UNCONDITIONAL dead end
    all_donors = list(donors.keys())
    shared_unconditional = set()
    if len(all_donors) >= 2:
        sets = []
        for donor in all_donors:
            s = set()
            for domain, de_map in donors[donor]["de_cells"].items():
                if de_map.get("UNCONDITIONAL", {}).get("count", 0) > 0:
                    s.add(domain)
            sets.append(s)
        shared_unconditional = set.intersection(*sets) if sets else set()

    return {
        "donors": donors,
        "all_domains": DOMAINS,
        "tiers": TIERS,
        "dead_end_types": DEAD_END_TYPES,
        "shared_unconditional_domains": list(shared_unconditional),
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>regmap — Heatmap</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #0f1117; color: #e0e0e0; }

header {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 24px; background: #1a1d27; border-bottom: 1px solid #2a2d3e;
}
header h1 { font-size: 1.1rem; font-weight: 600; letter-spacing: .03em; }
header span { font-size: .8rem; color: #888; }

.tab-bar {
  display: flex; gap: 0; padding: 0 24px;
  background: #1a1d27; border-bottom: 1px solid #2a2d3e;
}
.tab {
  padding: 10px 20px; font-size: .85rem; cursor: pointer;
  border-bottom: 3px solid transparent; color: #888;
  transition: color .15s, border-color .15s;
}
.tab.active { color: #e0e0e0; border-bottom-color: #3498db; }
.tab:hover { color: #e0e0e0; }

.panel { display: none; padding: 28px 24px; }
.panel.active { display: block; }

.section-title {
  font-size: .7rem; text-transform: uppercase; letter-spacing: .1em;
  color: #666; margin-bottom: 16px;
}

.grids {
  display: flex; gap: 40px; flex-wrap: wrap;
}

.grid-wrap { flex: 1; min-width: 300px; }
.grid-wrap h2 {
  font-size: .9rem; font-weight: 600; margin-bottom: 14px; color: #ccc;
}
.donor-meta { font-size: .75rem; color: #666; margin-bottom: 12px; }

table.heatmap {
  border-collapse: separate; border-spacing: 3px;
  font-size: .75rem;
}
table.heatmap th {
  font-weight: 500; color: #888; padding: 4px 8px;
  text-align: center; white-space: nowrap;
}
table.heatmap th.domain-header {
  text-align: right; padding-right: 12px; font-size: .72rem;
  min-width: 130px;
}
table.heatmap td {
  width: 80px; height: 48px; text-align: center; vertical-align: middle;
  border-radius: 4px; cursor: default; position: relative;
  transition: filter .15s;
}
table.heatmap td:hover { filter: brightness(1.3); cursor: pointer; }
table.heatmap td .cell-count { font-size: .85rem; font-weight: 600; }
table.heatmap td .cell-pct  { font-size: .68rem; color: rgba(255,255,255,.55); }

.domain-label { font-size: .72rem; text-align: right; padding-right: 12px; color: #aaa; }
.domain-label.shared-unconditional { color: #f1c40f; font-weight: 600; }
.shared-badge {
  font-size: .6rem; background: #f1c40f22; color: #f1c40f;
  border: 1px solid #f1c40f55; border-radius: 3px;
  padding: 1px 4px; margin-left: 6px; vertical-align: middle;
}

.empty-cell { background: #1a1d27; color: #333; }

#tooltip {
  position: fixed; background: #1a1d27; border: 1px solid #3a3d4e;
  border-radius: 8px; padding: 12px 16px; font-size: .78rem;
  max-width: 420px; pointer-events: none; opacity: 0;
  transition: opacity .15s; z-index: 200; line-height: 1.6;
}
#tooltip .tt-header { font-weight: 600; margin-bottom: 8px; }
#tooltip .tt-clause { color: #ccc; margin-bottom: 6px; border-left: 2px solid #3a3d4e; padding-left: 8px; }
#tooltip .tt-cid { font-size: .68rem; color: #666; margin-bottom: 2px; }
#tooltip .tt-de { font-size: .68rem; color: #e67e22; }

.legend-row {
  display: flex; gap: 20px; flex-wrap: wrap; margin-top: 24px;
}
.legend-item { display: flex; align-items: center; gap: 8px; font-size: .75rem; color: #888; }
.legend-swatch { width: 18px; height: 18px; border-radius: 3px; }

.divider { border: none; border-top: 1px solid #2a2d3e; margin: 32px 0; }
</style>
</head>
<body>

<header>
  <h1>regmap — Heatmap</h1>
  <span>Cross-donor clause density &amp; dead end analysis</span>
</header>

<div class="tab-bar">
  <div class="tab active" data-panel="density">Clause Density</div>
  <div class="tab" data-panel="deadends">Dead End Analysis</div>
</div>

<div id="density" class="panel active"></div>
<div id="deadends" class="panel"></div>
<div id="tooltip"></div>

<script>
const DATA = __HEATMAP_DATA__;

const TIER_COLORS = {
  RESTRICTION:          "#c0392b",
  HIGH_RISK:            "#d35400",
  DECISION:             "#2980b9",
  QUALIFIED_RESTRICTION:"#8e44ad",
};

const DE_COLORS = {
  UNCONDITIONAL: "#e74c3c",
  CONDITIONAL:   "#e67e22",
  AMBIGUOUS:     "#f39c12",
};

const tooltip = document.getElementById("tooltip");
const sharedSet = new Set(DATA.shared_unconditional_domains);

// ── helpers ──────────────────────────────────────────────────────────────────

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return [r,g,b];
}

function cellBg(baseHex, pct) {
  if (pct === 0) return null;
  const [r,g,b] = hexToRgb(baseHex);
  const alpha = 0.12 + (pct / 100) * 0.75;
  return `rgba(${r},${g},${b},${alpha.toFixed(2)})`;
}

function showTooltip(e, header, clauses) {
  if (!clauses || clauses.length === 0) return;
  const shown = clauses.slice(0, 4);
  const more = clauses.length - shown.length;
  tooltip.innerHTML = `
    <div class="tt-header">${header}</div>
    ${shown.map(c => `
      <div class="tt-clause">
        <div class="tt-cid">${c.clause_id}${c.dead_end_type ? ` · <span class="tt-de">${c.dead_end_type}</span>` : ""}</div>
        <div>${c.text}</div>
      </div>
    `).join("")}
    ${more > 0 ? `<div style="color:#666;font-size:.7rem;margin-top:4px">+${more} more</div>` : ""}
  `;
  tooltip.style.opacity = 1;
  moveTooltip(e);
}

function moveTooltip(e) {
  const tx = e.clientX + 16;
  const ty = e.clientY - 10;
  tooltip.style.left = tx + "px";
  tooltip.style.top  = ty + "px";
}

function hideTooltip() { tooltip.style.opacity = 0; }

// ── build a heatmap table ────────────────────────────────────────────────────

function buildTable(donorKey, donorData, cols, colorMap, cellKey) {
  const { total, active_domains, domain_totals } = donorData;

  const table = document.createElement("table");
  table.className = "heatmap";

  // header row
  const thead = table.createTHead();
  const hr = thead.insertRow();
  const thEmpty = document.createElement("th");
  thEmpty.className = "domain-header";
  hr.appendChild(thEmpty);
  cols.forEach(col => {
    const th = document.createElement("th");
    th.textContent = col.replace("_", " ");
    th.style.color = colorMap[col] || "#aaa";
    hr.appendChild(th);
  });

  // body rows — only active domains
  const tbody = table.createTBody();
  const activeDomains = DATA.all_domains.filter(d => active_domains.includes(d));

  activeDomains.forEach(domain => {
    const row = tbody.insertRow();
    const domainCell = row.insertCell();
    domainCell.className = "domain-label" + (sharedSet.has(domain) ? " shared-unconditional" : "");
    domainCell.innerHTML = domain + (sharedSet.has(domain) ? `<span class="shared-badge">↔ shared</span>` : "");

    const cellMap = donorData[cellKey][domain] || {};

    cols.forEach(col => {
      const td = row.insertCell();
      const info = cellMap[col];
      if (!info || info.count === 0) {
        td.className = "empty-cell";
        td.innerHTML = `<span class="cell-count" style="opacity:.2">—</span>`;
        return;
      }
      const bg = cellBg(colorMap[col] || "#888", info.pct);
      td.style.background = bg;
      td.innerHTML = `
        <div class="cell-count">${info.count}</div>
        <div class="cell-pct">${info.pct}%</div>
      `;

      td.addEventListener("mouseover", e => {
        showTooltip(e, `${donorKey} · ${domain} · ${col} (${info.count} clauses)`, info.clauses);
      });
      td.addEventListener("mousemove", moveTooltip);
      td.addEventListener("mouseout", hideTooltip);
    });
  });

  return table;
}

// ── render panels ────────────────────────────────────────────────────────────

function renderDensity() {
  const panel = document.getElementById("density");
  panel.innerHTML = "";

  const title = document.createElement("div");
  title.className = "section-title";
  title.textContent = "Clause density by domain × tier — normalized to each donor's total (hover cells for clauses)";
  panel.appendChild(title);

  const grids = document.createElement("div");
  grids.className = "grids";
  panel.appendChild(grids);

  Object.entries(DATA.donors).forEach(([donor, donorData]) => {
    const wrap = document.createElement("div");
    wrap.className = "grid-wrap";

    const h2 = document.createElement("h2");
    h2.textContent = donor;
    wrap.appendChild(h2);

    const meta = document.createElement("div");
    meta.className = "donor-meta";
    meta.textContent = `${donorData.total} clauses total`;
    wrap.appendChild(meta);

    const table = buildTable(donor, donorData, DATA.tiers, TIER_COLORS, "cells");
    wrap.appendChild(table);
    grids.appendChild(wrap);
  });

  // legend
  const legend = document.createElement("div");
  legend.className = "legend-row";
  DATA.tiers.forEach(t => {
    const item = document.createElement("div");
    item.className = "legend-item";
    item.innerHTML = `<div class="legend-swatch" style="background:${TIER_COLORS[t]}"></div>${t.replace("_"," ")}`;
    legend.appendChild(item);
  });
  if (sharedSet.size > 0) {
    const item = document.createElement("div");
    item.className = "legend-item";
    item.innerHTML = `<div class="legend-swatch" style="background:#f1c40f22;border:1px solid #f1c40f55"></div>Shared UNCONDITIONAL dead end domain`;
    legend.appendChild(item);
  }
  panel.appendChild(legend);
}

function renderDeadEnds() {
  const panel = document.getElementById("deadends");
  panel.innerHTML = "";

  const title = document.createElement("div");
  title.className = "section-title";
  title.textContent = "Dead end density by domain × type — % of domain clause total (hover for clauses)";
  panel.appendChild(title);

  const grids = document.createElement("div");
  grids.className = "grids";
  panel.appendChild(grids);

  Object.entries(DATA.donors).forEach(([donor, donorData]) => {
    const wrap = document.createElement("div");
    wrap.className = "grid-wrap";

    const h2 = document.createElement("h2");
    h2.textContent = donor;
    wrap.appendChild(h2);

    const meta = document.createElement("div");
    meta.className = "donor-meta";

    const total_de = Object.values(donorData.de_cells).reduce((sum, dm) => {
      return sum + Object.values(dm).reduce((s, v) => s + v.count, 0);
    }, 0);
    meta.textContent = `${total_de} dead ends across ${donorData.total} clauses`;
    wrap.appendChild(meta);

    const table = buildTable(donor, donorData, DATA.dead_end_types, DE_COLORS, "de_cells");
    wrap.appendChild(table);
    grids.appendChild(wrap);
  });

  // shared unconditional callout
  if (sharedSet.size > 0) {
    const hr = document.createElement("hr");
    hr.className = "divider";
    panel.appendChild(hr);

    const callout = document.createElement("div");
    callout.style.cssText = "background:#1a1d27;border:1px solid #f1c40f33;border-radius:8px;padding:16px 20px;max-width:600px;";
    callout.innerHTML = `
      <div style="font-size:.75rem;color:#f1c40f;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">Cross-donor pooling candidates</div>
      <div style="font-size:.82rem;color:#ccc;line-height:1.6;">
        Domains with UNCONDITIONAL dead ends in <strong>both donors</strong>:
        <strong style="color:#f1c40f">${[...sharedSet].join(", ")}</strong>.
        These are the strongest candidates for a shared compliance baseline.
      </div>
    `;
    panel.appendChild(callout);
  } else {
    const callout = document.createElement("div");
    callout.style.cssText = "background:#1a1d27;border:1px solid #2a2d3e;border-radius:8px;padding:16px 20px;max-width:600px;margin-top:24px;";
    callout.innerHTML = `
      <div style="font-size:.82rem;color:#888;line-height:1.6;">
        No domains currently share UNCONDITIONAL dead ends across both donors.
        Cross-donor pooling will require domain-level normalization first.
      </div>
    `;
    panel.appendChild(callout);
  }

  // legend
  const legend = document.createElement("div");
  legend.className = "legend-row";
  legend.style.marginTop = "24px";
  DATA.dead_end_types.forEach(t => {
    const item = document.createElement("div");
    item.className = "legend-item";
    item.innerHTML = `<div class="legend-swatch" style="background:${DE_COLORS[t]}"></div>${t}`;
    legend.appendChild(item);
  });
  panel.appendChild(legend);
}

// ── tabs ─────────────────────────────────────────────────────────────────────

document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.panel).classList.add("active");
  });
});

renderDensity();
renderDeadEnds();
</script>
</body>
</html>
"""


def build_viz(data: dict) -> None:
    html = HTML_TEMPLATE.replace("__HEATMAP_DATA__", json.dumps(data))
    HEATMAP_PATH.write_text(html)
    print(f"Written: {HEATMAP_PATH}")


if __name__ == "__main__":
    print("Building heatmap data…")
    data = build_heatmap_data()
    donors = data["donors"]
    for donor, d in donors.items():
        print(f"  {donor}: {d['total']} clauses, domains: {d['active_domains']}")
    print(f"  Shared UNCONDITIONAL domains: {data['shared_unconditional_domains'] or 'none'}")
    print("Building visualization…")
    build_viz(data)
    print("Done.")
