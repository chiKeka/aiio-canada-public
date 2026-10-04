from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiio.scenario_suite import run_scenario_suite
from aiio.schemas import ValidationError


class AlbertaScenarioSuiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.contract_path = (
            self.root / "data" / "model" / "alberta_50b_scenario_suite_contract_v0.1.json"
        )
        self.golden_path = (
            self.root / "data" / "model-runs" / "alberta_50b_scenario_suite_v0.1.json"
        )

    def test_committed_suite_is_reproducible_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            actual_path = temp / "suite.json"
            actual = run_scenario_suite(
                self.root,
                self.contract_path,
                actual_path,
                variant_output_dir=temp / "runs",
            )
            expected = json.loads(self.golden_path.read_text(encoding="utf-8"))
            self.assertEqual(actual, expected)
            self.assertEqual(actual_path.read_bytes(), self.golden_path.read_bytes())
        self.assertEqual(actual["variant_count"], 4)
        self.assertEqual(actual["evidence_status"], "scenario")
        self.assertFalse(actual["publication_boundary"]["forecast_authorized"])
        self.assertFalse(
            actual["publication_boundary"]["project_cost_or_delay_translation_authorized"]
        )

    def test_variants_isolate_timing_and_capture(self) -> None:
        report = json.loads(self.golden_path.read_text(encoding="utf-8"))
        variants = {item["variant_id"]: item for item in report["variant_summaries"]}
        self.assertEqual({item["investment_total_cad"] for item in variants.values()}, {50_000_000_000})
        self.assertEqual(variants["front_loaded"]["first_five_year_capex_share"], 0.67)
        self.assertEqual(variants["constrained_delivery"]["delivery_year_count"], 15)
        self.assertEqual(variants["high_local_capture"]["local_capture_share"], 0.9)
        self.assertEqual(
            variants["staggered"]["local_modelled_capex_cad"],
            variants["front_loaded"]["local_modelled_capex_cad"],
        )
        self.assertGreater(
            variants["high_local_capture"]["local_modelled_capex_cad"],
            variants["staggered"]["local_modelled_capex_cad"],
        )

    def test_variant_pressure_directions_are_coherent(self) -> None:
        report = json.loads(self.golden_path.read_text(encoding="utf-8"))
        variants = {item["variant_id"]: item for item in report["variant_summaries"]}
        trade_score = lambda item: item["top_trade"]["raw_central_pressure_score"]
        self.assertGreater(trade_score(variants["front_loaded"]), trade_score(variants["staggered"]))
        self.assertLess(
            trade_score(variants["constrained_delivery"]), trade_score(variants["staggered"])
        )
        self.assertGreater(
            trade_score(variants["high_local_capture"]), trade_score(variants["staggered"])
        )
        self.assertLess(
            variants["front_loaded"]["top_trade"]["central_peak_year"],
            variants["staggered"]["top_trade"]["central_peak_year"],
        )
        self.assertGreater(
            variants["constrained_delivery"]["top_trade"]["central_peak_year"],
            variants["staggered"]["top_trade"]["central_peak_year"],
        )

    def test_rejects_invariant_drift(self) -> None:
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        contract["invariants"]["investment_total_cad"] = 40_000_000_000
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            tampered_path = temp / "contract.json"
            tampered_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "locked investment total"):
                run_scenario_suite(
                    self.root,
                    tampered_path,
                    temp / "suite.json",
                    variant_output_dir=temp / "runs",
                )

    def test_rejects_premature_authorization_and_path_escape(self) -> None:
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            contract["publication_boundary"]["forecast_authorized"] = True
            authorization_path = temp / "authorized.json"
            authorization_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "fail closed"):
                run_scenario_suite(self.root, authorization_path, temp / "suite.json")

            contract["publication_boundary"]["forecast_authorized"] = False
            contract["graph_path"] = "../outside.json"
            escape_path = temp / "escape.json"
            escape_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "repository-relative"):
                run_scenario_suite(self.root, escape_path, temp / "suite.json")


if __name__ == "__main__":
    unittest.main()
