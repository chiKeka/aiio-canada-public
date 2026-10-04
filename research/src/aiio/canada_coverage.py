from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .schemas import ValidationError


MODEL_ID = "AIIO_CANADA_CROSS_DOMAIN_COVERAGE_0_1"
GEOGRAPHIES = {
    "PR_10": "Newfoundland and Labrador", "PR_11": "Prince Edward Island",
    "PR_12": "Nova Scotia", "PR_13": "New Brunswick", "PR_24": "Quebec",
    "PR_35": "Ontario", "PR_46": "Manitoba", "PR_47": "Saskatchewan",
    "PR_48": "Alberta", "PR_59": "British Columbia", "PR_60": "Yukon",
    "PR_61": "Northwest Territories", "PR_62": "Nunavut",
}
DOMAINS = (
    "labour", "materials", "building_investment", "regional_macro",
    "public_projects", "power_planning", "information_sector_capex",
)


def _sha(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_canada_cross_domain_coverage(
    root: Path, output_path: Path | None = None
) -> dict[str, Any]:
    root = root.resolve()
    inputs = {
        "labour_availability": root / "data/processed/labour_availability_canada.csv",
        "workforce_stock": root / "data/processed/labour_workforce_stock_canada.csv",
        "materials": root / "data/model-runs/bcpi_material_cost_screen_provinces_v0.1.json",
        "investment": root / "data/model-runs/building_investment_controls_canada_v0.1.json",
        "macro": root / "data/model-runs/regional_macro_controls_canada_v0.1.json",
        "provincial_projects": root / "data/processed/public_projects_bc_on_qc.csv",
        "alberta_projects": root / "data/processed/public_project_exposure_alberta.csv",
        "provincial_power": root / "data/model-runs/provincial_power_planning_contract_v0.1.json",
        "alberta_power": root / "data/model-runs/power_evidence_alberta_v0.1.json",
        "capex": root / "data/model-runs/information_sector_construction_capex_screen_v0.1.json",
    }
    missing = [str(path.relative_to(root)) for path in inputs.values() if not path.is_file()]
    if missing:
        raise ValidationError("Canada coverage inputs are missing: " + ", ".join(missing))

    labour_rows = _csv_rows(inputs["labour_availability"])
    workforce_rows = _csv_rows(inputs["workforce_stock"])
    materials = _json(inputs["materials"])
    investment = _json(inputs["investment"])
    macro = _json(inputs["macro"])
    provincial_projects = _csv_rows(inputs["provincial_projects"])
    alberta_projects = _csv_rows(inputs["alberta_projects"])
    power = _json(inputs["provincial_power"])
    capex = _json(inputs["capex"])

    labour_counts = Counter(row["geography_id"] for row in labour_rows)
    labour_published = Counter(row["geography_id"] for row in labour_rows if row["value"])
    workforce_counts = Counter(row["geography_id"] for row in workforce_rows)
    material_scope = set(materials["geography_scope"])
    investment_scope = {item for item in investment["geography_ids"] if item.startswith("PR_")}
    macro_counts: Counter[str] = Counter()
    for coverage in macro["metric_coverage"].values():
        macro_counts.update(coverage["available_geography_ids"])
    project_counts = Counter(row["geography_id"] for row in provincial_projects)
    project_counts["PR_48"] = len(alberta_projects)
    power_counts = Counter({key: value["metric_count"] for key, value in power["coverage"].items()})
    power_counts["PR_48"] = len(_json(inputs["alberta_power"])["metrics"])
    capex_summaries = {item["geography_id"]: item for item in capex["geography_summaries"]}

    rows = []
    domain_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for geography_id, label in GEOGRAPHIES.items():
        labour_total = labour_counts[geography_id]
        labour_status = "available_with_missingness" if labour_total and labour_published[geography_id] < labour_total else "available"
        cells = {
            "labour": {"status": labour_status, "record_count": labour_total + workforce_counts[geography_id], "role": "observed_context"},
            "materials": {"status": "available" if geography_id in material_scope else "not_available", "record_count": sum(1 for item in materials["observations"] if item["geography_id"] == geography_id), "role": "observed_proxy"},
            "building_investment": {"status": "available" if geography_id in investment_scope else "not_available", "record_count": investment["structure_count"] * investment["investment_basis_count"] * investment["quarter_count"] if geography_id in investment_scope else 0, "role": "observed_control"},
            "regional_macro": {"status": "available" if macro_counts[geography_id] == macro["metric_count"] else ("available_with_missingness" if macro_counts[geography_id] else "not_available"), "record_count": macro_counts[geography_id], "role": "observed_control_series"},
            "public_projects": {"status": "available" if project_counts[geography_id] else "not_available", "record_count": project_counts[geography_id], "role": "source_specific_inventory"},
            "power_planning": {"status": "available" if power_counts[geography_id] else "not_available", "record_count": power_counts[geography_id], "role": "non_comparable_physical_context"},
            "information_sector_capex": {"status": "available_with_missingness" if capex_summaries.get(geography_id, {}).get("withheld_or_unavailable_count", 0) else ("available" if geography_id in capex_summaries else "not_available"), "record_count": capex_summaries.get(geography_id, {}).get("published_value_count", 0), "role": "broad_sector_proxy"},
        }
        for domain, cell in cells.items():
            domain_status_counts[domain][cell["status"]] += 1
        rows.append({"geography_id": geography_id, "geography_label": label, "domains": cells})

    report = {
        "schema_version": "1.0.0", "model_id": MODEL_ID,
        "geography_count": len(rows), "domain_count": len(DOMAINS),
        "matrix_cell_count": len(rows) * len(DOMAINS), "domains": list(DOMAINS),
        "input_manifest": {key: {"path": str(path.relative_to(root)), "sha256": _sha(path)} for key, path in inputs.items()},
        "domain_status_counts": {domain: dict(sorted(counts.items())) for domain, counts in domain_status_counts.items()},
        "geographies": rows,
        "publication_boundary": {
            "cross_province_comparison_authorized": False,
            "province_model_calibration_authorized": False,
            "missingness_imputed": False,
            "ai_attributable_effect_authorized": False,
            "status": "coverage_inventory_only",
            "reason": "Availability does not establish common definitions, comparable measurement, treatment identification or province-specific model calibration."
        },
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def validate_canada_cross_domain_coverage(
    root: Path, report_path: Path
) -> dict[str, Any]:
    committed = _json(report_path)
    expected = build_canada_cross_domain_coverage(root)
    if committed != expected:
        raise ValidationError(
            "Canada cross-domain coverage artifact is stale or does not reproduce"
        )
    return committed
