from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiio.pspe_lineage import build_pspe_method_lineage, validate_pspe_method_lineage
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/model/pspe_method_lineage_contract_v0.1.json"
COMMITTED = ROOT / "data/model-runs/pspe_method_lineage_v0.1.json"


class PspeMethodLineageTests(unittest.TestCase):
    def test_committed_lineage_is_reproducible_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            generated_path = Path(directory) / "lineage.json"
            generated = build_pspe_method_lineage(ROOT, CONTRACT, generated_path)
        committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
        self.assertEqual(generated, committed)
        self.assertEqual(
            validate_pspe_method_lineage(ROOT, CONTRACT, COMMITTED), committed
        )
        self.assertEqual(committed["mapping_count"], 5)
        self.assertEqual(
            committed["lineage_status"],
            "adaptation_from_available_method_notes",
        )
        self.assertEqual(
            committed["source_repository_availability"]["status"],
            "method_repository_located_engine_source_not_located",
        )
        self.assertEqual(
            committed["source_repository_availability"]["commit"],
            "3e63c7aaca03ec96d148f77e55aea40f2b64e40d",
        )
        self.assertEqual(
            len(committed["source_repository_availability"]["method_artifacts"]), 5
        )
        boundary = committed["publication_boundary"]
        self.assertFalse(boundary["source_code_reproduction_claim_authorized"])
        self.assertTrue(boundary["methodological_inheritance_claim_authorized"])
        self.assertTrue(boundary["implemented_layer_claim_limited_to_mappings"])
        self.assertFalse(boundary["unimplemented_pspe_layers_claimed"])
        self.assertFalse(boundary["graph_score_monetization_authorized"])

    def test_rejects_missing_aiio_mapping_artifact(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        contract["mappings"][0]["aiio_implementation"] = "missing.py"
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            output_path = Path(directory) / "output.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "missing AIIO artifact"):
                build_pspe_method_lineage(ROOT, contract_path, output_path)

    def test_rejects_promoted_source_repository_claim(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        contract["source_repository_availability"]["status"] = "engine_source_available"
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            output_path = Path(directory) / "output.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "verified local state"):
                build_pspe_method_lineage(ROOT, contract_path, output_path)


if __name__ == "__main__":
    unittest.main()
