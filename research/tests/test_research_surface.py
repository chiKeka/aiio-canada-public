from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from aiio.research_surface import (
    ARTIFACTS,
    SURFACE_ID,
    build_research_surface_manifest,
    validate_research_surface_manifest,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
COMMITTED = ROOT / "public/data/research-surface.json"


class ResearchSurfaceManifestTests(unittest.TestCase):
    def test_inventory_covers_every_static_website_data_import(self) -> None:
        declared = {relative_path for _, relative_path, _ in ARTIFACTS}
        imported: set[str] = set()
        pattern = re.compile(r"from ['\"]@/(data/[^'\"]+\.json|public/data/[^'\"]+\.json)['\"]")
        for directory in ("app", "components", "lib"):
            for path in (ROOT / directory).rglob("*.ts*"):
                for match in pattern.finditer(path.read_text(encoding="utf-8")):
                    imported.add(match.group(1))
        imported.discard("public/data/research-surface.json")
        self.assertEqual(imported - declared, set())

    def test_committed_manifest_reconciles_and_remains_non_authorizing(self) -> None:
        manifest = validate_research_surface_manifest(ROOT, COMMITTED)
        self.assertEqual(manifest["surface_id"], SURFACE_ID)
        pointer = json.loads((ROOT / "public/data/latest-digest.json").read_text())
        approved_extras = 2 if pointer.get("status") == "approved" else 0
        self.assertEqual(manifest["artifact_count"], len(ARTIFACTS) + approved_extras)
        self.assertEqual(len(manifest["artifacts"]), manifest["artifact_count"])
        if approved_extras:
            paths = {item["path"] for item in manifest["artifacts"]}
            self.assertIn(f"data/digests/{pointer['edition_date']}.approval.json", paths)
            self.assertIn(f"data/digests/{pointer['edition_date']}.manifest.json", paths)
        boundary = manifest["publication_boundary"]
        self.assertFalse(boundary["is_frozen_public_release"])
        self.assertFalse(boundary["decision_grade_ready"])
        self.assertFalse(boundary["ai_attributable_effect_authorized"])
        self.assertFalse(boundary["project_cost_forecast_authorized"])
        self.assertFalse(boundary["deployment_authorized"])

    def test_validation_detects_artifact_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for _, relative_path, _ in ARTIFACTS:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                payload = {"path": relative_path}
                if relative_path == "public/data/manifest.json":
                    payload.update({"version": "test", "release_id": "TEST_RELEASE"})
                path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            manifest_path = root / "public/data/research-surface.json"
            build_research_surface_manifest(root, manifest_path)
            validate_research_surface_manifest(root, manifest_path)
            (root / ARTIFACTS[-1][1]).write_text('{"tampered": true}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "stale"):
                validate_research_surface_manifest(root, manifest_path)


if __name__ == "__main__":
    unittest.main()
