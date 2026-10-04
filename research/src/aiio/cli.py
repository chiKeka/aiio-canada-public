from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

from .adapters.statcan import (
    normalize_bcpi_alberta,
    normalize_bcpi_provinces,
    normalize_bcpi_reference_cmas,
    normalize_bcpi_reference_provinces,
    normalize_jvws_alberta,
    normalize_jvws_canada,
)
from .adapters.statcan_census import (
    fetch_census_trade_employment,
    normalize_census_trade_employment,
)
from .adapters.statcan_investment import normalize_investment_controls
from .adapters.statcan_capex import normalize_information_sector_construction_capex
from .adapters.canadabuys import (
    AWARD_SOURCE_ID as CANADABUYS_AWARD_SOURCE_ID,
    CONTRACT_SOURCE_ID as CANADABUYS_CONTRACT_SOURCE_ID,
    TENDER_SOURCE_ID as CANADABUYS_TENDER_SOURCE_ID,
    normalize_canadabuys_outcome_intake,
)
from .adapters.edmonton_permits import (
    SOURCE_ID as EDMONTON_PERMIT_SOURCE_ID,
    fetch_edmonton_permit_candidates,
    normalize_edmonton_permit_proxy,
)
from .adapters.vancouver_permits import (
    SOURCE_ID as VANCOUVER_PERMIT_SOURCE_ID,
    fetch_vancouver_permit_candidates,
    normalize_vancouver_permit_proxy,
)
from .adapters.ckan_permit_proxies import (
    MONTREAL_SOURCE_ID as MONTREAL_PERMIT_SOURCE_ID,
    TORONTO_SOURCE_ID as TORONTO_PERMIT_SOURCE_ID,
    fetch_ckan_permit_candidates,
    normalize_ckan_permit_proxy,
)
from .audited_outcomes import run_audited_project_outcomes
from .quebec_revisions import (
    DICTIONARY_SOURCE_ID as QUEBEC_DICTIONARY_SOURCE_ID,
    run_quebec_authorized_revisions,
)
from .quebec_vintages import (
    retrieve_full_archive_resources,
    retrieve_milestone_resources,
)
from .quebec_longitudinal import run_quebec_milestone_longitudinal
from .quebec_review import build_quebec_parser_review_package
from .quebec_full_archive import run_quebec_full_archive_longitudinal
from .adapters.alberta_projects import fetch_major_projects, normalize_major_projects
from .adapters.provincial_projects import (
    BC_SOURCE_ID,
    ONTARIO_SOURCE_ID,
    QUEBEC_SOURCE_ID,
    normalize_provincial_projects,
)
from .calibration import (
    PROVINCIAL_REFERENCE_GEOGRAPHY_LABELS,
    PROVINCIAL_REFERENCE_LIMITATIONS,
    PROVINCIAL_REFERENCE_MODEL_ID,
    run_reference_class_baseline,
)
from .canada_coverage import build_canada_cross_domain_coverage
from .cma_calibration import run_cma_reference_class_baseline
from .provincial_backcast import run_province_linked_reference_backcast
from .provincial_backcast_review import (
    build_province_linked_review_package,
    validate_province_linked_review_verdict,
)
from .attribution import build_attribution_readiness
from .ai_capex_ledger import run_ai_capex_announcement_ledger
from .panel_preflight import run_panel_acquisition_preflight
from .empirical_panel import build_empirical_covariate_panel
from .empirical_estimation import run_empirical_estimation_gate
from .proxy_treatment import build_reconstructed_treatment_proxy
from .proxy_association import run_proxy_association
from .comparison_market_panel import build_comparison_market_panel
from .comparison_market_association import run_comparison_market_association
from .pspc_outcomes import normalize_pspc_outcomes
from .treatment_source_feasibility import run_treatment_source_feasibility
from .digest import build_digest, find_latest_digest_items, validate_digest_cadence, publish_reviewed_digest
from .historical_envelope import run_historical_reference_envelope
from .historical_analog import run_historical_analog_matrix
from .labour import run_labour_recruitment_pressure
from .materials import run_material_cost_screen, run_provincial_material_cost_screen
from .macro_controls import build_regional_macro_controls
from .model_review import (
    build_reference_cost_review_package,
    validate_reference_cost_review_verdict,
)
from .power_evidence import run_power_evidence_screen
from .power_planning import run_provincial_power_planning_contract
from .project_cost import run_project_reference_cost
from .public_projects import run_public_project_exposure
from .registry import load_registry
from .readiness import audit_program_readiness, require_release_ready
from .research_surface import build_research_surface_manifest
from .source_freshness import build_source_freshness_report
from .practical_route import build_practical_evidence_route
from .planning_benchmark import run_planning_benchmark, OUTPUT as PLANNING_BENCHMARK_OUTPUT
from .vintage_linkage import run_vintage_linkage, OUTPUT as VINTAGE_LINKAGE_OUTPUT
from .full_schedule_proxy import build_full_schedule_proxy
from .full_schedule_comparison import run_full_schedule_comparison, OUTPUT as FULL_SCHEDULE_COMPARISON_OUTPUT
from .historical_intake import register_snapshot, load_snapshots, select_snapshot, build_snapshot_readiness, OUTPUT as SNAPSHOT_READINESS_OUTPUT
from .pspe_lineage import build_pspe_method_lineage
from .retrieval import retrieve
from .schemas import ValidationError
from .scenario import run_scenario
from .scenario_suite import run_scenario_suite
from .power import run_power_overlay
from .release import build_publication_artifacts, build_release, verify_manifest


