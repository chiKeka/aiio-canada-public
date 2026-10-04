from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiio.adapters.statcan import (
    JVWS_STATISTICS,
    PROVINCE_DGUID_TO_GEOGRAPHY_ID,
    TRADE_NOC_TO_NODE,
)
from aiio.release import (
    labour_workforce_stock_canada,
    latest_labour_availability,
    latest_labour_availability_canada,
    sha256_file,
    validate_cost_baseline_publication,
    verify_manifest,
    write_json,
)
from aiio.schemas import ValidationError


class ReleaseVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.version = "test"
        self.release_dir = self.root / "data" / "releases" / self.version
        self.public_dir = self.root / "public" / "data"
        self.release_dir.mkdir(parents=True)
        self.public_dir.mkdir(parents=True)
        self.input_path = self.root / "input.json"
        self.output_path = self.release_dir / "output.json"
        self.input_path.write_text('{"value": 1}\n', encoding="utf-8")
        self.output_path.write_text('{"result": 2}\n', encoding="utf-8")
        self.manifest = {
            "code_commit": "abc123",
            "inputs": {"input": sha256_file(self.input_path)},
            "outputs": {"output.json": sha256_file(self.output_path)},
        }
        write_json(self.release_dir / "manifest.json", self.manifest)
        write_json(self.public_dir / "latest.json", {"manifest": self.manifest})

    def write_canada_labour(
        self,
        path: Path,
        *,
        omit_geography: str | None = None,
        omit_pair_for: tuple[str, str, str] | None = None,
        mismatch_geography: bool = False,
    ) -> None:
        header = (
            "observation_id,indicator_id,geography_label,statcan_dguid,noc_code,"
            "occupation_label,trade_node_id,statistic,value,unit,geography_id,"
            "period_start,period_end,source_id,evidence_status,as_of_date,"
            "transformation_id,quality_flags"
        )
        labels = {"PR_48": "Alberta", "PR_35": "Ontario", "PR_46": "Manitoba"}
        rows = [header]
        for dguid, geography_id in PROVINCE_DGUID_TO_GEOGRAPHY_ID.items():
            if geography_id == omit_geography:
                continue
            published_geography_id = (
                "PR_48" if mismatch_geography and geography_id == "PR_10" else geography_id
            )
            for noc_code, trade_node_id in TRADE_NOC_TO_NODE.items():
                for statistic in sorted(JVWS_STATISTICS):
                    if omit_pair_for == (geography_id, noc_code, statistic):
                        continue
                    is_ab_missing = (
                        geography_id == "PR_48"
                        and noc_code == "72200"
                        and statistic == "Average offered hourly wage"
                    )
                    is_mb_zero = (
                        geography_id == "PR_46"
                        and noc_code == "72203"
                        and statistic == "Job vacancies"
                    )
                    value = "" if is_ab_missing else ("0.0" if is_mb_zero else "10")
                    status = "F" if is_ab_missing else "A"
                    flags = (
                        "status:F|value_missing_or_suppressed"
                        if is_ab_missing
                        else f"status:{status}"
                    )
                    unit = "Dollars" if statistic == "Average offered hourly wage" else "Number"
                    statistic_slug = statistic.upper().replace(" ", "_")
                    rows.append(
                        f"OBS_{geography_id}_{noc_code}_{statistic_slug},"
                        f"JVWS_{statistic_slug}_NOC_{noc_code},"
                        f"{labels.get(geography_id, geography_id)},{dguid},{noc_code},"
                        f"Occupation {noc_code},{trade_node_id},{statistic},{value},{unit},"
                        f"{published_geography_id},2026-01-01,2026-03-31,"
                        "STATCAN_JVWS_14100444,observed,2026-03-31,TR_CA,"
                        f"{flags}"
                    )
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    def write_workforce_stock(
        self,
        path: Path,
        *,
        omit_geography: str | None = None,
        mismatch_geography: bool = False,
    ) -> None:
        header = (
            "observation_id,indicator_id,geography_label,statcan_dguid,province_code,"
            "noc_code,occupation_label,trade_node_id,statistic,value,unit,geography_id,"
            "period_start,period_end,release_date,source_id,evidence_status,as_of_date,"
            "transformation_id,quality_flags,coordinate"
        )
        rows = [header]
        for dguid, geography_id in PROVINCE_DGUID_TO_GEOGRAPHY_ID.items():
            if geography_id == omit_geography:
                continue
            published_geography_id = (
                "PR_48" if mismatch_geography and geography_id == "PR_10" else geography_id
            )
            province_code = geography_id.removeprefix("PR_")
            for noc_code, trade_node_id in TRADE_NOC_TO_NODE.items():
                is_zero = geography_id == "PR_11" and noc_code == "72202"
                value = "0" if is_zero else "100"
                flags = (
                    "census_long_form_25pct_sample|random_rounding|"
                    "wds_response_status_code:2|census_zero_filler"
                    if is_zero
                    else "census_long_form_25pct_sample|random_rounding"
                )
                rows.append(
                    f"OBS_{geography_id}_{noc_code},CENSUS_EMPLOYED_PERSONS_NOC_{noc_code},"
                    f"{geography_id},{dguid},{province_code},{noc_code},Occupation {noc_code},"
                    f"{trade_node_id},Employed,{value},Persons,{published_geography_id},"
                    "2021-05-02,2021-05-08,2022-11-30,"
                    "STATCAN_CENSUS_OCCUPATION_98100449,observed,2021-05-08,TR_CENSUS,"
                    f"{flags},COORD_{geography_id}_{noc_code}"
                )
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    def verify(self) -> None:
        with (
            patch("aiio.release.release_input_paths", return_value={"input": self.input_path}),
            patch("aiio.release.git_state", return_value=("abc123", False)),
        ):
            verify_manifest(self.root, self.version)

    def test_verifier_accepts_matching_inputs_outputs_and_commit(self) -> None:
        self.verify()

    def test_public_release_rejects_unauthorized_cost_baseline(self) -> None:
        with self.assertRaisesRegex(ValidationError, "independent modelling gate"):
            validate_cost_baseline_publication(
                {
                    "publication_authorization": {
                        "public_projection_authorized": False
                    }
                }
            )

    def test_public_release_accepts_authorized_cost_baseline(self) -> None:
        validate_cost_baseline_publication(
            {
                "publication_authorization": {
                    "public_projection_authorized": True
                }
            }
        )

    def test_verifier_rejects_tampered_input(self) -> None:
        self.input_path.write_text('{"value": 9}\n', encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "input hash mismatch"):
            self.verify()

    def test_verifier_rejects_extra_manifest_input(self) -> None:
        self.manifest["inputs"]["undeclared"] = "sha256:not-used"
        write_json(self.release_dir / "manifest.json", self.manifest)
        write_json(self.public_dir / "latest.json", {"manifest": self.manifest})
        with self.assertRaisesRegex(ValidationError, "key set"):
            self.verify()

    def test_verifier_rejects_wrong_checked_out_commit(self) -> None:
        with (
            patch("aiio.release.release_input_paths", return_value={"input": self.input_path}),
            patch("aiio.release.git_state", return_value=("different", False)),
        ):
            with self.assertRaisesRegex(ValidationError, "HEAD"):
                verify_manifest(self.root, self.version)

    def test_verifier_allows_newer_pipeline_inputs_absent_from_old_manifest(self) -> None:
        newer_input = self.root / "newer.json"
        newer_input.write_text('{"new": true}\n', encoding="utf-8")
        with (
            patch(
                "aiio.release.release_input_paths",
                return_value={"input": self.input_path, "newer": newer_input},
            ),
            patch("aiio.release.git_state", return_value=("abc123", False)),
        ):
            verify_manifest(self.root, self.version)

    def test_latest_labour_baseline_keeps_suppressed_value_missing(self) -> None:
        labour_path = self.root / "labour.csv"
        labour_path.write_text(
            "observation_id,indicator_id,noc_code,occupation_label,trade_node_id,statistic,value,unit,geography_id,period_start,period_end,source_id,evidence_status,as_of_date,transformation_id,quality_flags\n"
            "OBS_OLD,JVWS_JOB_VACANCIES_NOC_72203,72203,Power line workers,trade_power_line,Job vacancies,50,Number,PR_48,2025-10-01,2025-12-31,STATCAN_JVWS_14100444,observed,2025-12-31,TR_TEST,status:E\n"
            "OBS_NEW,JVWS_JOB_VACANCIES_NOC_72203,72203,Power line workers,trade_power_line,Job vacancies,,Number,PR_48,2026-01-01,2026-03-31,STATCAN_JVWS_14100444,observed,2026-03-31,TR_TEST,status:F|value_missing_or_suppressed\n",
            encoding="utf-8",
        )
        baseline = latest_labour_availability(labour_path)
        self.assertEqual(baseline["period_end"], "2026-03-31")
        self.assertIsNone(baseline["observations"][0]["value"])
        self.assertIn(
            "value_missing_or_suppressed",
            baseline["observations"][0]["quality_flags"],
        )

    def test_canada_labour_snapshot_reports_missingness_by_province(self) -> None:
        labour_path = self.root / "labour_canada.csv"
        self.write_canada_labour(labour_path)
        baseline = latest_labour_availability_canada(labour_path)
        self.assertEqual(len(baseline["coverage"]), 13)
        alberta = next(
            item for item in baseline["coverage"] if item["geography_id"] == "PR_48"
        )
        self.assertEqual(alberta["observed_cells"], 11)
        self.assertEqual(alberta["not_published_cells"], 1)
        self.assertEqual(alberta["coverage_percent"], 91.7)
        self.assertIsNone(
            next(
                item
                for item in baseline["observations"]
                if item["geography_id"] == "PR_48"
                and item["noc_code"] == "72200"
                and item["statistic"] == "Average offered hourly wage"
            )["value"]
        )
        manitoba_zero = next(
            item
            for item in baseline["observations"]
            if item["geography_id"] == "PR_46"
            and item["noc_code"] == "72203"
            and item["statistic"] == "Job vacancies"
        )
        self.assertEqual(manitoba_zero["value"], 0.0)

    def test_canada_labour_snapshot_requires_all_13_geographies(self) -> None:
        labour_path = self.root / "labour_canada_missing_geo.csv"
        self.write_canada_labour(labour_path, omit_geography="PR_62")
        with self.assertRaisesRegex(ValidationError, "exactly 13"):
            latest_labour_availability_canada(labour_path)

    def test_canada_labour_snapshot_requires_all_12_cells(self) -> None:
        labour_path = self.root / "labour_canada_missing_cell.csv"
        self.write_canada_labour(
            labour_path,
            omit_pair_for=("PR_48", "72200", "Job vacancies"),
        )
        with self.assertRaisesRegex(ValidationError, "incomplete for PR_48"):
            latest_labour_availability_canada(labour_path)

    def test_canada_labour_snapshot_rejects_dguid_geography_mismatch(self) -> None:
        labour_path = self.root / "labour_canada_mismatch.csv"
        self.write_canada_labour(labour_path, mismatch_geography=True)
        with self.assertRaisesRegex(ValidationError, "mismatched geography"):
            latest_labour_availability_canada(labour_path)

    def test_workforce_stock_requires_13_geographies_and_preserves_zero(self) -> None:
        workforce_path = self.root / "workforce.csv"
        self.write_workforce_stock(workforce_path)
        baseline = labour_workforce_stock_canada(workforce_path)
        self.assertEqual(len(baseline["coverage"]), 13)
        self.assertEqual(len(baseline["observations"]), 78)
        pei = next(
            item for item in baseline["coverage"] if item["geography_id"] == "PR_11"
        )
        self.assertEqual(pei["zero_filler_cells"], 1)
        zero = next(
            item
            for item in baseline["observations"]
            if item["geography_id"] == "PR_11" and item["noc_code"] == "72202"
        )
        self.assertEqual(zero["value"], 0.0)

    def test_workforce_stock_rejects_missing_geography(self) -> None:
        workforce_path = self.root / "workforce_missing.csv"
        self.write_workforce_stock(workforce_path, omit_geography="PR_62")
        with self.assertRaisesRegex(ValidationError, "exactly 13"):
            labour_workforce_stock_canada(workforce_path)

    def test_workforce_stock_rejects_dguid_geography_mismatch(self) -> None:
        workforce_path = self.root / "workforce_mismatch.csv"
        self.write_workforce_stock(workforce_path, mismatch_geography=True)
        with self.assertRaisesRegex(ValidationError, "mismatched"):
            labour_workforce_stock_canada(workforce_path)


if __name__ == "__main__":
    unittest.main()
