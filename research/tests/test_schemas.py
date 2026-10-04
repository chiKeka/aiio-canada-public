from __future__ import annotations

import tempfile
import unittest
import zipfile
import json
from datetime import date
from pathlib import Path

from aiio.adapters.statcan import (
    BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID,
    BCPI_REFERENCE_PROVINCE_DGUID_TO_GEOGRAPHY_ID,
    PROVINCE_DGUID_TO_GEOGRAPHY_ID,
    TRADE_NOC_TO_NODE,
    normalize_bcpi_provinces,
    normalize_bcpi_reference_provinces,
    normalize_jvws_alberta,
    normalize_jvws_canada,
    quarter_bounds,
    slug,
)
from aiio.adapters.statcan_census import (
    CENSUS_WORKFORCE_PRODUCT_ID,
    census_workforce_requests,
    normalize_census_trade_employment,
)
from aiio.adapters.alberta_projects import (
    classify_ai_relevance,
    extract_coordinates,
    extract_verification_token,
    schedule_years,
)
from aiio.constants import EvidenceStatus
from aiio.digest import build_digest
from aiio.schemas import ObservationRecord, ScenarioRecord, ValidationError


class SchemaTests(unittest.TestCase):
    def test_observation_rejects_scenario_contamination(self) -> None:
        observation = ObservationRecord(
            observation_id="OBS_1",
            indicator_id="TEST",
            value=1,
            unit="index",
            geography_id="PR_48",
            period_start="2026-01-01",
            period_end="2026-03-31",
            source_id="SOURCE_1",
            evidence_status=EvidenceStatus.SCENARIO,
            as_of_date="2026-03-31",
        )
        with self.assertRaisesRegex(ValidationError, "scenario values"):
            observation.validate()

    def test_missing_observation_requires_quality_flag(self) -> None:
        observation = ObservationRecord(
            observation_id="OBS_MISSING",
            indicator_id="TEST",
            value=None,
            unit="Number",
            geography_id="PR_48",
            period_start="2026-01-01",
            period_end="2026-03-31",
            source_id="SOURCE_1",
            evidence_status=EvidenceStatus.OBSERVED,
            as_of_date="2026-03-31",
        )
        with self.assertRaisesRegex(ValidationError, "quality flag"):
            observation.validate()

    def test_scenario_requires_scenario_status(self) -> None:
        scenario = ScenarioRecord(
            scenario_id="AB_50B",
            geography_id="PR_48",
            investment_total_cad=50_000_000_000,
            currency_year=2026,
            start_year=2027,
            end_year=2036,
            construction_share=0.38,
            local_capture_share=0.72,
            evidence_status=EvidenceStatus.ASSUMED,
        )
        with self.assertRaisesRegex(ValidationError, "scenario overlays"):
            scenario.validate()

    def test_scenario_share_boundaries(self) -> None:
        scenario = ScenarioRecord(
            scenario_id="AB_50B",
            geography_id="PR_48",
            investment_total_cad=50_000_000_000,
            currency_year=2026,
            start_year=2027,
            end_year=2036,
            construction_share=1.2,
            local_capture_share=0.72,
        )
        with self.assertRaisesRegex(ValidationError, "construction_share"):
            scenario.validate()

    def test_statcan_quarter_conversion(self) -> None:
        self.assertEqual(quarter_bounds("2026-Q2"), ("2026-04-01", "2026-06-30"))
        self.assertEqual(quarter_bounds("2026-04"), ("2026-04-01", "2026-06-30"))
        self.assertEqual(slug("Non-residential building"), "NON_RESIDENTIAL_BUILDING")

    def test_bcpi_provincial_normalizer_keeps_published_provinces_separate(self) -> None:
        header = (
            '"REF_DATE","GEO","DGUID","Type of building","Division",'
            '"UOM","VALUE","STATUS","SYMBOL"\n'
        )
        rows = []
        for dguid in BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID:
            rows.append(
                f'"2026-Q2","Province {dguid}","{dguid}","Factory",'
                '"Concrete","Index, 2023=100","110.0","",""'
            )
        rows.extend(
            [
                '"2026-Q2","Canada","2021A000011124","Factory","Concrete","Index, 2023=100","111.0","",""',
                '"2026-Q2","Calgary, Alberta","2021S0503825","Factory","Concrete","Index, 2023=100","112.0","",""',
                '"2026-Q2","Alberta","2021A000248","Office building","Concrete","Index, 2023=100","113.0","",""',
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "bcpi.zip"
            output_path = root / "bcpi_provinces.csv"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("18100289.csv", header + "\n".join(rows) + "\n")
            observations = normalize_bcpi_provinces(archive_path, output_path)
            output = output_path.read_text(encoding="utf-8")
        self.assertEqual(len(observations), 9)
        self.assertEqual(
            {item.geography_id for item in observations},
            set(BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID.values()),
        )
        self.assertNotIn("Canada,2021A000011124", output)
        self.assertNotIn("Calgary, Alberta", output)
        self.assertNotIn("Office building", output)
        self.assertIn("TR_STATCAN_BCPI_CA_PROVINCES_MATERIALS_1_0_0", output)

    def test_bcpi_provincial_normalizer_fails_when_source_coverage_changes(self) -> None:
        header = (
            '"REF_DATE","GEO","DGUID","Type of building","Division",'
            '"UOM","VALUE","STATUS","SYMBOL"\n'
        )
        rows = []
        for dguid in BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID:
            rows.append(
                f'"2026-Q2","Province {dguid}","{dguid}","Factory",'
                '"Concrete","Index, 2023=100","110.0","",""'
            )
        rows.append(
            '"2026-Q2","Prince Edward Island","2021A000211","Factory",'
            '"Concrete","Index, 2023=100","109.0","",""'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "bcpi.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("18100289.csv", header + "\n".join(rows) + "\n")
            with self.assertRaisesRegex(ValidationError, "source province coverage changed"):
                normalize_bcpi_provinces(archive_path, root / "output.csv")

    def test_bcpi_reference_province_normalizer_keeps_target_scope(self) -> None:
        header = (
            '"REF_DATE","GEO","DGUID","Type of building","Division",'
            '"UOM","VALUE","STATUS","SYMBOL"\n'
        )
        buildings = (
            "Institutional buildings [62213]",
            "School",
            "Office building [62212]",
            "Bus depot with maintenance and repair facilities",
        )
        rows = []
        for dguid in BCPI_REFERENCE_PROVINCE_DGUID_TO_GEOGRAPHY_ID:
            for building in buildings:
                rows.append(
                    f'"2026-Q2","Province {dguid}","{dguid}",'
                    f'"{building}","Division composite",'
                    '"Index, 2023=100","110.0","",""'
                )
        rows.append(
            '"2026-Q2","Alberta","2021A000248",'
            '"School","Division composite","Index, 2023=100",'
            '"112.0","",""'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "bcpi.zip"
            output_path = root / "reference.csv"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("18100289.csv", header + "\n".join(rows) + "\n")
            observations = normalize_bcpi_reference_provinces(
                archive_path, output_path
            )
            output = output_path.read_text(encoding="utf-8")
        self.assertEqual(len(observations), 12)
        self.assertEqual(
            {item.geography_id for item in observations},
            set(BCPI_REFERENCE_PROVINCE_DGUID_TO_GEOGRAPHY_ID.values()),
        )
        self.assertNotIn("2021A000248", output)
        self.assertIn(
            "TR_STATCAN_BCPI_BC_ON_QC_REFERENCE_CLASSES_1_0_0", output
        )

    def test_bcpi_reference_province_normalizer_requires_every_class(self) -> None:
        header = (
            '"REF_DATE","GEO","DGUID","Type of building","Division",'
            '"UOM","VALUE","STATUS","SYMBOL"\n'
        )
        rows = [
            f'"2026-Q2","Province {dguid}","{dguid}",'
            '"School","Division composite","Index, 2023=100",'
            '"110.0","",""'
            for dguid in BCPI_REFERENCE_PROVINCE_DGUID_TO_GEOGRAPHY_ID
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "bcpi.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("18100289.csv", header + "\n".join(rows) + "\n")
            with self.assertRaisesRegex(
                ValidationError, "reference-class coverage changed"
            ):
                normalize_bcpi_reference_provinces(
                    archive_path, root / "output.csv"
                )

    def test_jvws_normalizer_preserves_suppression_and_trade_mapping(self) -> None:
        header = (
            '"REF_DATE","GEO","DGUID","National Occupational Classification",'
            '"Statistics","UOM","VALUE","STATUS","SYMBOL","TERMINATED"\n'
        )
        rows = [
            '"2026-01","Alberta","2021A000248","Electricians (except industrial and power system) [72200]","Job vacancies","Number","460","E","",""',
            '"2026-01","Alberta","2021A000248","Electrical power line and cable workers [72203]","Job vacancies","Number","","F","",""',
            '"2026-01","Ontario","2021A000235","Electricians (except industrial and power system) [72200]","Job vacancies","Number","1000","A","",""',
            '"2026-01","Alberta","2021A000248","Carpenters [72310]","Job vacancies","Number","900","A","",""',
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "jvws.zip"
            output_path = root / "labour.csv"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("14100444.csv", header + "\n".join(rows) + "\n")
            observations = normalize_jvws_alberta(archive_path, output_path)
            self.assertEqual(len(observations), 2)
            self.assertEqual(observations[0].value, 460.0)
            self.assertEqual(observations[1].value, None)
            self.assertIn("status:F", observations[1].quality_flags)
            self.assertIn("value_missing_or_suppressed", observations[1].quality_flags)
            output = output_path.read_text(encoding="utf-8")
            self.assertIn("trade_electricians", output)
            self.assertIn("trade_power_line", output)
            self.assertNotIn("Ontario", output)

    def test_jvws_canada_normalizer_keeps_provinces_separate(self) -> None:
        header = (
            '"REF_DATE","GEO","DGUID","National Occupational Classification",'
            '"Statistics","UOM","VALUE","STATUS","SYMBOL","TERMINATED"\n'
        )
        rows = [
            '"2026-01","Alberta","2021A000248","Electricians (except industrial and power system) [72200]","Job vacancies","Number","460","E","",""',
            '"2026-01","Ontario","2021A000235","Electricians (except industrial and power system) [72200]","Job vacancies","Number","1000","A","",""',
            '"2026-01","Canada","2021A000011124","Electricians (except industrial and power system) [72200]","Job vacancies","Number","3000","A","",""',
            '"2026-01","Calgary, Alberta","2021S05004830","Electricians (except industrial and power system) [72200]","Job vacancies","Number","200","A","",""',
            '"2026-01","Edmonton economic region, Alberta","2021A00034820","Electricians (except industrial and power system) [72200]","Job vacancies","Number","250","A","",""',
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "jvws.zip"
            output_path = root / "labour_canada.csv"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("14100444.csv", header + "\n".join(rows) + "\n")
            observations = normalize_jvws_canada(archive_path, output_path)
            self.assertEqual(len(observations), 2)
            self.assertEqual({item.geography_id for item in observations}, {"PR_35", "PR_48"})
            output = output_path.read_text(encoding="utf-8")
            self.assertIn("Alberta,2021A000248", output)
            self.assertIn("Ontario,2021A000235", output)
            self.assertNotIn("Canada,2021A000011124", output)
            self.assertNotIn("Calgary, Alberta", output)
            self.assertNotIn("Edmonton economic region", output)
            self.assertIn("TR_STATCAN_JVWS_CA_PROVINCES_NOC_1_0_0", output)

    def test_census_workforce_request_has_exact_province_trade_scope(self) -> None:
        metadata = census_metadata_fixture()
        requests, cells = census_workforce_requests(metadata)
        self.assertEqual(len(requests), 78)
        self.assertEqual(len(cells), 78)
        self.assertEqual({cell["geography_id"] for cell in cells}, set(PROVINCE_DGUID_TO_GEOGRAPHY_ID.values()))
        self.assertEqual({cell["noc_code"] for cell in cells}, set(TRADE_NOC_TO_NODE))
        alberta_electrician = next(
            cell
            for cell in cells
            if cell["geography_id"] == "PR_48" and cell["noc_code"] == "72200"
        )
        self.assertEqual(alberta_electrician["coordinate"], "121.1.1.1.563.2.0.0.0.0")

    def test_census_workforce_normalizer_preserves_documented_zero_filler(self) -> None:
        metadata = census_metadata_fixture()
        _, cells = census_workforce_requests(metadata)
        responses = []
        zero_coordinate = next(
            cell["coordinate"]
            for cell in cells
            if cell["geography_id"] == "PR_11" and cell["noc_code"] == "72202"
        )
        for cell in cells:
            if cell["coordinate"] == zero_coordinate:
                responses.append(
                    {
                        "status": "FAILED",
                        "object": {
                            "responseStatusCode": 2,
                            "productId": CENSUS_WORKFORCE_PRODUCT_ID,
                            "coordinate": cell["coordinate"],
                            "vectorId": 0,
                            "vectorDataPoint": [],
                        },
                    }
                )
            else:
                responses.append(
                    {
                        "status": "SUCCESS",
                        "object": {
                            "responseStatusCode": 0,
                            "productId": CENSUS_WORKFORCE_PRODUCT_ID,
                            "coordinate": cell["coordinate"],
                            "vectorId": 0,
                            "vectorDataPoint": [
                                {
                                    "refPerRaw": "2021-01-01",
                                    "value": 10,
                                    "releaseTime": "2022-11-30T08:30",
                                    "statusCode": 0,
                                    "symbolCode": 0,
                                    "securityLevelCode": 0,
                                }
                            ],
                        },
                    }
                )
        raw_payload = {
            "source_id": "STATCAN_CENSUS_OCCUPATION_98100449",
            "product_id": CENSUS_WORKFORCE_PRODUCT_ID,
            "metadata": [{"status": "SUCCESS", "object": metadata}],
            "requests": cells,
            "responses": responses,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_path = root / "raw.json"
            output_path = root / "workforce.csv"
            raw_path.write_text(json.dumps(raw_payload), encoding="utf-8")
            observations = normalize_census_trade_employment(raw_path, output_path)
            self.assertEqual(len(observations), 78)
            zero = next(
                item
                for item in observations
                if item.geography_id == "PR_11"
                and item.indicator_id.endswith("NOC_72202")
            )
            self.assertEqual(zero.value, 0.0)
            self.assertIn("census_zero_filler", zero.quality_flags)
            self.assertNotIn("value_missing_or_suppressed", zero.quality_flags)

    def test_major_projects_token_extraction(self) -> None:
        html = '<form><input name="__RequestVerificationToken" type="hidden" value="public-session-token" /></form>'
        self.assertEqual(extract_verification_token(html), "public-session-token")

    def test_ai_classifier_avoids_alberta_infrastructure_abbreviation(self) -> None:
        self.assertEqual(
            classify_ai_relevance(
                "Hospital power upgrade",
                "Institutional",
                "Alberta Infrastructure (AI) will expand the facility.",
            )[0],
            "none",
        )
        self.assertEqual(
            classify_ai_relevance("Wonder Valley AI Data Centre Park", "Industrial", "")[0],
            "core_data_centre",
        )
        self.assertEqual(
            classify_ai_relevance(
                "Greenlight Electricity Centre",
                "Power",
                "Generation intended to supply data center demand.",
            )[0],
            "enabling_power",
        )

    def test_project_schedule_and_coordinates(self) -> None:
        self.assertEqual(schedule_years("2027 - 2030"), (2027, 2030))
        self.assertEqual(schedule_years("Completion by 2030"), (None, 2030))
        point = '{"geometry":{"type":"Point","coordinates":[-113.5,53.5]}}'
        self.assertEqual(extract_coordinates(point), (-113.5, 53.5, 1))

    def test_digest_rejects_scenario_as_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            items = root / "items.json"
            items.write_text(
                '{"items":[{"headline":"Test","source_id":"X","source_url":"https://example.com",'
                '"observed_change":"Change","model_implication":"Implication","evidence_status":"scenario"}]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValidationError, "cannot present"):
                build_digest(items, root / "digest.md", date(2026, 8, 31))


def census_metadata_fixture() -> dict:
    province_member_ids = {
        "10": 2,
        "11": 7,
        "12": 10,
        "13": 16,
        "24": 26,
        "35": 56,
        "46": 104,
        "47": 111,
        "48": 121,
        "59": 141,
        "60": 170,
        "61": 172,
        "62": 174,
    }
    province_names = {
        "10": "Newfoundland and Labrador",
        "11": "Prince Edward Island",
        "12": "Nova Scotia",
        "13": "New Brunswick",
        "24": "Quebec",
        "35": "Ontario",
        "46": "Manitoba",
        "47": "Saskatchewan",
        "48": "Alberta",
        "59": "British Columbia",
        "60": "Yukon",
        "61": "Northwest Territories",
        "62": "Nunavut",
    }
    occupations = {
        "72200": (563, "Electricians (except industrial and power system)"),
        "72201": (564, "Industrial electricians"),
        "72202": (565, "Power system electricians"),
        "72203": (566, "Electrical power line and cable workers"),
        "72402": (584, "Heating, refrigeration and air conditioning mechanics"),
        "73100": (615, "Concrete finishers"),
    }
    return {
        "responseStatusCode": 0,
        "productId": str(CENSUS_WORKFORCE_PRODUCT_ID),
        "issueDate": "2022-11-30",
        "dimension": [
            {
                "dimensionPositionId": 1,
                "dimensionNameEn": "Geography",
                "member": [
                    {
                        "memberId": province_member_ids[code],
                        "memberNameEn": province_names[code],
                        "classificationCode": code,
                        "geoLevel": 2,
                    }
                    for code in province_member_ids
                ],
            },
            {
                "dimensionPositionId": 2,
                "dimensionNameEn": "Highest certificate, diploma or degree (16)",
                "member": [
                    {
                        "memberId": 1,
                        "memberNameEn": "Total - Highest certificate, diploma or degree",
                    }
                ],
            },
            {
                "dimensionPositionId": 3,
                "dimensionNameEn": "Age (15A)",
                "member": [{"memberId": 1, "memberNameEn": "Total - Age"}],
            },
            {
                "dimensionPositionId": 4,
                "dimensionNameEn": "Gender (3)",
                "member": [{"memberId": 1, "memberNameEn": "Total - Gender"}],
            },
            {
                "dimensionPositionId": 5,
                "dimensionNameEn": "Occupation - Unit group - National Occupational Classification (NOC) 2021 (821A)",
                "member": [
                    {"memberId": member_id, "memberNameEn": f"{code} {label}"}
                    for code, (member_id, label) in occupations.items()
                ],
            },
            {
                "dimensionPositionId": 6,
                "dimensionNameEn": "Labour force status (3)",
                "member": [{"memberId": 2, "memberNameEn": "Employed"}],
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
