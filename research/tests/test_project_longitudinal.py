import tempfile
import unittest
from pathlib import Path
from aiio.project_longitudinal import retain_snapshot, reconcile_snapshots, build_history
from aiio.schemas import ValidationError


def row(project="1", vintage="2026-08-31", cost="100", stage="construction"):
    return {"source_id": "ALBERTA_MAJOR_PROJECTS", "source_record_id": project,
            "project_id": "ABMP_" + project, "source_as_of_date": vintage,
            "snapshot_date": "2026-10-03", "name": "Hospital", "asset_class": "health_facilities",
            "estimated_cost_cad": cost, "stage": stage, "start_period": "2025", "completion_period": "2027"}


class ProjectLongitudinalTests(unittest.TestCase):
    def test_build_date_cannot_create_observation(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder)
            first = retain_snapshot([row()], archive)
            newer_build = {**row(), "snapshot_date": "2026-11-01"}
            self.assertEqual(first, retain_snapshot([newer_build], archive))
            newer_verification = {**newer_build, "source_as_of_date": "2026-11-01"}
            self.assertEqual(first, retain_snapshot([newer_verification], archive))
            self.assertEqual(len(list(archive.glob("*.json"))), 1)
            self.assertEqual(build_history(archive)["sources"]["ALBERTA_MAJOR_PROJECTS"]["dated_vintage_count"], 1)

    def test_other_source_change_does_not_create_unchanged_region_history(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder)
            comparator = {**row(), "source_id": "QUEBEC_PQI_PROJECT_DASHBOARD"}
            retain_snapshot([row(), comparator], archive)
            retain_snapshot([row(vintage="2026-09-30"), {**comparator, "stage": "in_service", "source_as_of_date": "2026-09-30"}], archive)
            history = build_history(archive)["sources"]
            self.assertEqual(history["ALBERTA_MAJOR_PROJECTS"]["dated_vintage_count"], 1)
            self.assertEqual(history["QUEBEC_PQI_PROJECT_DASHBOARD"]["dated_vintage_count"], 2)

    def test_changes_require_later_publisher_date(self):
        conflict = reconcile_snapshots([row()], [row(cost="200")])[0]
        self.assertFalse(conflict["eligible_dated_revision"])
        later = reconcile_snapshots([row()], [row(vintage="2026-09-30", cost="200")])[0]
        self.assertTrue(later["eligible_dated_revision"])
        self.assertEqual(later["scope_price_basis_reconciliation"], "pending")
        self.assertFalse(later["final_cost_outturn"])

    def test_disappearance_is_not_completion(self):
        events = reconcile_snapshots([row(), row(project="2")], [row()])
        self.assertEqual(events[0]["event_type"], "not_in_later_inventory")
        self.assertFalse(events[0]["completion_inferred"])

    def test_duplicate_ids_fail_closed(self):
        with self.assertRaises(ValidationError):
            reconcile_snapshots([], [row(), row()])

    def test_retained_history_reconciles_later_date(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder)
            retain_snapshot([row()], archive)
            retain_snapshot([row(vintage="2026-09-30", stage="in_service")], archive)
            source = build_history(archive)["sources"]["ALBERTA_MAJOR_PROJECTS"]
            self.assertEqual(source["dated_vintage_count"], 2)
            self.assertEqual(source["reconciled_events"][0]["changes"]["stage"]["after"], "in_service")
            self.assertFalse(source["reconciled_events"][0]["completion_inferred"])


if __name__ == "__main__":
    unittest.main()
