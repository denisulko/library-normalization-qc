"""Mass-concentration normalization planner for sequencing libraries.

This planner models dilution in ng/uL. It does NOT calculate molarity, account
for library fragment length, or generate instrument-ready liquid-handler files.
Only PASS rows contain actionable transfer volumes.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = {"sample_id", "conc_ng_ul", "volume_ul"}
OUTPUT_COLUMNS = [
    "sample_id",
    "conc_ng_ul",
    "volume_ul",
    "required_sample_volume_ul",
    "sample_volume_ul",
    "buffer_volume_ul",
    "predicted_conc_ng_ul",
    "status",
    "reason",
]


@dataclass(frozen=True)
class Config:
    target_ng_ul: float = 10.0
    final_volume_ul: float = 20.0
    min_transfer_ul: float = 1.0
    max_error_pct: float = 0.5

    def __post_init__(self) -> None:
        for name in ("target_ng_ul", "final_volume_ul", "min_transfer_ul"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")
        if not math.isfinite(self.max_error_pct) or not 0 <= self.max_error_pct < 100:
            raise ValueError("max_error_pct must be finite and between 0 and 100")
        if self.min_transfer_ul > self.final_volume_ul:
            raise ValueError("min_transfer_ul cannot exceed final_volume_ul")


def parse_measurement(value: object, *, allow_zero: bool = False) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("not a number") from exc
    if not math.isfinite(number) or number < 0 or (number == 0 and not allow_zero):
        raise ValueError("invalid or non-positive measurement")
    return number


def normalize_row(row: dict[str, str], config: Config, duplicated: bool = False) -> dict:
    """Calculate one row; FAIL rows never contain executable transfer volumes."""
    sample_id = (row.get("sample_id") or "").strip()
    result = {
        "sample_id": sample_id,
        "conc_ng_ul": row.get("conc_ng_ul", ""),
        "volume_ul": row.get("volume_ul", ""),
        "required_sample_volume_ul": "",
        "sample_volume_ul": "",
        "buffer_volume_ul": "",
        "predicted_conc_ng_ul": "",
        "status": "FAIL",
        "reason": "",
    }

    if not sample_id:
        result["reason"] = "missing_sample_id"
        return result
    if duplicated:
        result["reason"] = "duplicate_sample_id"
        return result

    try:
        concentration = parse_measurement(row.get("conc_ng_ul"))
    except ValueError:
        result["reason"] = "invalid_concentration"
        return result

    try:
        available = parse_measurement(row.get("volume_ul"), allow_zero=True)
    except ValueError:
        result["reason"] = "invalid_available_volume"
        return result

    required = config.target_ng_ul * config.final_volume_ul / concentration
    result["required_sample_volume_ul"] = f"{required:.4f}"

    if concentration < config.target_ng_ul:
        result["reason"] = "stock_below_target"
        return result

    # Volumes are rounded to 0.01 uL; resulting concentration is checked.
    sample = round(required, 2)
    buffer = round(config.final_volume_ul - sample, 2)
    if sample > available + 1e-9:
        result["reason"] = "insufficient_volume"
        return result
    if sample < config.min_transfer_ul - 1e-9:
        result["reason"] = "sample_below_min_transfer"
        return result
    if 0 < buffer < config.min_transfer_ul - 1e-9:
        result["reason"] = "buffer_below_min_transfer"
        return result
    if buffer < 0:
        result["reason"] = "stock_below_target"
        return result

    predicted = concentration * sample / config.final_volume_ul
    error_pct = 100 * abs(predicted - config.target_ng_ul) / config.target_ng_ul
    if error_pct > config.max_error_pct + 1e-9:
        result["reason"] = "rounding_out_of_tolerance"
        return result

    result.update(
        sample_volume_ul=f"{sample:.2f}",
        buffer_volume_ul=f"{buffer:.2f}",
        predicted_conc_ng_ul=f"{predicted:.4f}",
        status="PASS",
        reason="ok",
    )
    return result


def normalize_records(rows: list[dict[str, str]], config: Config) -> list[dict]:
    ids = [(row.get("sample_id") or "").strip() for row in rows]
    counts = Counter(sample_id for sample_id in ids if sample_id)
    return [
        normalize_row(row, config, duplicated=counts[ids[i]] > 1 if ids[i] else False)
        for i, row in enumerate(rows)
    ]


def read_samples(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(
                "Input CSV needs columns: sample_id, conc_ng_ul, volume_ul"
            )
        rows = list(reader)
    if not rows:
        raise ValueError("Input CSV contains no samples")
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict], config: Config, path: Path) -> dict:
    reasons = Counter(row["reason"] for row in rows if row["status"] == "FAIL")
    report = {
        "configuration": asdict(config),
        "total": len(rows),
        "passed": sum(row["status"] == "PASS" for row in rows),
        "failed": sum(row["status"] == "FAIL" for row in rows),
        "failure_reasons": dict(sorted(reasons.items())),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/sample_sheet.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "results/normalized_samples.csv")
    parser.add_argument("--summary", type=Path, default=ROOT / "results/qc_summary.json")
    parser.add_argument("--target-ng-ul", type=float, default=10.0)
    parser.add_argument("--final-volume-ul", type=float, default=20.0)
    parser.add_argument("--min-transfer-ul", type=float, default=1.0)
    parser.add_argument("--max-error-pct", type=float, default=0.5)
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any sample fails QC")
    args = parser.parse_args(argv)
    try:
        config = Config(
            target_ng_ul=args.target_ng_ul,
            final_volume_ul=args.final_volume_ul,
            min_transfer_ul=args.min_transfer_ul,
            max_error_pct=args.max_error_pct,
        )
        records = normalize_records(read_samples(args.input), config)
        write_csv(records, args.output)
        summary = write_summary(records, config, args.summary)
    except (OSError, ValueError, csv.Error, OverflowError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(
        f"Processed {summary['total']} libraries: "
        f"{summary['passed']} PASS, {summary['failed']} FAIL"
    )
    print(f"Transfer plan: {args.output}\nQC summary: {args.summary}")
    return 1 if args.strict and summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
