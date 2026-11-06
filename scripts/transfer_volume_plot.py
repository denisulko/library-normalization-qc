"""Plot liquid-handler transfer volume distribution and plate-level pipetting plan."""

from __future__ import annotations

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]


def plot_transfer_volumes(
    input_csv: Path,
    output_png: Path,
    final_volume_ul: float = 20.0,
    min_transfer_ul: float = 1.0,
) -> None:
    """Render two-panel visualization of actionable pipetting volumes and per-sample plan."""
    df = pd.read_csv(input_csv)
    df["sample_volume_num"] = pd.to_numeric(df["sample_volume_ul"], errors="coerce")
    df["buffer_volume_num"] = pd.to_numeric(df["buffer_volume_ul"], errors="coerce")
    if "required_sample_volume_ul" in df.columns:
        df["required_num"] = pd.to_numeric(df["required_sample_volume_ul"], errors="coerce")
    else:
        df["required_num"] = df["sample_volume_num"]

    pass_df = df[df["status"] == "PASS"].copy()

    sns.set_theme(style="whitegrid", context="talk")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300, gridspec_kw={"width_ratios": [1, 1.35]})

    # Panel A: Actionable Sample Transfer Volume Distribution (PASS samples)
    sns.histplot(
        pass_df["sample_volume_num"],
        bins=8,
        kde=True,
        color="#1f77b4",
        edgecolor="white",
        alpha=0.82,
        ax=ax1,
        label="Sample Volume (µL)",
    )
    ax1.axvline(
        min_transfer_ul,
        color="#d9534f",
        linestyle="--",
        linewidth=2.0,
        label=f"Min Pipetting Limit ({min_transfer_ul:.1f} µL)",
    )
    ax1.axvline(
        pass_df["sample_volume_num"].mean(),
        color="#2ca02c",
        linestyle="-.",
        linewidth=2.0,
        label=f"Mean Sample Transfer ({pass_df['sample_volume_num'].mean():.2f} µL)",
    )
    ax1.set_title("A. Actionable Sample Transfer Volumes (PASS)", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("Sample Transfer Volume (µL)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Number of Libraries", fontsize=11, fontweight="bold")
    ax1.set_xlim(0, final_volume_ul + 1)
    ax1.legend(frameon=True, facecolor="white", fontsize=9.5, loc="upper right")

    # Panel B: Per-sample stacked pipetting plan across all 24 wells
    x = np.arange(len(df))
    sample_bars = df["sample_volume_num"].fillna(0.0).values
    buffer_bars = df["buffer_volume_num"].fillna(0.0).values

    ax2.bar(
        x,
        sample_bars,
        color="#1f77b4",
        edgecolor="black",
        linewidth=0.7,
        label="Library Input (µL)",
    )
    ax2.bar(
        x,
        buffer_bars,
        bottom=sample_bars,
        color="#a6cee3",
        edgecolor="black",
        linewidth=0.7,
        label="EB / TE Buffer (µL)",
    )

    # Mark failed samples clearly
    fail_indices = np.where(df["status"] != "PASS")[0]
    if len(fail_indices) > 0:
        ax2.bar(
            fail_indices,
            [final_volume_ul] * len(fail_indices),
            color="#d9534f",
            alpha=0.28,
            edgecolor="#d9534f",
            linestyle="--",
            linewidth=1.2,
            label="Excluded (QC FAIL)",
        )

    ax2.axhline(
        final_volume_ul,
        color="#333333",
        linestyle=":",
        linewidth=1.5,
        label=f"Target Final Volume ({final_volume_ul:.0f} µL)",
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["sample_id"], rotation=60, fontsize=9)
    ax2.set_title("B. Automated Liquid-Handler Worklist Profile (24 Libraries)", fontsize=13, fontweight="bold", pad=12)
    ax2.set_xlabel("Library ID", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Volume (µL)", fontsize=11, fontweight="bold")
    ax2.set_ylim(0, final_volume_ul * 1.22)
    ax2.legend(frameon=True, facecolor="white", fontsize=9, loc="upper right", ncol=2)

    sns.despine(top=True, right=True)
    fig.suptitle("NGS Library Normalization Transfer Volume Analysis", fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved transfer volume distribution plot -> {output_png}")


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
        default=ROOT / "results/transfer_volume_distribution.png",
    )
    parser.add_argument("--final-volume-ul", type=float, default=20.0)
    parser.add_argument("--min-transfer-ul", type=float, default=1.0)
    args = parser.parse_args(argv)
    plot_transfer_volumes(
        args.input,
        args.output,
        final_volume_ul=args.final_volume_ul,
        min_transfer_ul=args.min_transfer_ul,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
