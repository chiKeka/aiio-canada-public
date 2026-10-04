from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from dataclasses import asdict


def refresh_canadabuys(root: Path, checked_date: str, *, fetcher=None):
    """Verify registered candidate CSVs only; never rebuild/promote outcome evidence."""
    from aiio.adapters.canadabuys import TENDER_SOURCE_ID, AWARD_SOURCE_ID, CONTRACT_SOURCE_ID, TENDER_REQUIRED_FIELDS, AWARD_REQUIRED_FIELDS, CONTRACT_REQUIRED_FIELDS
    from aiio.retrieval import retrieve
    from aiio.registry import load_registry
    from aiio.schemas import ValidationError

    sources = {source.source_id: source for source in load_registry(root / "data/registry/sources.json")}
    fetcher = fetcher or retrieve
    results = {}
    failures = []
    for source_id, fields in ((TENDER_SOURCE_ID, TENDER_REQUIRED_FIELDS), (AWARD_SOURCE_ID, AWARD_REQUIRED_FIELDS), (CONTRACT_SOURCE_ID, CONTRACT_REQUIRED_FIELDS)):
        def validate(content, fields=fields, source_id=source_id):
            reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
            missing = fields - set(reader.fieldnames or ())
            if missing or next(reader, None) is None:
                raise ValidationError(f"{source_id}: empty CSV or missing required fields {sorted(missing)}")
        try:
            result = record_fetch(root / "data/model-runs/weekly-source-refresh.json", source_id, checked_date, lambda: fetcher(sources[source_id], root / "data/raw", validate_content=validate))
            results[source_id] = asdict(result)
        except Exception:
            failures.append(source_id)
    if failures:
        raise ValidationError(f"CanadaBuys refresh failed for {', '.join(failures)}; last-good evidence retained")
    return results


def independent_refresh_checks(root: Path, checked_date: str, *, procurement=None, construction=None):
    """A failed feed group must not prevent independent groups from being checked."""
    failures = []
    try:
        (procurement or refresh_canadabuys)(root, checked_date)
    except Exception as exc:
        failures.append({'group': 'canadabuys', 'error_type': type(exc).__name__})
    completed = (construction or subprocess.run)([sys.executable, str(root / 'research/scripts/refresh_construction_evidence.py'), '--root', str(root), '--as-of', checked_date], cwd=root, check=False)
    if completed.returncode:
        failures.append({'group': 'construction', 'returncode': completed.returncode})
    return failures


def partial_refresh_summary(root: Path, failures: list) -> dict:
    failed_sources = []
    for name in ('weekly-source-refresh.json', 'construction-source-refresh.json'):
        path = root / 'data/model-runs' / name
        if path.exists():
            failed_sources.extend(source_id for source_id, receipt in json.loads(path.read_text()).get('sources', {}).items() if receipt.get('status') == 'error')
    return {'status': 'partial_refresh' if failures or failed_sources else 'review_pr_required', 'failed_source_ids': sorted(set(failed_sources)), 'failed_feed_groups': failures}


