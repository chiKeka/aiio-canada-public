from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.power_evidence import run_power_evidence_screen


class PowerEvidenceScreenTests(unittest.TestCase):
    def test_reconciles_limit_contracts_and_keeps_transmission_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "source.pdf"
            pdf.write_bytes(b"fixture pdf")
            digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
            manual = root / "manual.json"
            manual.write_text(
                json.dumps(
                    {
                        "source_id": "AESO_DATA_CENTRE_UPDATE_2025_09",
                        "source_content_hash": f"sha256:{digest}",
                        "source_locator": "page 1 chart",
                        "review_status": "independently_reviewed",
                        "reviewed_by": "independent fixture reviewer",
                        "reviewer_type": "test_fixture",
                        "reviewed_at": "2026-08-31",
                        "review_record": "fixture-review-record",
                        "requested_load_series": [
                            {"application_period": "2024-Q2", "requested_load_mw": 5000},
                            {"application_period": "2024-Q3", "requested_load_mw": 6400},
                            {"application_period": "2024-Q4", "requested_load_mw": 10900},
                            {"application_period": "2025-Q1", "requested_load_mw": 14600},
                            {"application_period": "2025-Q2", "requested_load_mw": 19800},
                            {"application_period": "2025-Q3", "requested_load_mw": 20700},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            large_load = root / "large.html"
            large_load.write_text(
                "All 1,200 MW of the interim connection limit was successfully allocated "
                "P2936 GLDC Load - <strong>970 MW</strong> "
                "P3083 Keephills Data Centre Phase I - <strong>230 MW</strong>",
                encoding="utf-8",
            )
            interim = root / "interim.html"
            interim.write_text(
                "interim limit of 1,200 MW. "
                "No new transmission system reinforcements or upgrades are required",
                encoding="utf-8",
            )
            result = run_power_evidence_screen(
                manual,
                pdf,
                large_load,
                interim,
                root / "power.json",
                root / "power.csv",
            )
        self.assertEqual(result["phase1"]["allocated_mw"], 1200)
        self.assertEqual(len(result["metrics"]), 10)
        self.assertNotIn(
            "AIIO_PHASE1_ALLOCATED_SHARE_OF_Q3_2025_REQUESTS",
            {item["metric_id"] for item in result["metrics"]},
        )
        self.assertEqual(
            result["manual_extraction_review"]["status"],
            "independently_reviewed",
        )
        self.assertFalse(
            result["transmission_boundary"][
                "phase1_new_transmission_reinforcement_required"
            ]
        )
        self.assertIsNone(
            result["transmission_boundary"][
                "additional_transmission_required_for_50b_counterfactual_mw"
            ]
        )


if __name__ == "__main__":
    unittest.main()
