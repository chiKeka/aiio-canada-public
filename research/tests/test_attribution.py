from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from aiio.attribution import build_attribution_readiness, validate_contract
from aiio.schemas import ValidationError


class AttributionReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[2]
        cls.contract = json.loads(
            (cls.project_root / "data/model/ai_attribution_panel_contract_v0.1.json").read_text(
                encoding="utf-8"
            )
        )
        registry = json.loads(
            (cls.project_root / "data/registry/sources.json").read_text(encoding="utf-8")
        )
        cls.registry_ids = {item["source_id"] for item in registry["sources"]}

    def test_locked_contract_validates_and_run_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "readiness.json"
            output = build_attribution_readiness(
                self.project_root / "data/model/ai_attribution_panel_contract_v0.1.json",
                self.project_root / "data/registry/sources.json",
                output_path,
            )
        self.assertEqual(output["analysis_status"], "not_assessed")
        authorization = output["publication_authorization"]
        self.assertFalse(authorization["ai_attributable_increment_authorized"])
        self.assertIsNone(authorization["cost_escalation_percent"])
        self.assertIsNone(authorization["cost_escalation_cad"])
        self.assertIsNone(authorization["schedule_delay_days"])
        self.assertIn(
            "S3/PSPE maps mechanisms",
            output["graph_role"],
        )

    def test_committed_readiness_artifact_is_reproducible(self) -> None:
        committed = json.loads(
            (
                self.project_root
                / "data/model-runs/ai_attribution_identification_readiness_v0.1.json"
            ).read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            rebuilt = build_attribution_readiness(
                self.project_root / "data/model/ai_attribution_panel_contract_v0.1.json",
                self.project_root / "data/registry/sources.json",
                Path(temporary_directory) / "readiness.json",
            )
        self.assertEqual(rebuilt, committed)

    def test_rejects_announcements_as_authorizing_treatment(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["treatment"]["authorizing_measures"].append("announced_capex_cad")
        with self.assertRaisesRegex(ValidationError, "cannot authorize treatment"):
            validate_contract(contract, registry_ids=self.registry_ids)

    def test_rejects_unknown_source_lineage(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["data_domains"][0]["source_ids"].append("UNKNOWN_SOURCE")
        with self.assertRaisesRegex(ValidationError, "unknown sources"):
            validate_contract(contract, registry_ids=self.registry_ids)

    def test_rejects_premature_non_null_effect(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["publication_authorization"]["cost_escalation_percent"] = 4.2
        with self.assertRaisesRegex(ValidationError, "must remain null"):
            validate_contract(contract, registry_ids=self.registry_ids)

    def test_rejects_conventional_twfe_as_primary_staggered_estimator(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["design"]["two_way_fixed_effects_event_study_primary"] = True
        with self.assertRaisesRegex(ValidationError, "cannot be the primary"):
            validate_contract(contract, registry_ids=self.registry_ids)


if __name__ == "__main__":
    unittest.main()
