"""Run the original research suite, disclosing unavailable-source checks as skips."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OMITTED = {
    'test_power_planning.ProvincialPowerPlanningContractTests.test_committed_artifacts_are_reproducible_and_fail_closed': 'Complete provincial source XLSX/PDF/HTML not redistributed.',
    'test_power_planning.ProvincialPowerPlanningContractTests.test_xlsx_locator_is_checked_against_source_cell': 'Original IESO workbook not redistributed; source-cell validation unavailable.',
    'test_power_planning.ProvincialPowerPlanningContractTests.test_incompatible_unit_contract_is_rejected': 'Original provincial source-file preflight unavailable before unit validation.',
    'test_power_planning.ProvincialPowerPlanningContractTests.test_source_hash_drift_is_rejected': 'Original provincial source-file preflight unavailable before hash-drift validation.',
    'test_provincial_projects.ProvincialProjectArtifactTests.test_committed_artifacts_are_reproducible_and_fail_closed': 'Contact-bearing full BC provider export omitted; normalized public derivative retained.',
}

def apply_boundary(suite: unittest.TestSuite) -> None:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            apply_boundary(item)
        elif item.id() in OMITTED:
            method = item._testMethodName
            original = getattr(item, method)
            def skipped(reason=OMITTED[item.id()]):
                raise unittest.SkipTest(reason)
            setattr(item, method, skipped)

suite = unittest.defaultTestLoader.discover(str(ROOT / 'research/tests'))
apply_boundary(suite)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print('Public-snapshot source omissions are skips, not passed source validation. Original research:test remains available for a rights-cleared full-source workspace.')
sys.exit(0 if result.wasSuccessful() else 1)
