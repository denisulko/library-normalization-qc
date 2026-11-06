"""Plot library normalization QC status and failure reason breakdown."""

from __future__ import annotations

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]

REASON_LABELS = {
    "ok": "PASS: Actionable Dilution",
    "stock_below_target": "FAIL: Stock < Target (<10 ng/µL)",
    "insufficient_volume": "FAIL: Insufficient Stock Volume",
    "sample_below_min_transfer": "FAIL: Sample < Min Transfer",
    "buffer_below_min_transfer": "FAIL: Buffer < Min Transfer",
    "rounding_out_of_tolerance": "FAIL: Rounding Tolerance Exceeded",
}


def plot_pass_fail(input_csv: Path, output_png: Path) -> None:
    """Render two-panel QC summary bar chart (Overall Pass/Fail + Failure Reasons)."""
    df = pd.read_csv(input_csv)
    total = len(df)

    sns.set_theme(style="whitegrid", context="talk")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.8), dpi=300, gridspec_kw={"width_ratios": [1, 1.35]})

    # Panel A: Overall PASS vs FAIL
    status_counts = df["status"].value_counts().reindex(["PASS", "FAIL"], fill_value=0)
    palette_status = ["#2ca02c", "#d9534f"]
    bars1 = ax1.bar(
        status_counts.index,
        status_counts.values,
        color=palette_status,
        edgecolor="black",
        linewidth=1.0,
        width=0.55,
        alpha=0.88,
    )
    for bar in bars1:
        height = int(bar.get_height())
        pct = 100.0 * height / total if total else 0.0
        ax1.annotate(
            f"{height} ({pct:.1f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )
    ax1.set_title("A. Overall Library QC Status", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("QC Status", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Library Count", fontsize=11, fontweight="bold")
    ax1.set_ylim(0, max(status_counts.values) * 1.22)

    # Panel B: Breakdown by Reason
    if "reason" in df.columns:
        reason_counts = df["reason"].value_counts()
    else:
        reason_counts = status_counts

    labels = [REASON_LABELS.get(str(k), str(k)) for k in reason_counts.index]
    colors = ["#2ca02c" if k == "ok" else "#e67e22" if k == "insufficient_volume" else "#d9534f" for k in reason_counts.index]

    bars2 = ax2.barh(
        labels[::-1],
        reason_counts.values[::-1],
        color=colors[::-1],
        edgecolor="black",
        linewidth=1.0,
        height=0.55,
        alpha=0.88,
    )
    for bar in bars2:
        width = int(bar.get_width())
        pct = 100.0 * width / total if total else 0.0
        ax2.annotate(
            f" {width} ({pct:.1f}%)",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=10.5,
            fontweight="bold",
        )
    ax2.set_title("B. QC Decision Breakdown by Rule", fontsize=13, fontweight="bold", pad=12)
    ax2.set_xlabel("Library Count", fontsize=11, fontweight="bold")
    ax2.set_xlim(0, max(reason_counts.values) * 1.32)

    sns.despine(top=True, right=True)
    fig.suptitle("NGS Library Normalization Quality Control Summary", fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved QC pass/fail plot -> {output_png}")


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
        default=ROOT / "results/pass_fail.png",
    )
    args = parser.parse_args(argv)
    plot_pass_fail(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
