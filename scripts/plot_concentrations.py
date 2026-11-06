"""Plot library stock concentration distribution against target normalization threshold."""

from __future__ import annotations

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]


def plot_concentration_distribution(
    input_csv: Path,
    output_png: Path,
    target_conc: float = 10.0,
) -> None:
    """Render publication-quality histogram and KDE of library stock concentrations."""
    df = pd.read_csv(input_csv)
    concs = pd.to_numeric(df["conc_ng_ul"], errors="coerce").dropna()

    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    bins = np.arange(0, max(40.0, concs.max() + 5.0), 4.0)
    sns.histplot(
        concs,
        bins=bins,
        kde=True,
        color="#2b5c8f",
        edgecolor="white",
        alpha=0.8,
        ax=ax,
        line_kws={"linewidth": 2.2, "color": "#16324f"},
    )

    # Highlight sub-target zone where dilution is physically impossible
    ax.axvspan(
        0,
        target_conc,
        color="#d9534f",
        alpha=0.12,
        label=f"Below Target (< {target_conc:.1f} ng/µL)",
    )
    ax.axvline(
        target_conc,
        color="#d9534f",
        linestyle="--",
        linewidth=2.2,
        label=f"Target Concentration ({target_conc:.1f} ng/µL)",
    )
    mean_val = concs.mean()
    median_val = concs.median()
    ax.axvline(
        mean_val,
        color="#2ca02c",
        linestyle="-.",
        linewidth=2.0,
        label=f"Mean ({mean_val:.1f} ng/µL)",
    )
    ax.axvline(
        median_val,
        color="#ff7f0e",
        linestyle=":",
        linewidth=2.0,
        label=f"Median ({median_val:.1f} ng/µL)",
    )

    ax.set_title(
        "NGS Library Stock Concentration Distribution (n = 24)",
        fontsize=15,
        fontweight="bold",
        pad=14,
    )
    ax.set_xlabel("Stock Concentration (ng/µL)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of Libraries", fontsize=12, fontweight="bold")
    ax.set_xlim(0, max(38.0, concs.max() + 3.0))
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, fontsize=10, loc="upper right")

    sns.despine(top=True, right=True)
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300)
    plt.close(fig)
    print(f"Saved concentration distribution plot -> {output_png}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "results/normalized_samples.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results/concentration_distribution.png",
    )
    parser.add_argument("--target-ng-ul", type=float, default=10.0)
    args = parser.parse_args(argv)
    plot_concentration_distribution(args.input, args.output, args.target_ng_ul)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
