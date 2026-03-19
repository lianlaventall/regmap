import json
from pathlib import Path

TIERS = ["RESTRICTION", "QUALIFIED_RESTRICTION", "HIGH_RISK", "DECISION"]


def normalize_comparison(path_a: str, path_b: str) -> dict:
    """Compare tier distributions across two output JSON files.

    Args:
        path_a: Path to first output JSON file.
        path_b: Path to second output JSON file.

    Returns:
        Dict with per-document tier counts and percentages, plus a diff of
        percentage points between the two documents.
    """
    docs = {}
    for path in (path_a, path_b):
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

    donor_a, donor_b = list(docs.keys())
    diff = {
        tier: round(
            docs[donor_b]["tiers"][tier]["pct"] - docs[donor_a]["tiers"][tier]["pct"], 1
        )
        for tier in TIERS
    }

    return {
        "documents": docs,
        "diff_pct_points": {
            "description": f"{donor_b} minus {donor_a}",
            "tiers": diff,
        },
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python -m src.compare <path_a> <path_b>")
        sys.exit(1)

    result = normalize_comparison(sys.argv[1], sys.argv[2])

    donors = list(result["documents"].keys())
    print(f"\n{'Tier':<25} ", end="")
    for donor in donors:
        print(f"{donor:>8} (n)  {donor:>6} (%)  ", end="")
    print(f"{'Δ pct pts':>10}")
    print("-" * (25 + len(donors) * 22 + 12))

    for tier in TIERS:
        print(f"{tier:<25} ", end="")
        for donor in donors:
            t = result["documents"][donor]["tiers"][tier]
            print(f"{t['count']:>8}      {t['pct']:>6.1f}%  ", end="")
        print(f"{result['diff_pct_points']['tiers'][tier]:>+10.1f}")

    print("-" * (25 + len(donors) * 22 + 12))
    print(f"{'TOTAL':<25} ", end="")
    for donor in donors:
        print(f"{result['documents'][donor]['total']:>8}      {'100.0':>6}%  ", end="")
    print()
