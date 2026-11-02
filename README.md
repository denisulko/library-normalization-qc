# NGS Library Normalization QC

A **Python-based, reproducible QC and transfer-volume planner** for sequencing libraries. Built around a real laboratory challenge: flagging libraries that cannot be normalized to a target **mass concentration** before anyone creates a pipetting plan.

> **Scope:** This project models mass concentration (ng/µL), not molarity (nM). For equimolar sequencing library pooling, fragment length and appropriate molecular-weight assumptions must also be considered. This is a portfolio/demo tool, **not validated for clinical or production laboratory use**. Always review results and instrument-specific requirements before pipetting.

## What it does

- Reads a CSV with `sample_id`, `conc_ng_ul` (ng/µL), and `volume_ul` (µL).
- Calculates dilution volumes using `C1 × V1 = C2 × V2`.
- Rejects samples below target concentration, insufficient stock, invalid values, duplicate IDs, and sub-minimum transfers.
- Rounds proposed sample/buffer transfers to 0.01 µL, then checks the estimated resulting concentration against a configurable tolerance.
- Writes a plan CSV (only **PASS** rows contain actionable transfer volumes) and a JSON QC summary.
- Includes Python standard-library unit tests and GitHub Actions CI.

## Quick start

Requires **Python 3.10+**. No third-party dependencies are required for the core CLI.

From the repository root:

```bash
python scripts/normalize_libraries.py
```

Default input: `data/raw/sample_sheet.csv`. Default outputs:
- `results/normalized_samples.csv`
- `results/qc_summary.json`

Run with custom parameters:

```bash
python scripts/normalize_libraries.py \
  --input data/raw/sample_sheet.csv \
  --output results/normalized_samples.csv \
  --summary results/qc_summary.json \
  --target-ng-ul 10 \
  --final-volume-ul 20 \
  --min-transfer-ul 1 \
  --max-error-pct 0.5
```

For automation, add `--strict` to exit with code 1 if any sample fails QC. A malformed file or invalid configuration exits with code 2.

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Input format

```csv
sample_id,conc_ng_ul,volume_ul
S01,27.6,11.7
S02,24.3,35.9
S03,18.4,24.9
```

All concentrations are in **ng/µL**; all volumes are in **µL**. Input examples are synthetic, not patient data.

## QC decision rules

1. Missing sample ID, duplicate ID, invalid/nonfinite concentration, and invalid/nonfinite stock volume cause FAIL.
2. Stock concentration below target causes `stock_below_target`; dilution cannot increase concentration.
3. Available stock must cover the calculated (rounded) sample transfer.
4. Nonzero sample and buffer transfers must meet `min_transfer_ul`. Zero buffer is valid when stock concentration equals target.
5. Rounded volumes must produce a concentration within `max_error_pct` of the target.

On failure, `sample_volume_ul` and `buffer_volume_ul` are **blank**; `required_sample_volume_ul` may still be reported for diagnosis. Reasons appear in the CSV's `reason` column.

**Example regression:** the old code incorrectly marked S18 and S22 as PASS despite negative buffer volumes. The updated logic flags both as `stock_below_target`.

## Files

- `scripts/normalize_libraries.py` — core CLI and calculations
- `tests/test_normalization.py` — unit and regression tests
- `.github/workflows/tests.yml` — automated tests
- `data/raw/sample_sheet.csv` — synthetic input data
- `results/` — example historical output and generated reports
- `notebooks/` and older plotting scripts — exploratory legacy analysis

> Existing files in `results/` are historical outputs from the earlier implementation. **Rerun the new CLI before interpreting the CSV.** Legacy plotting scripts are provided for exploration; they have not yet been refactored.

## Planned extensions

Molar normalization with explicit fragment length, configurable liquid-handler constraints, plate mapping, provenance/audit logs, and machine-readable instrument transfer files **after wet-lab validation**.

## Author

Denis Ulko — molecular biologist with practical NGS, Illumina sequencing, and laboratory automation experience.
