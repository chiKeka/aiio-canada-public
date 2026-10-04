from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from aiio.quebec_revisions import (
    DICTIONARY_ANCHORS,
    DICTIONARY_SOURCE_ID,
    QUEBEC_SOURCE_ID,
    run_quebec_authorized_revisions,
    sha256_file,
)
from aiio.schemas import ValidationError


class QuebecAuthorizedRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[2]
        cls.dashboard_path = (
            cls.project_root
            / "data/raw/quebec_pqi_project_dashboard/2026-09-01_a437f7ba9a74.csv"
        )
        cls.dictionary_path = (
            cls.project_root
            / "data/raw/quebec_pqi_data_dictionary/2026-09-01_86c6c1ab940b.pdf"
        )
        cls.dictionary_text = "\n".join(DICTIONARY_ANCHORS)

    def _write_manifest(self, path: Path, source_id: str) -> None:
        path.with_suffix(path.suffix + ".manifest.json").write_text(
            json.dumps(
                {
                    "source_id": source_id,
                    "content_hash": sha256_file(path),
                    "retrieved_at": "2026-09-01T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )

    def _run_fixture(self, rows: list[dict[str, str]]) -> tuple[dict, list[dict]]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dashboard_path = root / "dashboard.csv"
            fieldnames = [
                "no_projet",
                "nom_projet",
                "description",
                "cout_total",
                "contribution_quebec",
                "contribution_partenaires",
                "date_fin_mise_en_service",
                "etat_avancement",
                "suivi_modifications",
                "ministre",
                "organisme",
                "gestionnaire",
                "secteur_activite",
                "region",
                "nom_infrastructure",
                "localisation",
                "nature_travaux",
            ]
            with dashboard_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            self._write_manifest(dashboard_path, QUEBEC_SOURCE_ID)

            dictionary_path = root / "dictionary.pdf"
            dictionary_path.write_bytes(self.dictionary_path.read_bytes())
            self._write_manifest(dictionary_path, DICTIONARY_SOURCE_ID)
            summary_path = root / "summary.csv"
            report = run_quebec_authorized_revisions(
                dashboard_path,
                dictionary_path,
                root / "report.json",
                summary_path,
                root / "events.csv",
                dictionary_text_override=self.dictionary_text,
            )
            with summary_path.open(encoding="utf-8", newline="") as handle:
                summary_rows = list(csv.DictReader(handle))
            return report, summary_rows

    def _valid_row(self) -> dict[str, str]:
        return {
            "no_projet": "TEST-1",
            "nom_projet": "Hôpital de démonstration - Construction",
            "description": "Construction d'un établissement de santé.",
            "cout_total": "110.0",
            "contribution_quebec": "110.0",
            "contribution_partenaires": "0.0",
            "date_fin_mise_en_service": "Décembre 2027",
            "etat_avancement": "En réalisation",
            "suivi_modifications": (
                "Mars 2026\n"
                "Une hausse de 10,0 M$ au coût du projet a été autorisée. "
                "Prévu à 100,0 M$, le coût est maintenant de 110,0 M$. "
                "Une modification de la date de mise en service complète a été "
                "autorisée. Prévue en décembre 2026, elle est reportée à décembre 2027.\n"
                "Mars 2025\nLe projet a été autorisé à l'étape « En réalisation »."
            ),
            "ministre": "Ministre",
            "organisme": "Organisme",
            "gestionnaire": "Gestionnaire",
            "secteur_activite": "Santé et Services sociaux",
            "region": "06 - Montréal",
            "nom_infrastructure": "Hôpital de démonstration",
            "localisation": "Montréal",
            "nature_travaux": "Construction",
        }

    def test_parses_reconciled_cost_and_schedule_revision_chains(self) -> None:
        report, rows = self._run_fixture([self._valid_row()])
        self.assertEqual(
            report["coverage_summary"][
                "cost_revision_chain_reconciled_project_count"
            ],
            1,
        )
        self.assertEqual(
            report["coverage_summary"][
                "schedule_revision_chain_reconciled_project_count"
            ],
            1,
        )
        self.assertEqual(float(rows[0]["baseline_authorized_cost_cad"]), 100_000_000)
        self.assertEqual(float(rows[0]["authorized_cost_variance_percent"]), 0.1)
        self.assertEqual(rows[0]["authorized_schedule_change_months"], "12")
        self.assertEqual(rows[0]["cost_outcome_panel_authorized"], "False")

    def test_duplicate_stable_project_id_is_rejected(self) -> None:
        row = self._valid_row()
        with self.assertRaisesRegex(ValidationError, "duplicate no_projet"):
            self._run_fixture([row, row.copy()])

    def test_missing_dictionary_anchor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dashboard_path = root / "dashboard.csv"
            dashboard_path.write_bytes(self.dashboard_path.read_bytes())
            self._write_manifest(dashboard_path, QUEBEC_SOURCE_ID)
            dictionary_path = root / "dictionary.pdf"
            dictionary_path.write_bytes(self.dictionary_path.read_bytes())
            self._write_manifest(dictionary_path, DICTIONARY_SOURCE_ID)
            with self.assertRaisesRegex(ValidationError, "anchor is missing"):
                run_quebec_authorized_revisions(
                    dashboard_path,
                    dictionary_path,
                    root / "report.json",
                    root / "summary.csv",
                    root / "events.csv",
                    dictionary_text_override="not the official data dictionary",
                )

    def test_retrieval_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dashboard_path = root / "dashboard.csv"
            dashboard_path.write_bytes(self.dashboard_path.read_bytes())
            self._write_manifest(dashboard_path, QUEBEC_SOURCE_ID)
            dashboard_path.write_bytes(dashboard_path.read_bytes() + b"tamper")
            dictionary_path = root / "dictionary.pdf"
            dictionary_path.write_bytes(self.dictionary_path.read_bytes())
            self._write_manifest(dictionary_path, DICTIONARY_SOURCE_ID)
            with self.assertRaisesRegex(ValidationError, "hash mismatch"):
                run_quebec_authorized_revisions(
                    dashboard_path,
                    dictionary_path,
                    root / "report.json",
                    root / "summary.csv",
                    root / "events.csv",
                    dictionary_text_override=self.dictionary_text,
                )

    def test_committed_panel_is_reproducible_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = run_quebec_authorized_revisions(
                self.dashboard_path,
                self.dictionary_path,
                root / "report.json",
                root / "summary.csv",
                root / "events.csv",
                dictionary_text_override=self.dictionary_text,
            )
        committed = json.loads(
            (
                self.project_root
                / "data/model-runs/quebec_pqi_authorized_project_revisions_v0.1.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(report["coverage_summary"], committed["coverage_summary"])
        self.assertEqual(report["asset_class_coverage"], committed["asset_class_coverage"])
        self.assertEqual(
            report["descriptive_statistics"], committed["descriptive_statistics"]
        )
        self.assertEqual(report["outputs"]["summary_csv_sha256"], committed["outputs"]["summary_csv_sha256"])
        self.assertEqual(report["outputs"]["event_csv_sha256"], committed["outputs"]["event_csv_sha256"])
        self.assertFalse(
            report["publication_boundary"][
                "authorized_revision_reference_panel_authorized"
            ]
        )


if __name__ == "__main__":
    unittest.main()