def main() -> None:
    utc_today = datetime.now(UTC).date().isoformat()
    parser = argparse.ArgumentParser(prog="aiio", description="AIIO Canada research pipeline")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-registry", help="validate the machine-readable source registry")

    fetch_parser = subparsers.add_parser("fetch", help="retrieve one registered public source")
    fetch_parser.add_argument("source_id")

    bcpi_parser = subparsers.add_parser("normalize-bcpi", help="normalize Alberta rows from a BCPI zip")
    bcpi_parser.add_argument("zip_path", type=Path)

    bcpi_canada_parser = subparsers.add_parser(
        "normalize-bcpi-provinces",
        help="normalize selected province-level BCPI material observations",
    )
    bcpi_canada_parser.add_argument("zip_path", type=Path)

    bcpi_reference_provinces_parser = subparsers.add_parser(
        "normalize-bcpi-reference-provinces",
        help="normalize BC, Ontario and Quebec public-building BCPI reference classes",
    )
    bcpi_reference_provinces_parser.add_argument("zip_path", type=Path)

    bcpi_reference_cmas_parser = subparsers.add_parser(
        "normalize-bcpi-reference-cmas",
        help="normalize Vancouver, Toronto and Montréal public-building BCPI reference classes",
    )
    bcpi_reference_cmas_parser.add_argument("zip_path", type=Path)

    labour_parser = subparsers.add_parser(
        "normalize-jvws",
        help="normalize Alberta job-vacancy and offered-wage rows for graph-relevant trades",
    )
    labour_parser.add_argument("zip_path", type=Path)

    labour_canada_parser = subparsers.add_parser(
        "normalize-jvws-canada",
        help="normalize provincial and territorial trade labour observations",
    )
    labour_canada_parser.add_argument("zip_path", type=Path)

    investment_parser = subparsers.add_parser(
        "normalize-investment-controls",
        help="normalize quarterly regional non-residential building-investment controls",
    )
    investment_parser.add_argument("zip_path", type=Path)

    macro_controls_parser = subparsers.add_parser(
        "run-regional-macro-controls",
        help="build the Canada-wide quarterly regional macro control panel",
    )
    macro_controls_parser.add_argument("cpi_zip_path", type=Path)
    macro_controls_parser.add_argument("population_zip_path", type=Path)
    macro_controls_parser.add_argument("earnings_zip_path", type=Path)
    macro_controls_parser.add_argument("housing_zip_path", type=Path)

    capex_treatment_parser = subparsers.add_parser(
        "normalize-capex-treatment-screen",
        help="build the fail-closed NAICS 51 construction-capex treatment feasibility screen",
    )
    capex_treatment_parser.add_argument("zip_path", type=Path)
    capex_treatment_parser.add_argument("output_csv_path", type=Path)
    capex_treatment_parser.add_argument("output_json_path", type=Path)

    ai_capex_ledger_parser = subparsers.add_parser(
        "run-ai-capex-announcement-ledger",
        help="build the fail-closed Alberta AI-capex announcement and treatment-candidate ledger",
    )
    ai_capex_ledger_parser.add_argument("input_csv_path", type=Path)
    ai_capex_ledger_parser.add_argument("output_json_path", type=Path)

    canadabuys_parser = subparsers.add_parser(
        "normalize-canadabuys-outcomes",
        help="build the fail-closed CanadaBuys construction procurement outcome-feasibility intake",
    )
    canadabuys_parser.add_argument("tender_path", type=Path)
    canadabuys_parser.add_argument("award_path", type=Path)
    canadabuys_parser.add_argument("contract_path", type=Path)

    subparsers.add_parser(
        "fetch-edmonton-permits",
        help="retrieve a field-minimized broad screen from the Edmonton building-permit API",
    )

    edmonton_permits_parser = subparsers.add_parser(
        "normalize-edmonton-permits",
        help="build the fail-closed Edmonton data-centre permit activity proxy",
    )
    edmonton_permits_parser.add_argument("raw_path", type=Path)

    subparsers.add_parser(
        "fetch-vancouver-permits",
        help="retrieve a field-minimized Vancouver data-centre permit screen",
    )
    vancouver_permits_parser = subparsers.add_parser(
        "normalize-vancouver-permits",
        help="build the fail-closed Vancouver data-centre permit activity proxy",
    )
    vancouver_permits_parser.add_argument("raw_path", type=Path)
    for city in ("toronto", "montreal"):
        subparsers.add_parser(f"fetch-{city}-permits", help=f"retrieve a field-minimized {city.title()} data-centre permit screen")
        city_parser = subparsers.add_parser(f"normalize-{city}-permits", help=f"build the fail-closed {city.title()} data-centre permit proxy")
        city_parser.add_argument("raw_path", type=Path)
    subparsers.add_parser("build-comparison-market-panel", help="align three-city permit proxies to CMA BCPI")
    subparsers.add_parser("run-comparison-market-association", help="run the non-causal three-city proxy association")

    audited_outcomes_parser = subparsers.add_parser(
        "normalize-audited-project-outcomes",
        help="build fail-closed named project outcome references from the Ontario audit",
    )
    audited_outcomes_parser.add_argument("manual_extract_path", type=Path)
    audited_outcomes_parser.add_argument("source_pdf_path", type=Path)

    quebec_revisions_parser = subparsers.add_parser(
        "normalize-quebec-authorized-revisions",
        help="build a fail-closed panel of Quebec authorized cost and completion revisions",
    )
    quebec_revisions_parser.add_argument("dashboard_csv_path", type=Path)
    quebec_revisions_parser.add_argument("dictionary_pdf_path", type=Path)

    quebec_vintages_parser = subparsers.add_parser(
        "fetch-quebec-milestone-vintages",
        help="retrieve a threshold-aware milestone sample from the official Quebec dashboard archive",
    )
    quebec_vintages_parser.add_argument("catalog_json_path", type=Path)

    quebec_longitudinal_parser = subparsers.add_parser(
        "normalize-quebec-milestone-vintages",
        help="build a fail-closed stable-ID longitudinal panel from Quebec milestone snapshots",
    )
    quebec_longitudinal_parser.add_argument("contract_path", type=Path)

    quebec_review_parser = subparsers.add_parser(
        "build-quebec-parser-review",
        help="build a deterministic, still-unauthorized independent parser-review package",
    )
    quebec_review_parser.add_argument("dashboard_csv_path", type=Path)

    quebec_full_archive_parser = subparsers.add_parser(
        "fetch-quebec-full-archive",
        help="hash-lock every official Quebec dashboard CSV date and any required paired-workbook fallback",
    )
    quebec_full_archive_parser.add_argument("catalog_json_path", type=Path)

    quebec_full_normalize_parser = subparsers.add_parser(
        "normalize-quebec-full-archive",
        help="build the complete-catalog stable-ID Quebec longitudinal selection panel",
    )
    quebec_full_normalize_parser.add_argument("contract_path", type=Path)

    subparsers.add_parser(
        "fetch-census-workforce",
        help="retrieve selected provincial and territorial detailed-trade employment cells",
    )

    census_workforce_parser = subparsers.add_parser(
        "normalize-census-workforce",
        help="normalize selected 2021 Census detailed-trade employment cells",
    )
    census_workforce_parser.add_argument("raw_path", type=Path)

    labour_pressure_parser = subparsers.add_parser(
        "run-labour-pressure",
        help="build the cross-vintage vacancy/workforce recruitment-pressure diagnostic",
    )
    labour_pressure_parser.add_argument("vacancy_path", type=Path)
    labour_pressure_parser.add_argument("workforce_path", type=Path)
    labour_pressure_parser.add_argument("output_path", type=Path)

    materials_parser = subparsers.add_parser(
        "run-material-screen",
        help="build the Alberta BCPI component-overlap material cost diagnostic",
    )
    materials_parser.add_argument("bcpi_path", type=Path)
    materials_parser.add_argument("output_json_path", type=Path)
    materials_parser.add_argument("output_csv_path", type=Path)

    provincial_materials_parser = subparsers.add_parser(
        "run-provincial-material-screen",
        help="build the common province-level BCPI material-cost screen",
    )
    provincial_materials_parser.add_argument("bcpi_path", type=Path)
    provincial_materials_parser.add_argument("output_json_path", type=Path)
    provincial_materials_parser.add_argument("output_csv_path", type=Path)

    public_projects_parser = subparsers.add_parser(
        "run-public-project-exposure",
        help="build the Alberta public-delivery asset overlap diagnostic",
    )
    public_projects_parser.add_argument("projects_path", type=Path)
    public_projects_parser.add_argument("output_json_path", type=Path)
    public_projects_parser.add_argument("output_csv_path", type=Path)
    public_projects_parser.add_argument("--window-start", type=int, default=2027)
    public_projects_parser.add_argument("--window-end", type=int, default=2036)

    cost_baseline_parser = subparsers.add_parser(
        "run-cost-baseline",
        help="build the held-out Alberta BCPI public-building reference baseline",
    )
    cost_baseline_parser.add_argument("bcpi_path", type=Path)
    cost_baseline_parser.add_argument("output_path", type=Path)

    historical_envelope_parser = subparsers.add_parser(
        "run-historical-cost-envelope",
        help="build the descriptive Alberta BCPI historical planning envelope",
    )
    historical_envelope_parser.add_argument("bcpi_path", type=Path)
    historical_envelope_parser.add_argument("output_path", type=Path)

    historical_analog_parser = subparsers.add_parser(
        "run-historical-project-analogs",
        help="build schedule-weighted historical BCPI analog stress-test matrices",
    )
    historical_analog_parser.add_argument("bcpi_path", type=Path)
    historical_analog_parser.add_argument("output_path", type=Path)

    provincial_cost_baseline_parser = subparsers.add_parser(
        "run-cost-baseline-provinces",
        help="run the held-out BC, Ontario and Quebec BCPI reference baseline",
    )
    provincial_cost_baseline_parser.add_argument("bcpi_path", type=Path)
    provincial_cost_baseline_parser.add_argument("output_path", type=Path)

    cma_cost_baseline_parser = subparsers.add_parser(
        "run-cost-baseline-cmas",
        help="run the held-out Vancouver, Toronto and Montréal BCPI reference baseline",
    )
    cma_cost_baseline_parser.add_argument("bcpi_path", type=Path)
    cma_cost_baseline_parser.add_argument("output_path", type=Path)

    province_linked_parser = subparsers.add_parser(
        "run-province-linked-reference-backcast",
        help="build and validate a CMA-linked pre-2017 provincial BCPI reference history",
    )
    province_linked_parser.add_argument("province_bcpi_path", type=Path)
    province_linked_parser.add_argument("cma_bcpi_path", type=Path)
    province_linked_parser.add_argument("output_csv_path", type=Path)
    province_linked_parser.add_argument("output_json_path", type=Path)

    province_linked_review_parser = subparsers.add_parser(
        "build-province-linked-review",
        help="build the deterministic independent-review packet for the province-linked BCPI bridge",
    )
    province_linked_review_parser.add_argument("output_json_path", type=Path)
    province_linked_review_parser.add_argument("output_prompt_path", type=Path)

    province_linked_verdict_parser = subparsers.add_parser(
        "validate-province-linked-verdict",
        help="validate a province-linked BCPI review verdict without mutating authorization",
    )
    province_linked_verdict_parser.add_argument("package_path", type=Path)
    province_linked_verdict_parser.add_argument("verdict_path", type=Path)

    project_cost_parser = subparsers.add_parser(
        "run-project-reference-cost",
        help="apply a validated BCPI reference path to an explicit expenditure profile",
    )
    project_cost_parser.add_argument("project_path", type=Path)
    project_cost_parser.add_argument("baseline_path", type=Path)
    project_cost_parser.add_argument("output_path", type=Path)

    reference_review_parser = subparsers.add_parser(
        "build-reference-cost-review",
        help="build the deterministic independent-review packet for the Alberta E1 baseline",
    )
    reference_review_parser.add_argument("output_json_path", type=Path)
    reference_review_parser.add_argument("output_prompt_path", type=Path)

    reference_verdict_parser = subparsers.add_parser(
        "validate-reference-cost-verdict",
        help="validate an independent Alberta E1 review verdict without authorizing publication",
    )
    reference_verdict_parser.add_argument("package_path", type=Path)
    reference_verdict_parser.add_argument("verdict_path", type=Path)

    power_evidence_parser = subparsers.add_parser(
        "run-power-evidence",
        help="build the observed AESO request, contract and transmission-boundary screen",
    )
    power_evidence_parser.add_argument("manual_extract_path", type=Path)
    power_evidence_parser.add_argument("source_pdf_path", type=Path)
    power_evidence_parser.add_argument("large_load_html_path", type=Path)
    power_evidence_parser.add_argument("interim_html_path", type=Path)
    power_evidence_parser.add_argument("output_json_path", type=Path)
    power_evidence_parser.add_argument("output_csv_path", type=Path)

    provincial_power_parser = subparsers.add_parser(
        "run-provincial-power-planning",
        help="validate the Ontario, B.C. and Quebec power-planning source contract",
    )
    provincial_power_parser.add_argument("extract_path", type=Path)
    provincial_power_parser.add_argument("output_json_path", type=Path)
    provincial_power_parser.add_argument("output_csv_path", type=Path)

    subparsers.add_parser(
        "fetch-major-projects",
        help="retrieve the Alberta Major Projects public full-dataset CSV export",
    )

    projects_parser = subparsers.add_parser(
        "normalize-major-projects",
        help="normalize Alberta Major Projects and classify AI-relevant records",
    )
    projects_parser.add_argument("csv_path", type=Path)
    projects_parser.add_argument("--as-of", required=True)

    provincial_projects_parser = subparsers.add_parser(
        "normalize-provincial-projects",
        help="normalize BC, Ontario and Quebec official project inventories",
    )
    provincial_projects_parser.add_argument("bc_geojson_path", type=Path)
    provincial_projects_parser.add_argument("ontario_csv_path", type=Path)
    provincial_projects_parser.add_argument("quebec_csv_path", type=Path)

    digest_parser = subparsers.add_parser("build-digest", help="render a reviewed weekly evidence digest")
    digest_parser.add_argument("items_path", type=Path)
    digest_parser.add_argument("--date", default=utc_today)

    subparsers.add_parser(
        "build-latest-digest",
        help="render the newest valid dated weekly evidence intake",
    )

    research_surface_parser = subparsers.add_parser(
        "build-research-surface-manifest",
        help="hash-lock every supplemental artifact imported by the evolving research website",
    )
    research_surface_parser.add_argument(
        "--output", type=Path, default=Path("public/data/research-surface.json")
    )

    source_freshness_parser = subparsers.add_parser(
        "build-source-freshness-report",
        help="evaluate every registered source against its declared publication cadence",
    )
    source_freshness_parser.add_argument("--as-of", default=utc_today)
    source_freshness_parser.add_argument(
        "--output", type=Path, default=Path("public/data/source-freshness.json")
    )

    practical_route_parser = subparsers.add_parser(
        "build-practical-evidence-route",
        help="build the reconstructed treatment, prospective project and narrow revision gate",
    )
    practical_route_parser.add_argument("--as-of", default=utc_today)

    subparsers.add_parser("run-planning-benchmark", help="run frozen retrospective Alberta planning backtests without authorizing estimates")
    vintage_parser = subparsers.add_parser("audit-vintage-linkage", help="audit archived vintages and draft project/permit linkage without changing models")
    vintage_parser.add_argument("--verify-raw", action="store_true", help="also verify local raw blobs and reviewed description hashes")
    subparsers.add_parser("build-full-schedule-proxy", help="build v0.2 with full-schedule allocation and retained out-of-window ledger")
    subparsers.add_parser("run-full-schedule-comparison", help="compare frozen baseline/project/permit/combined arms using proxy v0.2")
    intake_parser = subparsers.add_parser("register-historical-snapshot", help="register an immutable normalized snapshot after raw-file verification")
    intake_parser.add_argument("descriptor", type=Path)
    selection_parser = subparsers.add_parser("select-historical-snapshot", help="select one whole source snapshot available at an exact UTC-aware date")
    selection_parser.add_argument("source_id")
    selection_parser.add_argument("--as-of", required=True)
    subparsers.add_parser("build-historical-snapshot-readiness", help="build per-origin snapshot selections and an acquisition queue")

    canada_coverage_parser = subparsers.add_parser(
        "build-canada-cross-domain-coverage",
        help="build the fail-closed province and territory evidence coverage inventory",
    )
    canada_coverage_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/model-runs/canada_cross_domain_coverage_v0.1.json"),
    )

    pspe_lineage_parser = subparsers.add_parser(
        "build-pspe-method-lineage",
        help="hash-lock the available PSPE method notes and their bounded AIIO adaptations",
    )
    pspe_lineage_parser.add_argument(
        "contract_path", type=Path,
        nargs="?", default=Path("data/model/pspe_method_lineage_contract_v0.1.json")
    )
    pspe_lineage_parser.add_argument(
        "output_path", type=Path,
        nargs="?", default=Path("data/model-runs/pspe_method_lineage_v0.1.json")
    )

    digest_audit_parser = subparsers.add_parser(
        "audit-digest-cadence",
        help="fail when the latest dated digest intake is older than the weekly tolerance",
    )
    digest_audit_parser.add_argument("--as-of", default=utc_today)
    digest_audit_parser.add_argument("--max-age-days", type=int, default=8)

    readiness_parser = subparsers.add_parser(
        "audit-program-readiness",
        help="audit structural, decision-grade, review and publication gates",
    )
    readiness_parser.add_argument("--as-of", default=utc_today)
    readiness_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/model-runs/program_readiness_current.json"),
    )
    readiness_parser.add_argument("--require-release-ready", action="store_true")

    attribution_parser = subparsers.add_parser(
        "run-attribution-readiness",
        help="validate the E2 causal-panel contract and write a fail-closed readiness run",
    )
    attribution_parser.add_argument("contract_path", type=Path)
    attribution_parser.add_argument("output_path", type=Path)

    panel_preflight_parser = subparsers.add_parser(
        "run-panel-acquisition-preflight",
        help="validate the E2 evidence-receipt and field-acquisition contract without assembling an ineligible panel",
    )
    panel_preflight_parser.add_argument("attribution_contract_path", type=Path)
    panel_preflight_parser.add_argument("acquisition_contract_path", type=Path)
    panel_preflight_parser.add_argument("output_path", type=Path)

    treatment_sources_parser = subparsers.add_parser(
        "run-treatment-source-feasibility",
        help="screen public treatment-source candidates against the locked E2 authorizing gates",
    )
    treatment_sources_parser.add_argument("contract_path", type=Path)
    treatment_sources_parser.add_argument("output_path", type=Path)

    empirical_panel_parser = subparsers.add_parser(
        "build-empirical-covariate-panel",
        help="assemble the five-market E2 quarterly covariate panel while withholding ineligible estimation",
    )
    empirical_panel_parser.add_argument("attribution_contract_path", type=Path)
    empirical_panel_parser.add_argument("acquisition_contract_path", type=Path)
    empirical_panel_parser.add_argument("alberta_bcpi_path", type=Path)
    empirical_panel_parser.add_argument("comparison_bcpi_path", type=Path)
    empirical_panel_parser.add_argument("investment_path", type=Path)
    empirical_panel_parser.add_argument("macro_path", type=Path)
    empirical_panel_parser.add_argument("labour_path", type=Path)
    empirical_panel_parser.add_argument("proxy_treatment_path", type=Path)
    empirical_panel_parser.add_argument("output_csv_path", type=Path)
    empirical_panel_parser.add_argument("output_json_path", type=Path)

    empirical_estimation_parser = subparsers.add_parser(
        "run-empirical-estimation-gate",
        help="run the E2 estimator eligibility gate and withhold effects when the panel is ineligible",
    )
    empirical_estimation_parser.add_argument("contract_path", type=Path)
    empirical_estimation_parser.add_argument("panel_path", type=Path)
    empirical_estimation_parser.add_argument("panel_report_path", type=Path)
    empirical_estimation_parser.add_argument("output_path", type=Path)

    proxy_treatment_parser = subparsers.add_parser("build-proxy-treatment", help="reconstruct an uncertainty-bounded, non-authorizing Alberta AI-construction exposure proxy")
    proxy_treatment_parser.add_argument("projects_path", type=Path)
    proxy_treatment_parser.add_argument("permits_path", type=Path)
    proxy_treatment_parser.add_argument("project_report_path", type=Path)
    proxy_treatment_parser.add_argument("permit_report_path", type=Path)
    proxy_treatment_parser.add_argument("output_csv_path", type=Path)
    proxy_treatment_parser.add_argument("output_json_path", type=Path)
    proxy_association_parser = subparsers.add_parser("run-proxy-association", help="estimate a disclosed non-causal Alberta proxy association")
    proxy_association_parser.add_argument("panel_path", type=Path)
    proxy_association_parser.add_argument("panel_report_path", type=Path)
    proxy_association_parser.add_argument("output_path", type=Path)
    pspc_outcomes_parser = subparsers.add_parser("normalize-pspc-outcomes", help="profile PSPC public real-property delivery outcomes and preserve their linkage limits")
    pspc_outcomes_parser.add_argument("input_path", type=Path)
    pspc_outcomes_parser.add_argument("output_csv_path", type=Path)
    pspc_outcomes_parser.add_argument("output_json_path", type=Path)

    scenario_parser = subparsers.add_parser(
        "run-scenario", help="run a versioned graph scenario and write auditable JSON output"
    )
    scenario_parser.add_argument("graph_path", type=Path)
    scenario_parser.add_argument("scenario_path", type=Path)
    scenario_parser.add_argument("output_path", type=Path)

    scenario_suite_parser = subparsers.add_parser(
        "run-scenario-suite",
        help="run and compare the versioned Alberta scenario variants",
    )
    scenario_suite_parser.add_argument("contract_path", type=Path)
    scenario_suite_parser.add_argument("output_path", type=Path)

    power_parser = subparsers.add_parser(
        "run-power-overlay", help="run the independent MW-based power overlay"
    )
    power_parser.add_argument("input_path", type=Path)
    power_parser.add_argument("output_path", type=Path)

    release_parser = subparsers.add_parser(
        "build-release", help="build one immutable research release and public data bundle"
    )
    release_parser.add_argument("version")
    release_parser.add_argument("--created-at", required=True)

    verify_parser = subparsers.add_parser("verify-release", help="verify release and public hashes")
    verify_parser.add_argument("version")

    publication_parser = subparsers.add_parser(
        "build-publication-artifacts",
        help="publish the workbook and hash the complete user-facing artifact set",
    )
    publication_parser.add_argument("version")
    publication_parser.add_argument("workbook_path", type=Path)

    args = parser.parse_args()
    root = args.root.resolve()
    registry_path = root / "data" / "registry" / "sources.json"

    try:
        if args.command == "validate-registry":
            sources = load_registry(registry_path)
            print(json.dumps({"status": "passed", "source_count": len(sources)}))
        elif args.command == "fetch":
            sources = {source.source_id: source for source in load_registry(registry_path)}
            if args.source_id not in sources:
                raise ValidationError(f"unknown source_id: {args.source_id}")
            record = retrieve(sources[args.source_id], root / "data" / "raw")
            print(json.dumps(asdict(record), indent=2))
        elif args.command == "normalize-bcpi":
            observations = normalize_bcpi_alberta(
                args.zip_path.resolve(),
                root / "data" / "processed" / "bcpi_alberta.csv",
            )
            print(json.dumps({"status": "passed", "observation_count": len(observations)}))
        elif args.command == "normalize-bcpi-provinces":
            observations = normalize_bcpi_provinces(
                args.zip_path.resolve(),
                root / "data" / "processed" / "bcpi_material_provinces.csv",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "observation_count": len(observations),
                        "geography_count": len(
                            {item.geography_id for item in observations}
                        ),
                    }
                )
            )
        elif args.command == "normalize-bcpi-reference-provinces":
            observations = normalize_bcpi_reference_provinces(
                args.zip_path.resolve(),
                root
                / "data"
                / "processed"
                / "bcpi_reference_bc_on_qc.csv",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "observation_count": len(observations),
                        "geography_count": len(
                            {item.geography_id for item in observations}
                        ),
                    }
                )
            )
        elif args.command == "normalize-bcpi-reference-cmas":
            observations = normalize_bcpi_reference_cmas(
                args.zip_path.resolve(),
                root / "data" / "processed" / "bcpi_reference_van_tor_mtl.csv",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "observation_count": len(observations),
                        "geography_count": len(
                            {item.geography_id for item in observations}
                        ),
                    }
                )
            )
        elif args.command == "normalize-jvws":
            observations = normalize_jvws_alberta(
                args.zip_path.resolve(),
                root / "data" / "processed" / "labour_availability_alberta.csv",
            )
            print(json.dumps({"status": "passed", "observation_count": len(observations)}))
        elif args.command == "normalize-jvws-canada":
            observations = normalize_jvws_canada(
                args.zip_path.resolve(),
                root / "data" / "processed" / "labour_availability_canada.csv",
            )
            print(json.dumps({"status": "passed", "observation_count": len(observations)}))
        elif args.command == "normalize-investment-controls":
            observations = normalize_investment_controls(
                args.zip_path.resolve(),
                root / "data/processed/building_investment_controls_canada.csv",
                root
                / "data/model-runs/building_investment_controls_canada_v0.1.json",
                args.zip_path.resolve().with_suffix(
                    args.zip_path.resolve().suffix + ".manifest.json"
                ),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "observation_count": len(observations),
                        "geography_count": len(
                            {item["geography_id"] for item in observations}
                        ),
                    }
                )
            )
        elif args.command == "run-regional-macro-controls":
            report = build_regional_macro_controls(
                args.cpi_zip_path.resolve(),
                args.population_zip_path.resolve(),
                args.earnings_zip_path.resolve(),
                args.housing_zip_path.resolve(),
                root / "data/processed/building_investment_controls_canada.csv",
                root
                / "data/model-runs/building_investment_controls_canada_v0.1.json",
                root / "data/processed/regional_macro_controls_canada.csv",
                root
                / "data/model-runs/regional_macro_controls_canada_v0.1.json",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": report["model_id"],
                        "observation_count": report["observation_count"],
                        "series_count": report["series_count"],
                        "common_latest_period_end": report[
                            "common_latest_period_end"
                        ],
                    }
                )
            )
        elif args.command == "normalize-capex-treatment-screen":
            manifest_path = args.zip_path.resolve().with_suffix(
                args.zip_path.resolve().suffix + ".manifest.json"
            )
            output = normalize_information_sector_construction_capex(
                args.zip_path.resolve(),
                args.output_csv_path.resolve(),
                args.output_json_path.resolve(),
                retrieval_manifest_path=(
                    manifest_path if manifest_path.exists() else None
                ),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "observation_count": output["observation_count"],
                        "authorizing_treatment_present": output[
                            "treatment_requirement_assessment"
                        ]["authorizing_treatment_present"],
                    }
                )
            )
        elif args.command == "run-ai-capex-announcement-ledger":
            report = run_ai_capex_announcement_ledger(
                args.input_csv_path.resolve(),
                args.output_json_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "ledger_id": report["ledger_id"],
                        "record_count": report["record_count"],
                        "known_reported_estimated_cost_cad": report[
                            "coverage_summary"
                        ]["known_reported_estimated_cost_cad"],
                        "authorizing_treatment_present": report[
                            "treatment_requirement_assessment"
                        ]["authorizing_treatment_present"],
                    }
                )
            )
        elif args.command == "normalize-canadabuys-outcomes":
            input_paths = {
                CANADABUYS_TENDER_SOURCE_ID: args.tender_path.resolve(),
                CANADABUYS_AWARD_SOURCE_ID: args.award_path.resolve(),
                CANADABUYS_CONTRACT_SOURCE_ID: args.contract_path.resolve(),
            }
            report = normalize_canadabuys_outcome_intake(
                input_paths[CANADABUYS_TENDER_SOURCE_ID],
                input_paths[CANADABUYS_AWARD_SOURCE_ID],
                input_paths[CANADABUYS_CONTRACT_SOURCE_ID],
                root
                / "data"
                / "processed"
                / "canadabuys_construction_outcome_feasibility.csv",
                root
                / "data"
                / "model-runs"
                / "canadabuys_construction_outcome_feasibility_v0.1.json",
                retrieval_manifest_paths={
                    source_id: path.with_suffix(path.suffix + ".manifest.json")
                    for source_id, path in input_paths.items()
                },
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": report["model_id"],
                        "construction_linkage_count": report[
                            "construction_linkage_count"
                        ],
                        "public_project_cost_outcome_authorized": report[
                            "publication_boundary"
                        ]["public_project_cost_outcome_authorized"],
                    }
                )
            )
        elif args.command == "fetch-edmonton-permits":
            source_records = {
                source.source_id: source for source in load_registry(registry_path)
            }
            if EDMONTON_PERMIT_SOURCE_ID not in source_records:
                raise ValidationError("Edmonton permit source is missing from the registry")
            record = fetch_edmonton_permit_candidates(root / "data" / "raw")
            print(json.dumps(record, indent=2, sort_keys=True))
        elif args.command == "normalize-edmonton-permits":
            source_records = {
                source.source_id: source for source in load_registry(registry_path)
            }
            if EDMONTON_PERMIT_SOURCE_ID not in source_records:
                raise ValidationError("Edmonton permit source is missing from the registry")
            raw_path = args.raw_path.resolve()
            report = normalize_edmonton_permit_proxy(
                raw_path,
                root
                / "data"
                / "processed"
                / "edmonton_data_centre_permit_proxy.csv",
                root
                / "data"
                / "model-runs"
                / "edmonton_data_centre_permit_proxy_v0.1.json",
                source_as_of_date=source_records[
                    EDMONTON_PERMIT_SOURCE_ID
                ].as_of_date,
                retrieval_manifest_path=raw_path.with_suffix(
                    raw_path.suffix + ".manifest.json"
                ),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": report["model_id"],
                        "broad_screen_row_count": report["broad_screen_row_count"],
                        "data_centre_candidate_count": report[
                            "data_centre_candidate_count"
                        ],
                        "realized_ai_construction_treatment_authorized": report[
                            "publication_boundary"
                        ]["realized_ai_construction_treatment_authorized"],
                    }
                )
            )
        elif args.command == "fetch-vancouver-permits":
            source_records = {source.source_id: source for source in load_registry(registry_path)}
            if VANCOUVER_PERMIT_SOURCE_ID not in source_records:
                raise ValidationError("Vancouver permit source is missing from the registry")
            print(json.dumps(fetch_vancouver_permit_candidates(root / "data" / "raw"), indent=2, sort_keys=True))
        elif args.command == "normalize-vancouver-permits":
            source_records = {source.source_id: source for source in load_registry(registry_path)}
            if VANCOUVER_PERMIT_SOURCE_ID not in source_records:
                raise ValidationError("Vancouver permit source is missing from the registry")
            raw_path = args.raw_path.resolve()
            report = normalize_vancouver_permit_proxy(
                raw_path,
                root / "data" / "processed" / "vancouver_data_centre_permit_proxy.csv",
                root / "data" / "model-runs" / "vancouver_data_centre_permit_proxy_v0.1.json",
                source_as_of_date=source_records[VANCOUVER_PERMIT_SOURCE_ID].as_of_date,
                retrieval_manifest_path=raw_path.with_suffix(raw_path.suffix + ".manifest.json"),
            )
            print(json.dumps({"status": "passed", "model_id": report["model_id"], "data_centre_candidate_count": report["data_centre_candidate_count"], "realized_ai_construction_treatment_authorized": report["publication_boundary"]["realized_ai_construction_treatment_authorized"]}))
        elif args.command in {"fetch-toronto-permits", "fetch-montreal-permits"}:
            city = args.command.split("-")[1]
            source_id = TORONTO_PERMIT_SOURCE_ID if city == "toronto" else MONTREAL_PERMIT_SOURCE_ID
            source_records = {source.source_id: source for source in load_registry(registry_path)}
            if source_id not in source_records: raise ValidationError(f"{city.title()} permit source is missing from the registry")
            print(json.dumps(fetch_ckan_permit_candidates(city, root / "data" / "raw"), indent=2, sort_keys=True))
        elif args.command in {"normalize-toronto-permits", "normalize-montreal-permits"}:
            city = args.command.split("-")[1]
            source_id = TORONTO_PERMIT_SOURCE_ID if city == "toronto" else MONTREAL_PERMIT_SOURCE_ID
            source_records = {source.source_id: source for source in load_registry(registry_path)}
            if source_id not in source_records: raise ValidationError(f"{city.title()} permit source is missing from the registry")
            raw_path = args.raw_path.resolve()
            report = normalize_ckan_permit_proxy(city, raw_path, root / "data" / "processed" / f"{city}_data_centre_permit_proxy.csv", root / "data" / "model-runs" / f"{city}_data_centre_permit_proxy_v0.1.json", source_as_of_date=source_records[source_id].as_of_date, retrieval_manifest_path=raw_path.with_suffix(raw_path.suffix + ".manifest.json"))
            print(json.dumps({"status": "passed", "model_id": report["model_id"], "data_centre_candidate_count": report["data_centre_candidate_count"], "realized_ai_construction_treatment_authorized": False}))
        elif args.command == "build-comparison-market-panel":
            permit_paths = {city: root / "data" / "processed" / f"{city}_data_centre_permit_proxy.csv" for city in ("vancouver", "toronto", "montreal")}
            permit_reports = {city: root / "data" / "model-runs" / f"{city}_data_centre_permit_proxy_v0.1.json" for city in permit_paths}
            report = build_comparison_market_panel(root, root / "data" / "processed" / "bcpi_reference_van_tor_mtl.csv", permit_paths, permit_reports, root / "data" / "processed" / "comparison_market_permit_bcpi_panel_v0.1.csv", root / "data" / "model-runs" / "comparison_market_permit_bcpi_panel_v0.1.json")
            print(json.dumps({"status": "passed", "model_id": report["model_id"], "row_count": report["row_count"]}))
        elif args.command == "run-comparison-market-association":
            output = run_comparison_market_association(root / "data" / "processed" / "comparison_market_permit_bcpi_panel_v0.1.csv", root / "data" / "model-runs" / "comparison_market_permit_bcpi_panel_v0.1.json", root / "data" / "model-runs" / "comparison_market_proxy_association_v0.1.json")
            print(json.dumps({"status": "passed", "run_id": output["run_id"], "observation_count": output["result"]["observation_count"], "causal_interpretation_authorized": False}))
        elif args.command == "normalize-audited-project-outcomes":
            source_records = {
                source.source_id: source for source in load_registry(registry_path)
            }
            source_id = "OAGO_SELECTED_INFRASTRUCTURE_PROJECTS_2024"
            if source_id not in source_records:
                raise ValidationError(
                    "Ontario audited-outcome source is missing from the registry"
                )
            report = run_audited_project_outcomes(
                args.manual_extract_path.resolve(),
                args.source_pdf_path.resolve(),
                root
                / "data"
                / "model-runs"
                / "oago_audited_project_outcomes_v0.1.json",
                root
                / "data"
                / "processed"
                / "oago_audited_project_outcomes.csv",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": report["model_id"],
                        "named_completed_project_count": report[
                            "coverage_summary"
                        ]["named_completed_project_count"],
                        "public_project_cost_outcome_authorized": report[
                            "publication_boundary"
                        ]["public_project_cost_outcome_authorized"],
                        "public_project_schedule_outcome_authorized": report[
                            "publication_boundary"
                        ]["public_project_schedule_outcome_authorized"],
                    }
                )
            )
        elif args.command == "normalize-quebec-authorized-revisions":
            source_records = {
                source.source_id: source for source in load_registry(registry_path)
            }
            required_source_ids = (QUEBEC_SOURCE_ID, QUEBEC_DICTIONARY_SOURCE_ID)
            missing_source_ids = [
                source_id
                for source_id in required_source_ids
                if source_id not in source_records
            ]
            if missing_source_ids:
                raise ValidationError(
                    "Quebec revision sources are missing from the registry: "
                    + ", ".join(missing_source_ids)
                )
            report = run_quebec_authorized_revisions(
                args.dashboard_csv_path.resolve(),
                args.dictionary_pdf_path.resolve(),
                root
                / "data"
                / "model-runs"
                / "quebec_pqi_authorized_project_revisions_v0.1.json",
                root
                / "data"
                / "processed"
                / "quebec_pqi_authorized_project_revisions.csv",
                root
                / "data"
                / "processed"
                / "quebec_pqi_authorized_revision_events.csv",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": report["model_id"],
                        **report["coverage_summary"],
                        "authorized_revision_reference_panel_authorized": report[
                            "publication_boundary"
                        ]["authorized_revision_reference_panel_authorized"],
                    }
                )
            )
        elif args.command == "fetch-quebec-milestone-vintages":
            report = retrieve_milestone_resources(
                args.catalog_json_path.resolve(),
                root / "data" / "raw" / "quebec_pqi_project_dashboard_vintages",
                root
                / "data"
                / "model"
                / "quebec_pqi_milestone_vintage_contract_v0.1.json",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "contract_id": report["contract_id"],
                        "catalog_csv_resource_count": report[
                            "catalog_csv_resource_count"
                        ],
                        "selected_vintage_count": report["selected_vintage_count"],
                        "catalog_start_date": report["catalog_start_date"],
                        "catalog_end_date": report["catalog_end_date"],
                        "longitudinal_outcome_panel_authorized": report[
                            "publication_boundary"
                        ]["longitudinal_outcome_panel_authorized"],
                    }
                )
            )
        elif args.command == "normalize-quebec-milestone-vintages":
            report = run_quebec_milestone_longitudinal(
                args.contract_path.resolve(),
                root / "data" / "raw" / "quebec_pqi_project_dashboard_vintages",
                root
                / "data"
                / "model-runs"
                / "quebec_pqi_milestone_longitudinal_v0.1.json",
                root
                / "data"
                / "processed"
                / "quebec_pqi_milestone_project_vintages.csv",
                root
                / "data"
                / "processed"
                / "quebec_pqi_milestone_project_lifecycles.csv",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": report["model_id"],
                        "vintage_count": report["vintage_count"],
                        "snapshot_observation_count": report[
                            "snapshot_observation_count"
                        ],
                        "unique_project_count": report["unique_project_count"],
                        "present_in_latest_project_count": report[
                            "present_in_latest_project_count"
                        ],
                        "complete_longitudinal_panel_authorized": report[
                            "publication_boundary"
                        ]["complete_longitudinal_panel_authorized"],
                    }
                )
            )
        elif args.command == "build-quebec-parser-review":
            report = build_quebec_parser_review_package(
                args.dashboard_csv_path.resolve(),
                root
                / "data"
                / "model-runs"
                / "quebec_pqi_authorized_project_revisions_v0.1.json",
                root
                / "data"
                / "processed"
                / "quebec_pqi_authorized_project_revisions.csv",
                root
                / "data"
                / "processed"
                / "quebec_pqi_authorized_revision_events.csv",
                root
                / "data"
                / "model-runs"
                / "quebec_pqi_milestone_longitudinal_v0.1.json",
                root
                / "data"
                / "processed"
                / "quebec_pqi_milestone_project_lifecycles.csv",
                root / "data" / "reviews" / "quebec_pqi_parser_review_sample_v0.1.csv",
                root
                / "data"
                / "model-runs"
                / "quebec_pqi_parser_review_package_v0.1.json",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "package_id": report["package_id"],
                        "review_status": report["review_status"],
                        "sample_project_count": report["sample_project_count"],
                        "source_project_count": report["source_project_count"],
                        "independent_parser_review_complete": report[
                            "publication_boundary"
                        ]["independent_parser_review_complete"],
                    }
                )
            )
        elif args.command == "fetch-quebec-full-archive":
            report = retrieve_full_archive_resources(
                args.catalog_json_path.resolve(),
                root
                / "data"
                / "model"
                / "quebec_pqi_milestone_vintage_contract_v0.1.json",
                root / "data" / "raw" / "quebec_pqi_project_dashboard_full_archive",
                root
                / "data"
                / "model"
                / "quebec_pqi_full_archive_contract_v0.1.json",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "contract_id": report["contract_id"],
                        "snapshot_date_count": report["snapshot_date_count"],
                        "direct_csv_snapshot_count": report[
                            "direct_csv_snapshot_count"
                        ],
                        "paired_xlsx_fallback_count": report[
                            "paired_xlsx_fallback_count"
                        ],
                        "project_exit_outcome_authorized": report[
                            "publication_boundary"
                        ]["project_exit_outcome_authorized"],
                    }
                )
            )
        elif args.command == "normalize-quebec-full-archive":
            report = run_quebec_full_archive_longitudinal(
                args.contract_path.resolve(),
                root,
                root
                / "data"
                / "model-runs"
                / "quebec_pqi_milestone_longitudinal_v0.1.json",
                root
                / "data"
                / "model-runs"
                / "quebec_pqi_full_archive_longitudinal_v0.1.json",
                root
                / "data"
                / "processed"
                / "quebec_pqi_full_archive_project_vintages.csv",
                root
                / "data"
                / "processed"
                / "quebec_pqi_full_archive_project_lifecycles.csv",
                root
                / "data"
                / "processed"
                / "quebec_pqi_full_archive_transitions.csv",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": report["model_id"],
                        "snapshot_date_count": report["snapshot_date_count"],
                        "snapshot_observation_count": report[
                            "snapshot_observation_count"
                        ],
                        "unique_project_count": report["unique_project_count"],
                        "additional_unique_projects_observed": report[
                            "milestone_comparison"
                        ]["additional_unique_projects_observed"],
                        "project_exit_outcome_authorized": report[
                            "publication_boundary"
                        ]["project_exit_outcome_authorized"],
                    }
                )
            )
        elif args.command == "fetch-major-projects":
            record = fetch_major_projects(root / "data" / "raw")
            print(json.dumps(asdict(record), indent=2))
        elif args.command == "normalize-major-projects":
            project_count, ai_count = normalize_major_projects(
                args.csv_path.resolve(),
                root / "data" / "processed" / "alberta_major_projects.csv",
                root / "data" / "processed" / "alberta_ai_projects.csv",
                args.as_of,
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "project_count": project_count,
                        "ai_relevant_count": ai_count,
                    }
                )
            )
        elif args.command == "normalize-provincial-projects":
            source_records = {
                source.source_id: source for source in load_registry(registry_path)
            }
            source_ids = (BC_SOURCE_ID, ONTARIO_SOURCE_ID, QUEBEC_SOURCE_ID)
            missing = [source_id for source_id in source_ids if source_id not in source_records]
            if missing:
                raise ValidationError(
                    f"provincial project sources missing from registry: {missing}"
                )
            report = normalize_provincial_projects(
                args.bc_geojson_path.resolve(),
                args.ontario_csv_path.resolve(),
                args.quebec_csv_path.resolve(),
                root / "data" / "processed" / "public_projects_bc_on_qc.csv",
                root
                / "data"
                / "model-runs"
                / "public_projects_bc_on_qc_intake_v0.1.json",
                source_as_of_dates={
                    source_id: source_records[source_id].as_of_date
                    for source_id in source_ids
                },
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "transformation_id": report["transformation_id"],
                        "record_count": report["record_count"],
                        "geography_count": report["geography_count"],
                    }
                )
            )
        elif args.command == "fetch-census-workforce":
            record = fetch_census_trade_employment(root / "data" / "raw")
            print(json.dumps(asdict(record), indent=2))
        elif args.command == "normalize-census-workforce":
            observations = normalize_census_trade_employment(
                args.raw_path.resolve(),
                root / "data" / "processed" / "labour_workforce_stock_canada.csv",
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "observation_count": len(observations),
                        "output": "data/processed/labour_workforce_stock_canada.csv",
                    }
                )
            )
        elif args.command == "run-labour-pressure":
            output = run_labour_recruitment_pressure(
                args.vacancy_path.resolve(),
                args.workforce_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "occupation_diagnostic_count": len(
                            output["occupation_diagnostics"]
                        ),
                        "trade_diagnostic_count": len(output["trade_diagnostics"]),
                    }
                )
            )
        elif args.command == "run-material-screen":
            output = run_material_cost_screen(
                args.bcpi_path.resolve(),
                args.output_json_path.resolve(),
                args.output_csv_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "observation_count": output["observation_count"],
                    }
                )
            )
        elif args.command == "run-provincial-material-screen":
            output = run_provincial_material_cost_screen(
                args.bcpi_path.resolve(),
                args.output_json_path.resolve(),
                args.output_csv_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "observation_count": output["observation_count"],
                        "geography_count": len(output["geography_scope"]),
                    }
                )
            )
        elif args.command == "run-public-project-exposure":
            output = run_public_project_exposure(
                args.projects_path.resolve(),
                args.output_json_path.resolve(),
                args.output_csv_path.resolve(),
                window_start=args.window_start,
                window_end=args.window_end,
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "screened_project_count": output["screened_project_count"],
                    }
                )
            )
        elif args.command == "run-cost-baseline":
            output = run_reference_class_baseline(
                args.bcpi_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "release_state": output["release_state"],
                        "reference_class_count": len(
                            output["reference_class_results"]
                        ),
                    }
                )
            )
        elif args.command == "run-cost-baseline-provinces":
            output = run_reference_class_baseline(
                args.bcpi_path.resolve(),
                args.output_path.resolve(),
                geography_labels=PROVINCIAL_REFERENCE_GEOGRAPHY_LABELS,
                model_id=PROVINCIAL_REFERENCE_MODEL_ID,
                limitations=PROVINCIAL_REFERENCE_LIMITATIONS,
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "release_state": output["release_state"],
                        "reference_class_count": len(
                            output["reference_class_results"]
                        ),
                    }
                )
            )
        elif args.command == "run-cost-baseline-cmas":
            output = run_cma_reference_class_baseline(
                args.bcpi_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "release_state": output["release_state"],
                        "reference_class_count": len(
                            output["reference_class_results"]
                        ),
                    }
                )
            )
        elif args.command == "run-province-linked-reference-backcast":
            output = run_province_linked_reference_backcast(
                args.province_bcpi_path.resolve(),
                args.cma_bcpi_path.resolve(),
                args.output_csv_path.resolve(),
                args.output_json_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "release_state": output["release_state"],
                        "reference_class_count": len(
                            output["reference_class_results"]
                        ),
                    }
                )
            )
        elif args.command == "build-province-linked-review":
            output = build_province_linked_review_package(
                root,
                args.output_json_path.resolve(),
                args.output_prompt_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "package_id": output["package_id"],
                        "review_status": output["review_status"],
                        "criterion_count": len(output["required_criteria"]),
                    }
                )
            )
        elif args.command == "validate-province-linked-verdict":
            output = validate_province_linked_review_verdict(
                args.package_path.resolve(), args.verdict_path.resolve()
            )
            print(json.dumps(output))
        elif args.command == "run-historical-cost-envelope":
            output = run_historical_reference_envelope(
                args.bcpi_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "reference_class_count": len(
                            output["reference_class_results"]
                        ),
                        "historical_summary_authorized": output[
                            "publication_authorization"
                        ]["historical_summary_authorized"],
                    }
                )
            )
        elif args.command == "run-historical-project-analogs":
            output = run_historical_analog_matrix(
                args.bcpi_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "reference_class_count": len(
                            output["reference_class_results"]
                        ),
                        "grid_result_count": sum(
                            len(item["grid"])
                            for item in output["reference_class_results"]
                        ),
                        "historical_analog_stress_test_authorized": output[
                            "publication_authorization"
                        ]["historical_analog_stress_test_authorized"],
                    }
                )
            )
        elif args.command == "run-project-reference-cost":
            output = run_project_reference_cost(
                args.project_path.resolve(),
                args.baseline_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": output["status"],
                        "model_id": output["model_id"],
                        "project_id": output["project_id"],
                    }
                )
            )
        elif args.command == "build-reference-cost-review":
            output = build_reference_cost_review_package(
                root,
                args.output_json_path.resolve(),
                args.output_prompt_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "package_id": output["package_id"],
                        "review_status": output["review_status"],
                        "criterion_count": len(output["required_criteria"]),
                    }
                )
            )
        elif args.command == "validate-reference-cost-verdict":
            output = validate_reference_cost_review_verdict(
                args.package_path.resolve(),
                args.verdict_path.resolve(),
            )
            print(json.dumps(output))
        elif args.command == "run-power-evidence":
            output = run_power_evidence_screen(
                args.manual_extract_path.resolve(),
                args.source_pdf_path.resolve(),
                args.large_load_html_path.resolve(),
                args.interim_html_path.resolve(),
                args.output_json_path.resolve(),
                args.output_csv_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "metric_count": len(output["metrics"]),
                    }
                )
            )
        elif args.command == "run-provincial-power-planning":
            output = run_provincial_power_planning_contract(
                args.extract_path.resolve(),
                root,
                args.output_json_path.resolve(),
                args.output_csv_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "model_id": output["model_id"],
                        "metric_count": output["metric_count"],
                        "publication_authorized": output["publication_boundary"][
                            "provincial_power_profile_authorized"
                        ],
                    }
                )
            )
        elif args.command == "build-digest":
            edition_date = date.fromisoformat(args.date)
            output = root / "data" / "digests" / f"{edition_date.isoformat()}.md"
            manifest = build_digest(
                args.items_path.resolve(),
                output,
                edition_date,
                source_registry_path=root / "data" / "registry" / "sources.json",
                approval_receipt_path=output.with_suffix('.approval.json'),
            )
            publish_reviewed_digest(root, args.items_path.resolve(), manifest, output.with_suffix('.approval.json'))
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "output": str(output),
                        "manifest": str(output.with_suffix(".manifest.json")),
                        "digest_id": manifest["digest_id"],
                    }
                )
            )
        elif args.command == "build-latest-digest":
            edition_date, items_path = find_latest_digest_items(
                root / "data" / "digests" / "items"
            )
            output = root / "data" / "digests" / f"{edition_date.isoformat()}.md"
            manifest = build_digest(
                items_path.resolve(),
                output,
                edition_date,
                source_registry_path=root / "data" / "registry" / "sources.json",
                approval_receipt_path=output.with_suffix('.approval.json'),
            )
            publish_reviewed_digest(root, items_path.resolve(), manifest, output.with_suffix('.approval.json'))
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "items": str(items_path),
                        "output": str(output),
                        "manifest": str(output.with_suffix(".manifest.json")),
                        "digest_id": manifest["digest_id"],
                    }
                )
            )
        elif args.command == "build-research-surface-manifest":
            output_path = (
                args.output if args.output.is_absolute() else root / args.output
            ).resolve()
            manifest = build_research_surface_manifest(root, output_path)
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "output": str(output_path),
                        "surface_id": manifest["surface_id"],
                        "artifact_count": manifest["artifact_count"],
                    }
                )
            )
        elif args.command == "build-source-freshness-report":
            output_path = (args.output if args.output.is_absolute() else root / args.output).resolve()
            report = build_source_freshness_report(
                root / "data/registry/sources.json", args.as_of, output_path
            )
            print(json.dumps({"status": report["status"], "output": str(output_path), "source_count": report["source_count"], "stale_count": report["stale_count"]}))
        elif args.command == "register-historical-snapshot":
            descriptor = args.descriptor if args.descriptor.is_absolute() else root / args.descriptor
            print(json.dumps(register_snapshot(root, descriptor)))
        elif args.command == "select-historical-snapshot":
            print(json.dumps(select_snapshot(load_snapshots(root), args.source_id, args.as_of)))
        elif args.command == "build-historical-snapshot-readiness":
            report = build_snapshot_readiness(root, root / SNAPSHOT_READINESS_OUTPUT)
            print(json.dumps({"status": report["status"], "snapshot_count": report["snapshot_count"], "complete_source_snapshot_origins": report["complete_source_snapshot_origins"], "missing_source_origin_pairs": report["missing_source_origin_pairs"], "output": SNAPSHOT_READINESS_OUTPUT}))
        elif args.command == "build-full-schedule-proxy":
            report, _, _ = build_full_schedule_proxy(root, root)
            print(json.dumps({"status": report["status"], "project_allocation_totals_cad": report["project_allocation_totals_cad"], "output_manifest": report["output_manifest"]}))
        elif args.command == "run-full-schedule-comparison":
            report = run_full_schedule_comparison(root, root / FULL_SCHEDULE_COMPARISON_OUTPUT)
            print(json.dumps({"status": report["status"], "arms": {name: value["metrics"] for name, value in report["arms"].items()}, "historical_comparison": report["historical_comparison"]}))
        elif args.command == "audit-vintage-linkage":
            report, verification = run_vintage_linkage(root, root / VINTAGE_LINKAGE_OUTPUT, args.verify_raw)
            print(json.dumps({"status": report["status"], "permit_review_count": len(report["included_permit_review"]), "raw_verification": verification, "output": VINTAGE_LINKAGE_OUTPUT}))
        elif args.command == "run-planning-benchmark":
            report = run_planning_benchmark(root, root / PLANNING_BENCHMARK_OUTPUT)
            print(json.dumps({"status": report["status"], "metrics": report["metrics"], "point_error_checks": report["point_error_checks"], "output": PLANNING_BENCHMARK_OUTPUT}))
        elif args.command == "build-practical-evidence-route":
            report = build_practical_evidence_route(
                root,
                args.as_of,
                root / "data/processed/ai_construction_proxy_alberta_v0.1.csv",
                root / "data/processed/public_projects_bc_on_qc.csv",
                root / "data/processed/quebec_pqi_authorized_revision_events.csv",
                root / "data/processed/public_project_prospective_snapshot_current.csv",
                root / "data/model-runs/practical_evidence_route_current.json",
            )
            print(json.dumps({"status": report["status"], "as_of_date": report["as_of_date"], "gate_evaluation": report["gate_evaluation"]}))
        elif args.command == "build-canada-cross-domain-coverage":
            output_path = (
                args.output if args.output.is_absolute() else root / args.output
            ).resolve()
            report = build_canada_cross_domain_coverage(root, output_path)
            print(json.dumps({
                "status": "passed",
                "output": str(output_path),
                "model_id": report["model_id"],
                "geography_count": report["geography_count"],
                "domain_count": report["domain_count"],
                "matrix_cell_count": report["matrix_cell_count"],
            }))
        elif args.command == "build-pspe-method-lineage":
            contract_path = (
                args.contract_path if args.contract_path.is_absolute() else root / args.contract_path
            ).resolve()
            output_path = (
                args.output_path if args.output_path.is_absolute() else root / args.output_path
            ).resolve()
            report = build_pspe_method_lineage(root, contract_path, output_path)
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "output": str(output_path),
                        "model_id": report["model_id"],
                        "mapping_count": report["mapping_count"],
                        "lineage_status": report["lineage_status"],
                    }
                )
            )
        elif args.command == "audit-digest-cadence":
            result = validate_digest_cadence(
                root / "data" / "digests" / "items",
                as_of_date=date.fromisoformat(args.as_of),
                max_age_days=args.max_age_days,
            )
            print(json.dumps(result))
        elif args.command == "audit-program-readiness":
            output_path = (
                args.output if args.output.is_absolute() else root / args.output
            ).resolve()
            result = audit_program_readiness(
                root,
                as_of_date=date.fromisoformat(args.as_of),
                output_path=output_path,
            )
            if result["status_counts"]["fail"]:
                raise ValidationError(
                    "program readiness audit found structural failures; see "
                    + str(output_path)
                )
            if args.require_release_ready:
                require_release_ready(result)
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "output": str(output_path),
                        "structural_integrity": result["structural_integrity"],
                        "decision_grade_ready": result["decision_grade_ready"],
                        "release_ready": result["release_ready"],
                        "status_counts": result["status_counts"],
                    }
                )
            )
        elif args.command == "run-attribution-readiness":
            output = build_attribution_readiness(
                args.contract_path.resolve(),
                registry_path,
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "run_id": output["run_id"],
                        "analysis_status": output["analysis_status"],
                        "ai_attributable_increment_authorized": output[
                            "publication_authorization"
                        ]["ai_attributable_increment_authorized"],
                    }
                )
            )
        elif args.command == "run-panel-acquisition-preflight":
            output = run_panel_acquisition_preflight(
                root,
                args.attribution_contract_path.resolve(),
                args.acquisition_contract_path.resolve(),
                registry_path,
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "preflight_id": output["preflight_id"],
                        "candidate_region_count": output["candidate_scope"][
                            "region_count"
                        ],
                        "required_field_instance_count": output[
                            "field_gap_summary"
                        ]["required_field_instance_count"],
                        "assembled_panel_row_count": output[
                            "current_eligibility"
                        ]["assembled_panel_row_count"],
                        "effect_estimation_authorized": output[
                            "publication_boundary"
                        ]["effect_estimation_authorized"],
                    }
                )
            )
        elif args.command == "build-empirical-covariate-panel":
            output = build_empirical_covariate_panel(
                root,
                args.attribution_contract_path.resolve(), args.acquisition_contract_path.resolve(),
                args.alberta_bcpi_path.resolve(), args.comparison_bcpi_path.resolve(),
                args.investment_path.resolve(), args.macro_path.resolve(), args.labour_path.resolve(), args.proxy_treatment_path.resolve(),
                args.output_csv_path.resolve(), args.output_json_path.resolve(),
            )
            print(json.dumps({"status": "passed", "panel_id": output["panel_id"], "row_count": output["row_count"], "effect_estimation_authorized": output["publication_boundary"]["effect_estimation_authorized"]}))
        elif args.command == "run-empirical-estimation-gate":
            output = run_empirical_estimation_gate(root, args.contract_path.resolve(), args.panel_path.resolve(), args.panel_report_path.resolve(), args.output_path.resolve())
            print(json.dumps({"status": "passed", "run_id": output["run_id"], "analysis_status": output["status"], "effect_publication_authorized": output["publication_boundary"]["effect_publication_authorized"]}))
        elif args.command == "build-proxy-treatment":
            output = build_reconstructed_treatment_proxy(root, args.projects_path.resolve(), args.permits_path.resolve(), args.project_report_path.resolve(), args.permit_report_path.resolve(), args.output_csv_path.resolve(), args.output_json_path.resolve())
            print(json.dumps({"status": "passed", "model_id": output["model_id"], "row_count": output["row_count"], "causal_effect_authorized": output["publication_boundary"]["causal_effect_authorized"]}))
        elif args.command == "run-proxy-association":
            output = run_proxy_association(args.panel_path.resolve(), args.panel_report_path.resolve(), args.output_path.resolve())
            print(json.dumps({"status": "passed", "run_id": output["run_id"], "result_count": len(output["results"]), "causal_interpretation_authorized": output["publication_boundary"]["causal_interpretation_authorized"]}))
        elif args.command == "normalize-pspc-outcomes":
            output = normalize_pspc_outcomes(args.input_path.resolve(), args.output_csv_path.resolve(), args.output_json_path.resolve())
            print(json.dumps({"status": "passed", "model_id": output["model_id"], "record_count": output["record_count"], "project_outcome_authorized": output["publication_boundary"]["project_outcome_authorized"]}))
        elif args.command == "run-treatment-source-feasibility":
            output = run_treatment_source_feasibility(
                args.contract_path.resolve(),
                registry_path,
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "feasibility_id": output["feasibility_id"],
                        "candidate_count": output["candidate_count"],
                        "authorizing_candidate_count": output[
                            "authorizing_candidate_count"
                        ],
                        "treatment_authorized": output["publication_boundary"][
                            "treatment_authorized"
                        ],
                    }
                )
            )
        elif args.command == "run-scenario":
            output = run_scenario(
                args.graph_path.resolve(),
                args.scenario_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "scenario_id": output["scenario_id"],
                        "pressure_node_count": len(output["pressure_peaks"]),
                    }
                )
            )
        elif args.command == "run-scenario-suite":
            output = run_scenario_suite(
                root,
                args.contract_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "suite_id": output["suite_id"],
                        "variant_count": output["variant_count"],
                        "comparison_node_count": len(output["comparison_matrix"]),
                    }
                )
            )
        elif args.command == "run-power-overlay":
            output = run_power_overlay(
                args.input_path.resolve(),
                args.output_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "overlay_id": output["overlay_id"],
                        "case_count": len(output["cases"]),
                    }
                )
            )
        elif args.command == "build-release":
            manifest = build_release(root, args.version, args.created_at)
            print(json.dumps({"status": "passed", "release_id": manifest["release_id"]}))
        elif args.command == "verify-release":
            verify_manifest(root, args.version)
            print(json.dumps({"status": "passed", "version": args.version}))
        elif args.command == "build-publication-artifacts":
            artifacts = build_publication_artifacts(
                root,
                args.version,
                args.workbook_path.resolve(),
            )
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "version": args.version,
                        "artifact_count": len(artifacts["artifacts"]),
                    }
                )
            )
    except ValidationError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