def record_fetch(receipt_path: Path, source_id: str, checked_date: str, operation):
    """Persist actual attempt dates; failure retains last success and last-good values."""
    report = json.loads(receipt_path.read_text()) if receipt_path.exists() else {"sources": {}}
    old = report["sources"].get(source_id, {})
    try:
        result = operation()
        report["sources"][source_id] = {**{key: value for key, value in old.items() if key not in {"error_type", "reason", "http_status"}}, "last_attempt": checked_date, "last_success": checked_date, "status": "checked"}
    except Exception as exc:
        report["sources"][source_id] = {**old, "last_attempt": checked_date, "status": "error", "error_type": type(exc).__name__, "http_status": getattr(exc, "code", None), "reason": "source_fetch_failed_last_good_retained"}
        print(json.dumps({"source_id": source_id, **report["sources"][source_id]}), file=sys.stderr)
        raise
    finally:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = receipt_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        temporary.replace(receipt_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh AIIO's review-gated weekly public evidence")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--edition-date", type=date.fromisoformat, default=datetime.now(UTC).date())
    parser.add_argument("--check-receipts", action="store_true", help="Offline read-only check of local receipts; no fetch, edition, commit, or publication")
    parser.add_argument("--canadabuys-only", action="store_true", help="Fetch and validate registered candidate CSVs and operational receipts only; no evidence promotion")
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / "research" / "src"))

    from aiio.adapters.ckan_permit_proxies import fetch_ckan_permit_candidates, normalize_ckan_permit_proxy
    from aiio.adapters.edmonton_permits import fetch_edmonton_permit_candidates, normalize_edmonton_permit_proxy
    from aiio.adapters.vancouver_permits import fetch_vancouver_permit_candidates, normalize_vancouver_permit_proxy
    from aiio.comparison_market_association import run_comparison_market_association
    from aiio.comparison_market_panel import build_comparison_market_panel
    from aiio.digest import build_digest
    from aiio.research_surface import build_research_surface_manifest
    from aiio.source_freshness import build_source_freshness_report
    from aiio.practical_route import build_practical_evidence_route

    as_of = args.edition_date.isoformat()
    checked_date = datetime.now(UTC).date().isoformat()
    if args.check_receipts:
        report = build_source_freshness_report(root / "data/registry/sources.json", checked_date)
        print(json.dumps({"mode": "offline_receipt_check", "evaluated_at": checked_date, "source_count": report["source_count"], "stale_source_ids": report["stale_source_ids"], "writes": False, "network": False}, indent=2))
        return
    raw_root = root / "data" / "raw"
    if args.canadabuys_only:
        failures = []
        try:
            canadabuys = refresh_canadabuys(root, checked_date)
        except Exception as exc:
            canadabuys = {}
            failures.append({'group': 'canadabuys', 'error_type': type(exc).__name__})
        build_source_freshness_report(root / "data/registry/sources.json", checked_date, root / "public/data/source-receipts.json")
        print(json.dumps({**partial_refresh_summary(root, failures), "source_ids": list(canadabuys), "automatic_model_change": False}, indent=2))
        if failures:
            raise SystemExit(1)
        return
    refresh_failures = independent_refresh_checks(root, checked_date)

    receipt_path = root / "data/model-runs/weekly-source-refresh.json"
    def fetch_with_receipt(source_id, operation):
        return record_fetch(receipt_path, source_id, checked_date, operation)

    edmonton = fetch_with_receipt("EDMONTON_GENERAL_BUILDING_PERMITS", lambda: fetch_edmonton_permit_candidates(raw_root))
    edmonton_raw = Path(edmonton["archive_path"])
    edmonton_report = normalize_edmonton_permit_proxy(
        edmonton_raw,
        root / "data/processed/edmonton_data_centre_permit_proxy.csv",
        root / "data/model-runs/edmonton_data_centre_permit_proxy_v0.1.json",
        source_as_of_date=as_of,
        retrieval_manifest_path=edmonton_raw.with_suffix(".json.manifest.json"),
    )

    vancouver = fetch_with_receipt("VANCOUVER_ISSUED_BUILDING_PERMITS", lambda: fetch_vancouver_permit_candidates(raw_root))
    vancouver_raw = Path(vancouver["archive_path"])
    vancouver_report = normalize_vancouver_permit_proxy(
        vancouver_raw,
        root / "data/processed/vancouver_data_centre_permit_proxy.csv",
        root / "data/model-runs/vancouver_data_centre_permit_proxy_v0.1.json",
        source_as_of_date=as_of,
        retrieval_manifest_path=vancouver_raw.with_suffix(".json.manifest.json"),
    )

    reports = {"vancouver": vancouver_report}
    for city in ("toronto", "montreal"):
        receipt = fetch_with_receipt({"toronto": "TORONTO_CLEARED_BUILDING_PERMITS", "montreal": "MONTREAL_CONSTRUCTION_PERMITS"}[city], lambda: fetch_ckan_permit_candidates(city, raw_root))
        raw_path = Path(receipt["archive_path"])
        reports[city] = normalize_ckan_permit_proxy(
            city,
            raw_path,
            root / f"data/processed/{city}_data_centre_permit_proxy.csv",
            root / f"data/model-runs/{city}_data_centre_permit_proxy_v0.1.json",
            source_as_of_date=as_of,
            retrieval_manifest_path=raw_path.with_suffix(".json.manifest.json"),
        )

    permit_paths = {city: root / f"data/processed/{city}_data_centre_permit_proxy.csv" for city in reports}
    permit_report_paths = {city: root / f"data/model-runs/{city}_data_centre_permit_proxy_v0.1.json" for city in reports}
    panel_path = root / "data/processed/comparison_market_permit_bcpi_panel_v0.1.csv"
    panel_report_path = root / "data/model-runs/comparison_market_permit_bcpi_panel_v0.1.json"
    panel_report = build_comparison_market_panel(
        root,
        root / "data/processed/bcpi_reference_van_tor_mtl.csv",
        permit_paths,
        permit_report_paths,
        panel_path,
        panel_report_path,
    )
    association = run_comparison_market_association(
        panel_path,
        panel_report_path,
        root / "data/model-runs/comparison_market_proxy_association_v0.1.json",
    )

    # Rebuild every deterministic receipt downstream of the refreshed permit
    # evidence before publishing the surface manifest. The order is deliberate:
    # treatment feeds the panel, which feeds the non-causal association and
    # estimation gates; the preflight then locks the resulting evidence hashes.
    for script in (
        "attribution:proxy-treatment",
        "attribution:panel",
        "attribution:estimate",
        "attribution:proxy-association",
        "attribution:preflight",
    ):
        subprocess.run(["npm", "run", script], cwd=root, check=True)

    registry = json.loads((root / "data/registry/sources.json").read_text(encoding="utf-8"))
    canonical = {item["source_id"]: item["canonical_url"] for item in registry["sources"]}
    item_path = root / "data/digests/items" / f"{as_of}.json"
    digest_payload = {
        "schema_version": "1.1.0",
        "digest_id": f"AIIO_DIGEST_{as_of.replace('-', '_')}",
        "edition_date": as_of,
        "status": "review",
        "items": [{
            "item_id": f"MUNICIPAL_DATA_CENTRE_PERMIT_REFRESH_{as_of.replace('-', '_')}",
            "headline": "Four municipal permit feeds refresh the data-centre activity proxy",
            "sources": [
                {"source_id": source_id, "source_url": canonical[source_id]}
                for source_id in (
                    "EDMONTON_GENERAL_BUILDING_PERMITS",
                    "VANCOUVER_ISSUED_BUILDING_PERMITS",
                    "TORONTO_CLEARED_BUILDING_PERMITS",
                    "MONTREAL_CONSTRUCTION_PERMITS",
                )
            ],
            "observed_change": (
                f"Official municipal APIs were retrieved on {checked_date}. The controlled screens retain "
                f"{edmonton_report['data_centre_candidate_count']} Edmonton, "
                f"{reports['vancouver']['data_centre_candidate_count']} Vancouver, "
                f"{reports['toronto']['data_centre_candidate_count']} Toronto and "
                f"{reports['montreal']['data_centre_candidate_count']} Montréal candidate permit records. "
                f"The aligned comparison panel contains {panel_report['row_count']} market-quarter-asset rows; "
                f"the descriptive association uses {association['result']['observation_count']} rows."
                + (" Independent construction/procurement feed checks were partial; failed sources retain last-good values and are identified in the operational receipts." if refresh_failures else "")
            ),
            "model_implication": (
                "Retain the refreshed records as administrative activity proxies and review record-level changes. "
                "Do not treat permit counts, declared values or completion milestones as realized AI construction "
                "spending, labour hours, public-project outcomes or an attributable escalation coefficient."
            ),
            "evidence_status": "inferred",
            "geography_ids": ["CMA_835", "CMA_933", "CMA_535", "CMA_462"],
            "model_action": "review_candidate",
            "automatic_model_change": False,
        }],
    }
    item_path.parent.mkdir(parents=True, exist_ok=True)
    item_path.write_text(json.dumps(digest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest_manifest = build_digest(
        item_path,
        root / "data/digests" / f"{as_of}.md",
        args.edition_date,
        source_registry_path=root / "data/registry/sources.json",
        manifest_path=root / "data/digests" / f"{as_of}.manifest.json",
    )
    latest_digest = {
        "schema_version": "1.0.0",
        "digest_id": digest_manifest["digest_id"],
        "edition_date": digest_manifest["edition_date"],
        "status": digest_manifest["status"],
        "item_count": digest_manifest["item_count"],
        "source_ids": digest_manifest["source_ids"],
        "automatic_model_change": digest_manifest["automatic_model_change"],
    }
    latest_digest_path = root / "public/data/latest-digest.json"
    latest_digest_path.write_text(
        json.dumps(latest_digest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    freshness = build_source_freshness_report(
        root / "data/registry/sources.json", checked_date, root / "public/data/source-receipts.json"
    )
    practical_route = build_practical_evidence_route(
        root,
        as_of,
        root / "data/processed/ai_construction_proxy_alberta_v0.1.csv",
        root / "data/processed/public_projects_bc_on_qc.csv",
        root / "data/processed/quebec_pqi_authorized_revision_events.csv",
        root / "data/processed/public_project_prospective_snapshot_current.csv",
        root / "data/model-runs/practical_evidence_route_current.json",
    )
    subprocess.run([sys.executable, str(root / "scripts/build-construction-inputs.py"), "--root", str(root)], cwd=root, check=True)
    surface = build_research_surface_manifest(root, root / "public/data/research-surface.json")
    summary = partial_refresh_summary(root, refresh_failures)
    print(json.dumps({**summary, "edition_date": as_of, "candidate_counts": {"edmonton": edmonton_report["data_centre_candidate_count"], **{city: reports[city]["data_centre_candidate_count"] for city in reports}}, "comparison_panel_rows": panel_report["row_count"], "research_surface_artifacts": surface["artifact_count"], "automatic_model_change": False}, indent=2, sort_keys=True))
    if summary['status'] == 'partial_refresh':
        raise SystemExit(1)


if __name__ == "__main__":
    main()
