from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .schemas import ValidationError


SURFACE_ID = "AIIO_CANADA_RESEARCH_SURFACE_0_1"
ARTIFACTS = [
    ("source_receipts", "public/data/source-receipts.json", "governance"),
    ("enabling_infrastructure", "data/scenarios/alberta_enabling_infrastructure_v0.1.json", "assumption"),
    ("alberta_delivery_register", "data/governance/alberta-delivery-register.json", "governance"),
    ("alberta_comparison_baseline", "data/governance/alberta-comparison-baseline.json", "published_evidence_bundle"),
    ("construction_projects", "public/data/construction/projects.json", "observed_inventory"),
    ("construction_benchmarks", "public/data/construction/benchmarks.json", "mixed_evidence_reference"),
    ("construction_briefing", "public/data/construction/briefing.json", "observed_and_analytical"),
    ("construction_manifest", "public/data/construction/manifest.json", "provenance"),
    ("construction_snapshot", "public/data/construction/snapshot.json", "published_evidence_bundle"),
    ("adm_evidence", "public/data/construction/adm-evidence.json", "observed_and_analytical"),
    ("adm_deck_pointer", "public/data/construction/adm-deck.json", "provenance"),
    ("alberta_boom_analog", "public/data/alberta-boom-analog.json", "observed_historical_comparison"),
    ("frozen_release_bundle", "public/data/latest.json", "frozen_release"),
    ("frozen_release_manifest", "public/data/manifest.json", "governance"),
    ("latest_digest_pointer", "public/data/latest-digest.json", "governance"),
    ("reviewed_digest", "public/data/reviewed-digest.json", "reviewed_evidence_note"),
    ("program_gates", "data/governance/program-gates.json", "governance"),
    ("executive_monthly_escalation", "data/model-runs/executive_monthly_escalation_current.json", "withheld_model_output"),
    ("source_registry", "data/registry/sources.json", "source_provenance"),
    ("source_freshness", "public/data/source-freshness.json", "governance"),
    ("practical_evidence_route", "data/model-runs/practical_evidence_route_current.json", "governance"),
    ("authorized_revision_estimand_contract", "data/model/authorized_revision_estimand_contract_v0.1.json", "method_lineage"),
    ("pspe_method_lineage", "data/model-runs/pspe_method_lineage_v0.1.json", "method_lineage"),
    ("canada_cross_domain_coverage", "data/model-runs/canada_cross_domain_coverage_v0.1.json", "coverage_inventory"),
    ("alberta_graph", "data/model/alberta_graph_v0.2.json", "assumption"),
    ("scenario_suite", "data/model-runs/alberta_50b_scenario_suite_v0.1.json", "scenario"),
    ("historical_envelope", "data/model-runs/alberta_bcpi_historical_envelope_v0.1.json", "observed_descriptive"),
    ("historical_analog", "data/model-runs/alberta_project_historical_analog_matrix_v0.1.json", "historical_what_if"),
    ("reference_review", "data/model-runs/alberta_reference_cost_review_package_v0.1.json", "governance"),
    ("information_sector_capex", "data/model-runs/information_sector_construction_capex_screen_v0.1.json", "inferred_proxy"),
    ("cma_reference", "data/model-runs/vancouver_toronto_montreal_bcpi_reference_baseline_v0.1.json", "withheld_model_output"),
    ("regional_macro", "data/model-runs/regional_macro_controls_canada_v0.1.json", "observed_descriptive"),
    ("province_linked_reference", "data/model-runs/bc_on_qc_province_linked_reference_baseline_v0.1.json", "inferred_proxy"),
    ("ai_capex_ledger", "data/model-runs/alberta_ai_capex_announcement_ledger_v0.1.json", "observed_and_inferred"),
    ("attribution_readiness", "data/model-runs/ai_attribution_identification_readiness_v0.1.json", "governance"),
    ("panel_preflight", "data/model-runs/ai_attribution_panel_preflight_v0.1.json", "governance"),
    ("empirical_covariate_panel", "data/model-runs/ai_attribution_empirical_covariate_panel_v0.1.json", "observed_descriptive"),
    ("empirical_estimation", "data/model-runs/ai_attribution_empirical_estimation_v0.1.json", "withheld_model_output"),
    ("reconstructed_ai_construction_proxy", "data/model-runs/ai_construction_proxy_alberta_v0.1.json", "inferred_proxy"),
    ("proxy_association", "data/model-runs/ai_attribution_proxy_association_v0.1.json", "descriptive_proxy_analysis"),
    ("pspc_outcome_feasibility", "data/model-runs/pspc_real_property_outcome_feasibility_v0.1.json", "observed_reference"),
    ("treatment_source_feasibility", "data/model-runs/ai_attribution_treatment_source_feasibility_v0.1.json", "governance"),
    ("building_investment_controls", "data/model-runs/building_investment_controls_canada_v0.1.json", "observed_descriptive"),
    ("procurement_feasibility", "data/model-runs/canadabuys_construction_outcome_feasibility_v0.1.json", "governance"),
    ("edmonton_permit_proxy", "data/model-runs/edmonton_data_centre_permit_proxy_v0.1.json", "inferred_proxy"),
    ("vancouver_permit_proxy", "data/model-runs/vancouver_data_centre_permit_proxy_v0.1.json", "inferred_proxy"),
    ("toronto_permit_proxy", "data/model-runs/toronto_data_centre_permit_proxy_v0.1.json", "inferred_proxy"),
    ("montreal_permit_proxy", "data/model-runs/montreal_data_centre_permit_proxy_v0.1.json", "inferred_proxy"),
    ("comparison_market_panel", "data/model-runs/comparison_market_permit_bcpi_panel_v0.1.json", "observed_and_inferred"),
    ("comparison_market_association", "data/model-runs/comparison_market_proxy_association_v0.1.json", "descriptive_proxy_analysis"),
    ("audited_outcomes", "data/model-runs/oago_audited_project_outcomes_v0.1.json", "observed_reference"),
    ("quebec_revisions", "data/model-runs/quebec_pqi_authorized_project_revisions_v0.1.json", "observed_reference"),
    ("quebec_full_archive", "data/model-runs/quebec_pqi_full_archive_longitudinal_v0.1.json", "observed_and_inferred"),
    ("quebec_parser_review", "data/model-runs/quebec_pqi_parser_review_package_v0.1.json", "governance"),
]


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def build_research_surface_manifest(root: Path, output_path: Path | None) -> dict[str, Any]:
    root = root.resolve()
    artifacts = []
    digest = json.loads((root / "public/data/latest-digest.json").read_text(encoding="utf-8"))
    digest_artifacts = []
    if digest.get("status") == "approved":
        from datetime import date
        edition = date.fromisoformat(digest["edition_date"]).isoformat()
        digest_artifacts = [("reviewed_digest_manifest", f"data/digests/{edition}.manifest.json", "provenance"), ("digest_editorial_approval", f"data/digests/{edition}.approval.json", "governance")]
    for artifact_id, relative_path, evidence_role in [*ARTIFACTS, *digest_artifacts]:
        path = root / relative_path
        if not path.is_file():
            raise ValidationError(f"research-surface artifact is missing: {relative_path}")
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "path": relative_path,
                "evidence_role": evidence_role,
                "sha256": sha256_file(path),
            }
        )
    release_manifest = json.loads((root / "public/data/manifest.json").read_text(encoding="utf-8"))
    aggregate_payload = "\n".join(
        f"{item['path']}={item['sha256']}" for item in artifacts
    ).encode("utf-8")
    manifest = {
        "schema_version": "1.0.0",
        "surface_id": SURFACE_ID,
        "status": "workspace_research_preview",
        "frozen_release_version": release_manifest["version"],
        "frozen_release_id": release_manifest["release_id"],
        "artifact_count": len(artifacts),
        "artifact_manifest_sha256": f"sha256:{hashlib.sha256(aggregate_payload).hexdigest()}",
        "artifacts": artifacts,
        "publication_boundary": {
            "is_frozen_public_release": False,
            "decision_grade_ready": False,
            "ai_attributable_effect_authorized": False,
            "project_cost_forecast_authorized": False,
            "deployment_authorized": False,
            "note": "This manifest reconciles the evolving research workspace above the frozen public release. It does not promote supplemental artifacts into that release.",
        },
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return manifest


def validate_research_surface_manifest(root: Path, manifest_path: Path) -> dict[str, Any]:
    expected = build_research_surface_manifest(root, None)
    actual = json.loads(manifest_path.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValidationError("research-surface manifest is stale or does not reconcile")
    return actual
