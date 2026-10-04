from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .registry import load_registry
from .schemas import ValidationError


POLICY_VERSION = "AIIO_SOURCE_FRESHNESS_0_2"


def _maximum_age_days(frequency: str) -> int:
    value = frequency.lower().strip()
    if "daily" in value or "continuous" in value:
        return 10
    if "monthly" in value:
        return 45
    if "quarter" in value:
        return 120
    if "annual" in value or "quinquennial" in value:
        return 400
    if any(token in value for token in ("event", "irregular", "ongoing", "periodic", "cycle", "dashboard", "methodology", "one-time", "discontinued")):
        return 190
    raise ValidationError(f"no freshness policy for update_frequency: {frequency!r}")


def build_source_freshness_report(
    registry_path: Path,
    as_of: str,
    output_path: Path | None = None,
) -> dict[str, Any]:
    try:
        report_date = date.fromisoformat(as_of)
    except ValueError as exc:
        raise ValidationError(f"as_of must be an ISO date: {as_of!r}") from exc

    # Receipts supersede registry metadata, but an unsuccessful attempt never
    # advances last success or the observation date of last-good evidence.
    root = registry_path.parent.parent.parent
    receipts: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "data/raw").glob("**/*.manifest.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        source_id = item.get("source_id")
        success = item.get("retrieved_at", "")[:10]
        if source_id and item.get("result") == "success" and success <= as_of:
            old = receipts.get(source_id, {})
            if success >= old.get("last_success", ""):
                receipts[source_id] = {"last_success": success, "last_attempt": success, "status": "checked", "receipt_path": str(path.relative_to(root))}
    for attempts_path in (root / "data/model-runs/construction-source-refresh.json", root / "data/model-runs/weekly-source-refresh.json"):
        if attempts_path.exists():
            for source_id, item in json.loads(attempts_path.read_text()).get("sources", {}).items():
                if item.get("last_attempt", "") <= as_of:
                    old = receipts.get(source_id, {})
                    merged = {**old, **item}
                    successes = [value for value in (old.get("last_success"), item.get("last_success")) if value]
                    if successes:
                        merged["last_success"] = max(successes)
                    receipts[source_id] = merged
    sources = []
    by_domain: dict[str, dict[str, int]] = {}
    for source in sorted(load_registry(registry_path), key=lambda item: item.source_id):
        receipt = receipts.get(source.source_id, {})
        success = receipt.get("last_success")
        verified = date.fromisoformat(success or source.last_verified)
        age_days = (report_date - verified).days
        if age_days < 0:
            raise ValidationError(f"source {source.source_id} was verified after report date")
        maximum_age_days = _maximum_age_days(source.update_frequency)
        state = "current" if age_days <= maximum_age_days else "stale"
        record = {
            "source_id": source.source_id,
            "domain": source.domain,
            "registry_status": source.status.value,
            "last_verified": verified.isoformat(),
            "verification_basis": "successful_retrieval_receipt" if success else "registry_verification_only",
            "last_attempt": receipt.get("last_attempt"),
            "last_success": success,
            "last_attempt_status": receipt.get("status", "unrecorded"),
            "observation_date": receipt.get("observation_date"),
            "review_due": date.fromordinal(verified.toordinal() + maximum_age_days).isoformat(),
            "age_days": age_days,
            "maximum_age_days": maximum_age_days,
            "update_frequency": source.update_frequency,
            "freshness_state": state,
        }
        sources.append(record)
        domain = by_domain.setdefault(source.domain, {"source_count": 0, "current_count": 0, "stale_count": 0})
        domain["source_count"] += 1
        domain[f"{state}_count"] += 1

    stale = [source["source_id"] for source in sources if source["freshness_state"] == "stale"]
    report = {
        "schema_version": "1.0.0",
        "report_id": POLICY_VERSION,
        "as_of_date": as_of,
        "status": "operational" if not stale else "degraded",
        "source_count": len(sources),
        "current_count": len(sources) - len(stale),
        "stale_count": len(stale),
        "stale_source_ids": stale,
        "domain_summary": [
            {"domain": domain, **counts} for domain, counts in sorted(by_domain.items())
        ],
        "sources": sources,
        "methodology": {
            "basis": "calendar days since last successful retrieval receipt; explicit registry-only fallback where receipts are unavailable",
            "policy": "daily/continuous=10; monthly=45; quarterly=120; annual/quinquennial=400; event, irregular, periodic and documentary sources=190",
            "boundary": "Freshness confirms source verification cadence only. It does not authorize causal attribution or forecasts.",
        },
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
