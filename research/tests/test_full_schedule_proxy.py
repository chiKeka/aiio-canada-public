import csv
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from aiio.full_schedule_proxy import CONTRACT, CSV_OUTPUT, LEDGER_OUTPUT, OLD_PROXY, PROJECTS, REPORT_OUTPUT, build_full_schedule_proxy, full_schedule, reconstruct
from aiio.full_schedule_comparison import OUTPUT, component_series, run_full_schedule_comparison
from aiio.planning_benchmark import _check_manifest
from aiio.schemas import ValidationError

ROOT = Path(__file__).resolve().parents[2]


def rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


class FullScheduleProxyTests(unittest.TestCase):
    def test_full_schedule_conserves_every_cent_and_retains_tail(self):
        allocation = full_schedule("750000000.00", "2024", "2026")
        self.assertEqual(len(allocation), 12)
        self.assertEqual(sum(allocation.values()), Decimal("750000000.00"))
        inside = sum(v for q, v in allocation.items() if q <= "2026-Q2")
        self.assertEqual(inside, Decimal("652739251.04"))
        self.assertEqual(sum(v for q, v in allocation.items() if q > "2026-Q2"), Decimal("97260748.96"))
        tiny = full_schedule("0.03", "2024", "2026")
        self.assertEqual(sum(tiny.values()), Decimal("0.03"))
        self.assertTrue(all(v >= 0 and v * 100 == (v * 100).to_integral_value() for v in tiny.values()))

    def test_changing_window_does_not_renormalize_overlapping_quarters(self):
        contract = json.loads((ROOT / CONTRACT).read_text())
        settings = contract["reconstruction"]
        original = rows(ROOT / OLD_PROXY)
        full, ledger, _ = reconstruct(rows(ROOT / PROJECTS), original, settings)
        shorter = {**settings, "window_start": "2024-Q2", "window_end": "2025-Q4"}
        subset = [r for r in original if shorter["window_start"] <= r["quarter"] <= shorter["window_end"]]
        clipped, shorter_ledger, reconciliation = reconstruct(rows(ROOT / PROJECTS), subset, shorter)
        values = {(r["geography_id"], r["quarter"]): r["project_schedule_proxy_cad"] for r in full}
        for row in clipped:
            self.assertEqual(row["project_schedule_proxy_cad"], values[(row["geography_id"], row["quarter"])])
        self.assertEqual([(r["quarter"], r["allocation_cad"]) for r in ledger], [(r["quarter"], r["allocation_cad"]) for r in shorter_ledger])
        self.assertGreater(Decimal(reconciliation[0]["before_window_cad"]), 0)
        self.assertGreater(Decimal(reconciliation[0]["after_window_cad"]), 0)

    def test_invalid_costs_and_schedules_fail_closed(self):
        for value in ("NaN", "Infinity", "-1", "0", "0.001", "bad"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                full_schedule(value, "2024", "2026")
        with self.assertRaises(ValidationError):
            full_schedule("100", "2026", "2024")

    def test_v2_reproduces_and_preserves_permits_and_frozen_inputs(self):
        contract = json.loads((ROOT / CONTRACT).read_text())
        with tempfile.TemporaryDirectory() as folder:
            report, corrected, _ = build_full_schedule_proxy(ROOT, Path(folder))
            self.assertEqual(report, json.loads((ROOT / REPORT_OUTPUT).read_text()))
            for name in (CSV_OUTPUT, LEDGER_OUTPUT):
                self.assertEqual((Path(folder) / name).read_bytes(), (ROOT / name).read_bytes())
        old = {(r["geography_id"], r["quarter"]): r for r in rows(ROOT / OLD_PROXY)}
        for row in corrected:
            prior = old[(row["geography_id"], row["quarter"])]
            for key in ("permit_activity_proxy_cad", "explicit_data_centre_permit_count", "active_uncosted_project_count", "active_costed_project_count"):
                self.assertEqual(row[key], prior[key])
            low, central, high = [Decimal(row[f"reconstructed_proxy_{case}_cad"]) for case in ("low", "central", "high")]
            self.assertLessEqual(low, central)
            self.assertLessEqual(central, high)
        _check_manifest(ROOT, contract["input_manifest"])
        self.assertFalse(any(report["publication_boundary"].values()))

    def test_comparison_reproduces_and_matches_every_frozen_fold(self):
        report = run_full_schedule_comparison(ROOT)
        self.assertEqual(report, json.loads((ROOT / OUTPUT).read_text()))
        self.assertEqual(set(report["arms"]), {"baseline_only", "project_only", "permit_only", "combined"})
        reference = report["arms"]["baseline_only"]["predictions"]
        for arm in report["arms"].values():
            self.assertEqual(len(arm["predictions"]), 48)
            for row, before in zip(arm["predictions"], reference):
                for key in ("geography_id", "asset_class", "target_quarter", "baseline_yoy_pp", "training_end", "information_cutoff", "actual_yoy_pp"):
                    self.assertEqual(row[key], before[key])
        self.assertFalse(any(report["publication_boundary"].values()))
        self.assertEqual(len(report["sensitivity"]), 27)
        self.assertTrue(all(r["status"] == "insufficient_data" for r in report["sensitivity"] if r["information_lag_quarters"] == 4))

    def test_ablation_isolates_sources_without_changing_outcomes(self):
        original = {("CMA_825", "health_facilities"): {8096: {"y": 2.5, "low": 99, "central": 99, "high": 99}}}
        settings = {"project_realization": {c: 1 for c in ("low", "central", "high")}, "permit_realization": {c: 1 for c in ("low", "central", "high")}}
        cells = [{"geography_id": "CMA_825", "quarter": "2024-Q1", "project_schedule_proxy_cad": "100.00", "permit_activity_proxy_cad": "25.00", **{f"reconstructed_proxy_{c}_cad": "125.00" for c in ("low", "central", "high")}}]
        for arm, expected in (("baseline_only", 0), ("project_only", 100), ("permit_only", 25), ("combined", 125)):
            observation = component_series(original, cells, settings, arm)[("CMA_825", "health_facilities")][8096]
            self.assertEqual(observation["central"], expected)
            self.assertEqual(observation["y"], 2.5)
        self.assertEqual(original[("CMA_825", "health_facilities")][8096]["central"], 99)
        with self.assertRaisesRegex(ValidationError, "duplicate"):
            component_series(original, cells * 2, settings, "combined")
        with self.assertRaisesRegex(ValidationError, "missing"):
            component_series(original, [], settings, "combined")

    def test_duplicate_input_cells_and_input_overwrite_are_rejected(self):
        settings = json.loads((ROOT / CONTRACT).read_text())["reconstruction"]
        old = rows(ROOT / OLD_PROXY)
        with self.assertRaisesRegex(ValidationError, "exact locked window"):
            reconstruct(rows(ROOT / PROJECTS), old + old[:1], settings)
        with self.assertRaisesRegex(ValidationError, "overwrite"):
            run_full_schedule_comparison(ROOT, ROOT / OLD_PROXY)

    def test_source_drift_and_promotion_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / CONTRACT
            path.parent.mkdir(parents=True)
            contract = json.loads((ROOT / CONTRACT).read_text())
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValidationError, "hash drift"):
                build_full_schedule_proxy(root)
            contract["publication_boundary"]["automatic_promotion_allowed"] = True
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValidationError, "authorizing"):
                build_full_schedule_proxy(root)
