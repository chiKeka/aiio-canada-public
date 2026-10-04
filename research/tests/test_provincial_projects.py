from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.adapters.provincial_projects import (
    BC_SOURCE_ID,
    ONTARIO_SOURCE_ID,
    QUEBEC_SOURCE_ID,
    classify_asset_class,
    normalize_bc_projects,
    normalize_provincial_projects,
)
from aiio.schemas import ValidationError


class ProvincialProjectAdapterTests(unittest.TestCase):
    def test_cross_source_asset_taxonomy_preserves_public_asset_classes(self) -> None:
        self.assertEqual(
            classify_asset_class(
                ONTARIO_SOURCE_ID,
                "Health care",
                "",
                "",
                "Regional hospital",
                "New patient tower",
            ),
            "health_facilities",
        )
        self.assertEqual(
            classify_asset_class(
                QUEBEC_SOURCE_ID,
                "Réseau routier",
                "Reconstruction",
                "",
                "Échangeur",
                "",
            ),
            "roads_transit_and_airports",
        )
        self.assertEqual(
            classify_asset_class(
                BC_SOURCE_ID,
                "Utilities (incl sewage treatment)",
                "Water, Sewage, and Other Systems",
                "Utilities",
                "Wastewater plant",
                "",
            ),
            "municipal_water_and_resilience",
        )
        self.assertEqual(
            classify_asset_class(
                BC_SOURCE_ID,
                "Utilities (incl sewage treatment)",
                "Utilities",
                "Utilities",
                "Grid reinforcement",
                "",
                clean_energy=True,
            ),
            "power_sector_infrastructure",
        )

    def test_combined_adapter_converts_units_and_withholds_zero_costs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bc_path = root / "bc.geojson"
            ontario_path = root / "ontario.csv"
            quebec_path = root / "quebec.csv"
            output_csv = root / "projects.csv"
            output_report = root / "report.json"
            bc_path.write_text(json.dumps(_bc_payload()), encoding="utf-8")
            _write_csv(ontario_path, [_ontario_row(), _ontario_row()])
            _write_csv(quebec_path, [_quebec_row()])

            report = normalize_provincial_projects(
                bc_path,
                ontario_path,
                quebec_path,
                output_csv,
                output_report,
                source_as_of_dates={
                    BC_SOURCE_ID: "2024-12-01",
                    ONTARIO_SOURCE_ID: "2026-06-12",
                    QUEBEC_SOURCE_ID: "2026-08-20",
                },
            )
            with output_csv.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(report["record_count"], 3)
        self.assertFalse(report["publication_boundary"]["public_project_exposure_authorized"])
        ontario_diagnostic = next(
            item
            for item in report["source_diagnostics"]
            if item["source_id"] == ONTARIO_SOURCE_ID
        )
        self.assertEqual(ontario_diagnostic["collapsed_exact_duplicate_row_count"], 1)
        by_source = {row["source_id"]: row for row in rows}
        self.assertEqual(float(by_source[BC_SOURCE_ID]["estimated_cost_cad"]), 40_000_000)
        self.assertEqual(by_source[BC_SOURCE_ID]["start_year"], "2027")
        self.assertEqual(by_source[BC_SOURCE_ID]["end_year"], "2028")
        self.assertEqual(by_source[ONTARIO_SOURCE_ID]["estimated_cost_cad"], "")
        self.assertEqual(
            by_source[ONTARIO_SOURCE_ID]["cost_status"],
            "zero_placeholder_treated_as_missing",
        )
        self.assertEqual(by_source[ONTARIO_SOURCE_ID]["end_year"], "2028")
        self.assertIn("source_is_sample_not_complete_inventory", by_source[ONTARIO_SOURCE_ID]["quality_flags"])
        self.assertEqual(float(by_source[QUEBEC_SOURCE_ID]["estimated_cost_cad"]), 24_300_000)
        self.assertEqual(by_source[QUEBEC_SOURCE_ID]["end_year"], "2027")

    def test_schema_drift_fails_closed(self) -> None:
        payload = _bc_payload()
        del payload["features"][0]["properties"]["ESTIMATED_COST"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bc.geojson"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "schema changed"):
                normalize_bc_projects(path, "2024-12-01")


class ProvincialProjectArtifactTests(unittest.TestCase):
    def test_committed_artifacts_are_reproducible_and_fail_closed(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        committed_csv = project_root / "data" / "processed" / "public_projects_bc_on_qc.csv"
        committed_report = (
            project_root
            / "data"
            / "model-runs"
            / "public_projects_bc_on_qc_intake_v0.1.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regenerated_csv = root / "projects.csv"
            regenerated_report = root / "report.json"
            report = normalize_provincial_projects(
                project_root
                / "data"
                / "raw"
                / "bc_major_projects_inventory"
                / "2026-09-01_8ff579493b29.geojson",
                project_root
                / "data"
                / "raw"
                / "ontario_builds_projects"
                / "2026-09-01_acd5e57a1989.csv",
                project_root
                / "data"
                / "raw"
                / "quebec_pqi_project_dashboard"
                / "2026-09-01_a437f7ba9a74.csv",
                regenerated_csv,
                regenerated_report,
                source_as_of_dates={
                    BC_SOURCE_ID: "2024-12-01",
                    ONTARIO_SOURCE_ID: "2026-06-12",
                    QUEBEC_SOURCE_ID: "2026-08-20",
                },
            )
            regenerated_csv_hash = _hash_file(regenerated_csv)
            regenerated_report_hash = _hash_file(regenerated_report)

        self.assertEqual(regenerated_csv_hash, _hash_file(committed_csv))
        self.assertEqual(regenerated_report_hash, _hash_file(committed_report))
        self.assertEqual(report["record_count"], 7231)
        self.assertEqual(report["source_count"], 3)
        self.assertFalse(
            report["publication_boundary"]["public_project_exposure_authorized"]
        )


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bc_payload() -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "PROJECT_ID": 4808,
                    "PROJECT_NAME": "Regional hospital expansion",
                    "PROJECT_DESCRIPTION": "New acute-care tower",
                    "ESTIMATED_COST": 40,
                    "PROJECT_CATEGORY_NAME": "Public Services",
                    "PROJECT_TYPE": "Health Care and Social Assistance",
                    "CONSTRUCTION_SUBTYPE": "Health",
                    "REGION": "1. Vancouver Island/Coast",
                    "MUNICIPALITY": "Duncan",
                    "DEVELOPER": "BC Health Authority",
                    "PROJECT_STATUS": "Proposed",
                    "PROJECT_STAGE": "Permitting",
                    "PUBLIC_FUNDING_IND": "TRUE",
                    "CLEAN_ENERGY_IND": "FALSE",
                    "STANDARDIZED_START_DATE": "2027-Q1",
                    "STANDARDIZED_COMPLETION_DATE": "2028-Q4",
                    "LATITUDE": 48.773167,
                    "LONGITUDE": -123.703657,
                    "PROJECT_WEBSITE": "https://example.gov.bc.ca/project",
                },
                "geometry": None,
            }
        ],
    }


