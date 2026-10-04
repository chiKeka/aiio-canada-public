import copy
import json
import tempfile
import unittest
from pathlib import Path

from aiio.planning_benchmark import CONTRACT, OUTPUT, evaluate, quarter, ridge_predict, run_planning_benchmark
from aiio.schemas import ValidationError

ROOT = Path(__file__).resolve().parents[2]


class PlanningBenchmarkTests(unittest.TestCase):
    def test_committed_benchmark_reproduces_and_never_authorizes(self):
        report = run_planning_benchmark(ROOT)
        self.assertEqual(report, json.loads((ROOT / OUTPUT).read_text()))
        self.assertEqual(report["coverage"]["held_out_quarters"], 8)
        self.assertEqual(report["coverage"]["market_quarter_cells"], 16)
        self.assertEqual(report["coverage"]["asset_rows"], 48)
        self.assertIsNone(report["coverage"]["independently_linked_events"])
        self.assertFalse(any(report["publication_boundary"].values()))
        self.assertEqual(report["predictive_intervals"]["status"], "withheld")
        for row in report["predictions"]:
            self.assertLessEqual(quarter(row["training_end"]), quarter(row["information_cutoff"]))
            self.assertLess(quarter(row["information_cutoff"]), quarter(row["target_quarter"]))

    def test_future_outcomes_and_exposure_cannot_change_earlier_forecast(self):
        first = quarter("2017-Q1")
        rows = {first + i: {"y": 1 + i * 0.1, "central": float(i * i)} for i in range(38)}
        series = {("CMA_825", "health_facilities"): rows}
        design = {"first_test_quarter": "2024-Q2", "last_test_quarter": "2024-Q2", "minimum_training_quarters": 20, "ridge_penalty": 1}
        before = evaluate(series, design, "central", 2)[0]
        changed = copy.deepcopy(series)
        for q, row in changed[("CMA_825", "health_facilities")].items():
            if q > quarter(before["information_cutoff"]):
                row.update(y=999999, central=1e15)
        after = evaluate(changed, design, "central", 2)[0]
        self.assertEqual(before["baseline_yoy_pp"], after["baseline_yoy_pp"])
        self.assertEqual(before["proxy_yoy_pp"], after["proxy_yoy_pp"])
        self.assertNotEqual(before["actual_yoy_pp"], after["actual_yoy_pp"])

    def test_constant_proxy_adds_no_spurious_prediction(self):
        x = [[float(i)] for i in range(25)]
        y = [2 + i * 0.3 for i in range(25)]
        baseline = ridge_predict(x, y, [26], 1)
        augmented = ridge_predict([row + [0] for row in x], y, [26, 1000], 1)
        self.assertAlmostEqual(baseline, augmented)

    def test_hash_drift_and_promotion_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / CONTRACT
            path.parent.mkdir(parents=True)
            contract = json.loads((ROOT / CONTRACT).read_text())
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValidationError, "hash drift"):
                run_planning_benchmark(root)
            contract["publication_boundary"]["validated_proxy_estimate_allowed"] = True
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValidationError, "cannot authorize"):
                run_planning_benchmark(root)

    def test_insufficient_training_is_not_silently_skipped(self):
        series = {("CMA_825", "health_facilities"): {quarter("2024-Q1"): {"y": 1, "central": 0}}}
        design = {"first_test_quarter": "2024-Q2", "last_test_quarter": "2024-Q2", "minimum_training_quarters": 20, "ridge_penalty": 1}
        with self.assertRaisesRegex(ValidationError, "insufficient training"):
            evaluate(series, design, "central", 2)
