from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from aiio.schemas import ValidationError
from aiio.treatment_source_feasibility import (
    REQUIRED_GATES,
    build_treatment_source_feasibility,
    validate_treatment_source_contract,
)


class TreatmentSourceFeasibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        cls.contract_path = (
            cls.root
            / "data/model/ai_attribution_treatment_source_feasibility_contract_v0.1.json"
        )
        cls.registry_path = cls.root / "data/registry/sources.json"
        cls.contract = json.loads(cls.contract_path.read_text(encoding="utf-8"))
        registry = json.loads(cls.registry_path.read_text(encoding="utf-8"))
        cls.registry_ids = {item["source_id"] for item in registry["sources"]}

    def test_committed_report_is_reproducible_and_fail_closed(self) -> None:
        rebuilt = build_treatment_source_feasibility(
            self.contract_path, self.registry_path
        )
        committed = json.loads(
            (
                self.root
                / "data/model-runs/ai_attribution_treatment_source_feasibility_v0.1.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(rebuilt, committed)
        self.assertEqual(rebuilt["candidate_count"], 8)
        self.assertEqual(rebuilt["authorizing_candidate_count"], 0)
        self.assertEqual(rebuilt["required_authorizing_gates"], list(REQUIRED_GATES))
        self.assertEqual(
            rebuilt["input_manifest"]["contract_path"],
            "data/model/ai_attribution_treatment_source_feasibility_contract_v0.1.json",
        )
        self.assertEqual(
            rebuilt["input_manifest"]["registry_path"],
            "data/registry/sources.json",
        )
        self.assertFalse(rebuilt["publication_boundary"]["treatment_authorized"])
        self.assertIsNone(
            rebuilt["publication_boundary"]["ai_attributable_cost_effect"]
        )

    def test_rejects_unknown_source_and_incomplete_gate_coverage(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["candidates"][0]["source_id"] = "UNKNOWN"
        with self.assertRaisesRegex(ValidationError, "unknown source"):
            validate_treatment_source_contract(contract, registry_ids=self.registry_ids)

        contract = copy.deepcopy(self.contract)
        contract["candidates"][0]["gate_assessment"].pop(REQUIRED_GATES[0])
        with self.assertRaisesRegex(ValidationError, "gate coverage"):
            validate_treatment_source_contract(contract, registry_ids=self.registry_ids)

    def test_rejects_proxy_promoted_to_authorizing_treatment(self) -> None:
        for candidate_id in (
            "ALBERTA_MAJOR_PROJECTS_INVENTORY",
            "EDMONTON_BUILDING_PERMIT_PROXY",
            "STATCAN_INFORMATION_SECTOR_CAPEX",
            "STATCAN_BUILDING_PERMITS",
            "STATCAN_SCIEU_2024_RELEASE",
            "STATCAN_CMA_INDUSTRY_EMPLOYMENT",
        ):
            contract = copy.deepcopy(self.contract)
            candidate = next(
                item for item in contract["candidates"] if item["candidate_id"] == candidate_id
            )
            candidate["authorizing_status"] = "authorizing_candidate"
            with self.assertRaisesRegex(ValidationError, "contradicts its gates"):
                validate_treatment_source_contract(
                    contract, registry_ids=self.registry_ids
                )

    def test_requires_null_effects_when_no_source_is_authorizing(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["publication_boundary"]["ai_attributable_cost_effect"] = 2.5
        with self.assertRaisesRegex(ValidationError, "AI-attributable effect"):
            validate_treatment_source_contract(contract, registry_ids=self.registry_ids)

        contract = copy.deepcopy(self.contract)
        contract["publication_boundary"]["authorizing_treatment_measure"] = "proxy"
        with self.assertRaisesRegex(ValidationError, "treatment measure"):
            validate_treatment_source_contract(contract, registry_ids=self.registry_ids)


if __name__ == "__main__":
    unittest.main()
