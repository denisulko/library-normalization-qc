"""Synthetic NGS library quantification generator for normalization QC testing.

Generates a reproducible sample sheet containing fluorometric concentrations
(e.g., Qubit dsDNA HS/BR in ng/uL) and available eluate volumes (uL).
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def generate_sample_sheet(
    num_samples: int = 24,
    min_conc: float = 4.0,
    max_conc: float = 35.0,
    min_vol: float = 8.0,
    max_vol: float = 40.0,
    seed: int | None = 42,
) -> pd.DataFrame:
    """Generate synthetic library concentration and volume measurements."""
    rng = random.Random(seed)
    samples = []
    for i in range(1, num_samples + 1):
        samples.append(
            {
                "sample_id": f"S{i:02d}",
                "conc_ng_ul": round(rng.uniform(min_conc, max_conc), 1),
                "volume_ul": round(rng.uniform(min_vol, max_vol), 1),
            }
        )
    return pd.DataFrame(samples)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/raw/sample_sheet.csv",
        help="Destination CSV path (default: data/raw/sample_sheet.csv)",
    )
    parser.add_argument("--count", type=int, default=24, help="Number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args(argv)

    df = generate_sample_sheet(num_samples=args.count, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Generated {len(df)} samples -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
