import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def write_result(result: dict, filename: str) -> Path:
    """Write a classifier result dict to output/<filename>.json.

    Args:
        result: structured output dict from classifier.classify()
        filename: original PDF filename (used to derive the output path)

    Returns:
        Path to the written JSON file
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(filename).stem
    out_path = OUTPUT_DIR / f"{stem}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return out_path
