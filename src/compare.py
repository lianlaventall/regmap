import json
from pathlib import Path

TIERS = ["RESTRICTION", "QUALIFIED_RESTRICTION", "HIGH_RISK", "DECISION"]


def normalize_comparison(*paths: str) -> dict:
    """Compare tier distributions across two or more output JSON files.

    Args:
        *paths: Paths to output JSON files. At least two required.

    Returns:
        Dict with per-document tier counts and percentages, plus diffs of
        percentage points for each document relative to the first (baseline).
    """
    if len(paths) < 2:
        raise ValueError("At least two paths are required for comparison.")

    docs = {}
    for path in paths:
        data = json.loads(Path(path).read_text())
        clauses = data["clauses"]
        total = len(clauses)
        tier_counts = {tier: 0 for tier in TIERS}
        for clause in clauses:
            tier = clause.get("tier")
            if tier in tier_counts:
                tier_counts[tier] += 1
        docs[data["donor"]] = {
            "document": data["document"],
            "total": total,
            "tiers": {
                tier: {
                    "count": tier_counts[tier],
                    "pct": round(tier_counts[tier] / total * 100, 1) if total else 0.0,
                }
                for tier in TIERS
            },
        }

    donors = list(docs.keys())
    baseline = donors[0]
    diffs = {
        donor: {
            "description": f"{donor} minus {baseline}",
            "tiers": {
                tier: round(
                    docs[donor]["tiers"][tier]["pct"] - docs[baseline]["tiers"][tier]["pct"], 1
                )
                for tier in TIERS
            },
        }
        for donor in donors[1:]
    }

    return {
        "documents": docs,
        "diff_pct_points": diffs,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m src.compare <path_1> <path_2> [path_3 ...]")
        sys.exit(1)

    result = normalize_comparison(*sys.argv[1:])

    donors = list(result["documents"].keys())
    baseline = donors[0]

    print(f"\n{'Tier':<25} ", end="")
    for donor in donors:
        print(f"{donor:>8} (n)  {donor:>6} (%)  ", end="")
    for donor in donors[1:]:
        print(f"Δ {donor} vs {baseline}  ", end="")
    print()
    print("-" * (25 + len(donors) * 22 + len(donors[1:]) * 20))

    for tier in TIERS:
        print(f"{tier:<25} ", end="")
        for donor in donors:
            t = result["documents"][donor]["tiers"][tier]
            print(f"{t['count']:>8}      {t['pct']:>6.1f}%  ", end="")
        for donor in donors[1:]:
            delta = result["diff_pct_points"][donor]["tiers"][tier]
            print(f"{delta:>+10.1f}          ", end="")
        print()

    print("-" * (25 + len(donors) * 22 + len(donors[1:]) * 20))
    print(f"{'TOTAL':<25} ", end="")
    for donor in donors:
        print(f"{result['documents'][donor]['total']:>8}      {'100.0':>6}%  ", end="")
    print()
