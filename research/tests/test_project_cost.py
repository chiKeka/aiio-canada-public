from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiio.project_cost import build_project_reference_cost, run_project_reference_cost
from aiio.schemas import ValidationError


def baseline(*, authorized: bool = True, failed_second_year: bool = False) -> dict:
    return {
        "model_id": "BASELINE_TEST",
        "as_of_date": "2026-06-30",
        "publication_authorization": {
            "public_projection_authorized": authorized
        },
        "reference_class_results": [
            {
                "asset_class": "health_facilities",
                "geography_id": "CMA_825",
                "reference_indicator_id": "BCPI_TEST",
                "mapping_status": "proxy",
                "mapping_note": "Test reference proxy.",
                "latest_period_end": "2026-06-30",
                "latest_index": 100.0,
                "horizons": [
                    {
                        "horizon_years": 1,
                        "status": "gate_passed",
                        "reason": None,
                        "projected_index": 105.0,
                    },
                    {
                        "horizon_years": 2,
                        "status": (
                            "gate_failed" if failed_second_year else "gate_passed"
                        ),
                        "reason": (
                            "validation gate failed" if failed_second_year else None
                        ),
                        "projected_index": None if failed_second_year else 110.0,
                    },
                ],
            }
        ],
    }


def project() -> dict:
    return {
        "project_id": "TEST_HOSPITAL",
        "project_name": "Test hospital",
        "asset_class": "health_facilities",
        "geography_id": "CMA_825",
        "current_estimate_cad": 100_000_000,
        "estimate_price_basis_period_end": "2026-06-30",
        "expenditure_profile": [
            {"horizon_years": 1, "share": 0.4},
            {"horizon_years": 2, "share": 0.6},
        ],
    }


class ProjectReferenceCostTests(unittest.TestCase):
    def test_schedule_weights_reference_indices_instead_of_end_loading_budget(self) -> None:
        result = build_project_reference_cost(project(), baseline())
        market = result["market_reference_baseline"]
        self.assertEqual(result["status"], "baseline_only")
        self.assertEqual(market["schedule_weighted_factor"], 1.08)
        self.assertEqual(market["schedule_weighted_change_percent"], 8.0)
        self.assertEqual(market["schedule_weighted_estimate_cad"], 108_000_000)
        self.assertEqual(market["schedule_weighted_escalation_cad"], 8_000_000)
        self.assertIsNone(
            result["ai_attributable_increment"]["cost_escalation_percent"]
        )

    def test_origin_year_share_uses_current_index_factor(self) -> None:
        definition = project()
        definition["expenditure_profile"] = [
            {"horizon_years": 0, "share": 0.25},
            {"horizon_years": 1, "share": 0.75},
        ]
        result = build_project_reference_cost(definition, baseline())
        self.assertEqual(
            result["market_reference_baseline"]["schedule_weighted_factor"],
            1.0375,
        )

    def test_any_failed_expenditure_horizon_withholds_entire_project_result(self) -> None:
        result = build_project_reference_cost(
            project(), baseline(failed_second_year=True)
        )
        self.assertEqual(result["status"], "not_assessed")
        self.assertEqual(result["failed_horizons"][0]["horizon_years"], 2)
        self.assertIsNone(
            result["market_reference_baseline"]["schedule_weighted_estimate_cad"]
        )

    def test_independent_review_gate_withholds_otherwise_valid_result(self) -> None:
        result = build_project_reference_cost(project(), baseline(authorized=False))
        self.assertEqual(result["status"], "withheld")
        self.assertIsNone(
            result["market_reference_baseline"]["schedule_weighted_change_percent"]
        )

    def test_price_basis_must_match_forecast_origin(self) -> None:
        definition = project()
        definition["estimate_price_basis_period_end"] = "2025-12-31"
        result = build_project_reference_cost(definition, baseline())
        self.assertEqual(result["status"], "not_assessed")
        self.assertIn("price basis", result["reason"])

    def test_profile_shares_must_sum_to_one(self) -> None:
        definition = project()
        definition["expenditure_profile"][1]["share"] = 0.5
        with self.assertRaisesRegex(ValidationError, "sum to exactly 1"):
            build_project_reference_cost(definition, baseline())

    def test_unknown_reference_class_is_not_assessed(self) -> None:
        definition = project()
        definition["geography_id"] = "PR_48"
        result = build_project_reference_cost(definition, baseline())
        self.assertEqual(result["status"], "not_assessed")
        self.assertIn("no eligible", result["reason"])

    def test_runner_hashes_both_inputs_and_writes_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project_path = root / "project.json"
            baseline_path = root / "baseline.json"
            output_path = root / "output.json"
            project_path.write_text(json.dumps(project()) + "\n", encoding="utf-8")
            baseline_path.write_text(json.dumps(baseline()) + "\n", encoding="utf-8")
            result = run_project_reference_cost(
                project_path, baseline_path, output_path
            )
            written = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(result, written)
        self.assertEqual(len(result["inputs"]["project_definition_sha256"]), 64)
        self.assertEqual(len(result["inputs"]["cost_baseline_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