def _ontario_row() -> dict[str, str]:
    return {
        "Category": "Education",
        "Supporting Ministry": "Education",
        "Community": "Thunder Bay",
        "Project": "New public school",
        "Status": "Under construction",
        "Target Completion Date": "28-Nov",
        "Description": "Construction of a new school",
        "Result": "Additional pupil places",
        "Area": "Thunder Bay",
        "Region": "Northwest",
        "Address": "1 School Road",
        "Highway / Transit Line": "",
        "Estimated Total Budget ($)": "0",
        "Municipal Funding": "",
        "Provincial Funding": "Yes",
        "Federal Funding": "",
        "Other Funding": "",
        "Website": "https://example.ontario.ca/project",
        "Latitude": "48.42",
        "Longitude": "-89.26",
    }


def _quebec_row() -> dict[str, str]:
    return {
        "no_projet": "98",
        "nom_projet": "École secondaire – Reconstruction",
        "description": "Reconstruction d'une école secondaire.",
        "cout_total": "24.30",
        "contribution_quebec": "20.00",
        "contribution_partenaires": "4.30",
        "date_fin_mise_en_service": "Décembre 2027",
        "etat_avancement": "En réalisation",
        "suivi_modifications": "",
        "ministre": "Ministre de l'Éducation",
        "organisme": "Centre de services scolaire",
        "gestionnaire": "Société québécoise des infrastructures",
        "secteur_activite": "Éducation",
        "region": "06 – Montréal",
        "nom_infrastructure": "École secondaire",
        "localisation": "Montréal",
        "nature_travaux": "Reconstruction",
    }


if __name__ == "__main__":
    unittest.main()
