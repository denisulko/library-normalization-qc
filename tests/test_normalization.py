"""Edge-case and regression tests for mass-based normalization."""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from normalize_libraries import Config, normalize_records, normalize_row, read_samples


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.cfg = Config()

    def row(self, conc="20", available="30", sample_id="S01"):
        return {"sample_id": sample_id, "conc_ng_ul": conc, "volume_ul": available}

    def test_valid_dilution(self):
        result = normalize_row(self.row(), self.cfg)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["sample_volume_ul"], "10.00")
        self.assertEqual(result["buffer_volume_ul"], "10.00")

    def test_exact_target_needs_no_buffer(self):
        result = normalize_row(self.row("10"), self.cfg)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["buffer_volume_ul"], "0.00")

    def test_no_concentration_by_dilution(self):
        for conc in ("4.8", "5.8", "6"):
            with self.subTest(conc=conc):
                result = normalize_row(self.row(conc, "100"), self.cfg)
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["reason"], "stock_below_target")
                self.assertEqual(result["sample_volume_ul"], "")

    def test_insufficient_available_stock(self):
        result = normalize_row(self.row("20", "9"), self.cfg)
        self.assertEqual(result["reason"], "insufficient_volume")

    def test_invalid_concentrations(self):
        for conc in ("", "0", "-2", "nan", "inf", "abc"):
            with self.subTest(conc=conc):
                self.assertEqual(normalize_row(self.row(conc), self.cfg)["reason"], "invalid_concentration")

    def test_invalid_volumes(self):
        for available in ("", "-1", "nan", "inf", "oops"):
            with self.subTest(available=available):
                self.assertEqual(normalize_row(self.row("20", available), self.cfg)["reason"], "invalid_available_volume")

    def test_zero_available_volume(self):
        self.assertEqual(normalize_row(self.row("20", "0"), self.cfg)["reason"], "insufficient_volume")

    def test_min_sample_transfer(self):
        result = normalize_row(self.row("1000"), self.cfg)
        self.assertEqual(result["reason"], "sample_below_min_transfer")

    def test_min_buffer_transfer(self):
        result = normalize_row(self.row("10.2"), self.cfg)
        self.assertEqual(result["reason"], "buffer_below_min_transfer")

    def test_duplicate_identifiers(self):
        results = normalize_records([self.row(), self.row("30")], self.cfg)
        self.assertEqual([r["reason"] for r in results], ["duplicate_sample_id"] * 2)

    def test_missing_id(self):
        self.assertEqual(normalize_row(self.row(sample_id=""), self.cfg)["reason"], "missing_sample_id")

    def test_invalid_configuration(self):
        for kwargs in ({"target_ng_ul": 0}, {"final_volume_ul": -1},
                       {"min_transfer_ul": 25}, {"max_error_pct": float("nan")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Config(**kwargs)

    def test_original_dataset_regression(self):
        path = Path(__file__).resolve().parents[1] / "data/raw/sample_sheet.csv"
        results = normalize_records(read_samples(path), self.cfg)
        by_id = {r["sample_id"]: r for r in results}
        self.assertEqual(by_id["S18"]["reason"], "stock_below_target")
        self.assertEqual(by_id["S22"]["reason"], "stock_below_target")
        self.assertEqual(by_id["S14"]["reason"], "insufficient_volume")
        self.assertEqual(len(results), 24)
        self.assertTrue(all(r["status"] == "FAIL" or (
            float(r["sample_volume_ul"]) >= 0 and
            float(r["buffer_volume_ul"]) >= 0
        ) for r in results))


if __name__ == "__main__":
    unittest.main()
