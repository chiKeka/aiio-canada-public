"""Separate evidence availability, proxy validation and causal authorization.

This assessment does not authorize forecasts. Unimplemented validation receipts
remain not_assessed rather than being inferred from disclosure or causal gates.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

from .schemas import ValidationError


PROXY_REPORT = "data/model-runs/ai_construction_proxy_alberta_v0.1.json"
PROXY_ROWS = "data/processed/ai_construction_proxy_alberta_v0.1.csv"
ASSOCIATION_REPORT = "data/model-runs/ai_attribution_proxy_association_v0.1.json"


def assess_proxy_planning(root: Path) -> dict:
    proxy = json.loads((root / PROXY_REPORT).read_text())
    association = json.loads((root / ASSOCIATION_REPORT).read_text())
    for name, digest in {**proxy["input_manifest"], PROXY_ROWS: proxy["output_sha256"]}.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValidationError("proxy validation input is missing or outside repository")
        if "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValidationError(f"proxy validation source drift: {name}")
    with (root / PROXY_ROWS).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValidationError("proxy validation requires exposure rows")
    ordered = True
    for row in rows:
        values = [float(row[f"reconstructed_proxy_{case}_cad"]) for case in ("low", "central", "high")]
        ordered &= all(math.isfinite(value) for value in values) and 0 <= values[0] <= values[1] <= values[2]
    cases = {item["proxy_case"] for item in association["results"]}
    checks = [
        {"id": "lineage", "status": "pass", "finding": "Reconstruction input hashes and quarterly output reconcile.", "next_step": None},
        {"id": "uncertainty_cases", "status": "pass" if ordered and cases == {"low", "central", "high"} else "fail", "finding": "Ordered exposure sensitivity cases are checked; these are not predictive intervals.", "next_step": "Validate interval coverage on held-out observations."},
        {"id": "scope_coverage", "status": "not_assessed", "finding": f"{proxy['costed_project_count']} costed project, {proxy['permit_candidate_count']} permit candidates; {proxy['geography_count']} markets. No validated project/horizon domain.", "next_step": "Lock the target market, asset, outcome, horizon and minimum independent-event coverage before fitting."},
        {"id": "timing_validation", "status": "not_assessed", "finding": "Quarterly allocation uses an assumed construction profile; permit issue is not expenditure timing.", "next_step": "Compare timing alternatives against dated construction milestones; disclose monthly interpolation."},
        {"id": "out_of_sample_performance", "status": "not_assessed", "finding": "Existing association fit is in-sample; repeated asset rows are not independent events.", "next_step": "Run time-blocked rolling-origin backtests against a baseline-only benchmark, with locked error and interval-coverage tolerances."},
        {"id": "overlap_and_double_counting", "status": "not_assessed", "finding": "Permit/project linkage is unresolved; separate components do not establish non-overlap.", "next_step": "Link records or bound overlap, test leave-one-project/source-out sensitivity, and reconcile baseline versus incremental pressure."},
        {"id": "independent_planning_review", "status": "not_assessed", "finding": "No scope-specific proxy-planning validation receipt has been accepted.", "next_step": "Review the frozen model, validation metrics, source coverage and claim language; bind the verdict to input/model hashes."},
    ]
    return {
        "schema_version": "1.0.0",
        "assessment_id": "AIIO_PROXY_PLANNING_VALIDATION_0_1",
        "status": "validation_incomplete",
        "checks": checks,
        "passed_check_count": sum(check["status"] == "pass" for check in checks),
        "check_count": len(checks),
        "levels": {
            "observed_evidence": "display_with_source_scope_and_date",
            "assumption_scenarios": "available_not_validated_estimates",
            "proxy_planning": "validation_incomplete",
            "causal_attribution": "separate_identification_gate",
        },
        "publication_boundary": {
            "scenario_sensitivity_allowed": True,
            "validated_proxy_estimate_allowed": False,
            "causal_attribution_allowed": False,
            "requires_private_realized_spending_or_labour_hours": False,
            "ai_attributable_effect": None,
        },
        "input_manifest": {name: "sha256:" + hashlib.sha256((root / name).read_bytes()).hexdigest() for name in (PROXY_REPORT, PROXY_ROWS, ASSOCIATION_REPORT)},
    }
