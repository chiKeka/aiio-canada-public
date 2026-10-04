from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .schemas import ValidationError


MODEL_ID = "AIIO_PSPE_METHOD_LINEAGE_0_1"


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def build_pspe_method_lineage(
    root: Path, contract_path: Path, output_path: Path | None
) -> dict[str, Any]:
    root = root.resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "AIIO_PSPE_METHOD_LINEAGE_CONTRACT_0_1":
        raise ValidationError("unexpected PSPE lineage contract")
    source = contract.get("source_material", {})
    if source.get("distribution_status") != "local_only_not_redistributed":
        raise ValidationError("PSPE source material must retain its local-only boundary")
    availability = contract.get("source_repository_availability", {})
    if availability.get("status") != "method_repository_located_engine_source_not_located":
        raise ValidationError("PSPE repository availability must reflect verified local state")
    commit = availability.get("commit")
    if not isinstance(commit, str) or len(commit) != 40 or any(
        char not in "0123456789abcdef" for char in commit
    ):
        raise ValidationError("PSPE method repository receipt requires a Git commit")
    if availability.get("worktree_status_at_receipt") != "clean":
        raise ValidationError("PSPE method repository receipt must disclose a clean worktree")
    method_artifacts = availability.get("method_artifacts")
    if not isinstance(method_artifacts, list) or len(method_artifacts) < 5:
        raise ValidationError("PSPE method repository receipt is incomplete")
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("path"), str)
        or not isinstance(item.get("sha256"), str)
        or not item["sha256"].startswith("sha256:")
        or not isinstance(item.get("byte_size"), int)
        or item["byte_size"] <= 0
        for item in method_artifacts
    ):
        raise ValidationError("PSPE method repository artifact receipt is invalid")
    curriculum_receipts = [
        item for item in method_artifacts if item["path"] == "CURRICULUM.md"
    ]
    if len(curriculum_receipts) != 1 or curriculum_receipts[0]["sha256"] != source.get("sha256"):
        raise ValidationError("PSPE curriculum receipt does not reconcile to method repository")
    if availability.get("searched_engine_filenames") != [
        "graph_schema.py", "propagation.py", "s3_metrics.py", "sd_bridge.py"
    ]:
        raise ValidationError("PSPE engine-source search receipt is incomplete")
    mappings = contract.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        raise ValidationError("PSPE lineage requires at least one method mapping")
    seen_ids: set[str] = set()
    resolved = []
    for mapping in mappings:
        mapping_id = mapping.get("mapping_id")
        if not isinstance(mapping_id, str) or not mapping_id or mapping_id in seen_ids:
            raise ValidationError("PSPE mapping IDs must be unique and nonblank")
        seen_ids.add(mapping_id)
        paths = [
            mapping.get("aiio_implementation"),
            mapping.get("aiio_contract"),
            *(mapping.get("validation_tests") or []),
        ]
        if any(not isinstance(value, str) or not value for value in paths):
            raise ValidationError(f"{mapping_id} has an incomplete artifact mapping")
        artifacts = []
        for relative_path in paths:
            path = root / relative_path
            if not path.is_file():
                raise ValidationError(
                    f"{mapping_id} references a missing AIIO artifact: {relative_path}"
                )
            artifacts.append(
                {"path": relative_path, "sha256": sha256_file(path)}
            )
        resolved.append({**mapping, "artifacts": artifacts})
    non_claims = contract.get("non_claims")
    if not isinstance(non_claims, list) or len(non_claims) < 4:
        raise ValidationError("PSPE lineage requires explicit non-claims")
    report = {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "lineage_status": "adaptation_from_available_method_notes",
        "contract_sha256": sha256_file(contract_path),
        "source_material_receipt": source,
        "source_repository_availability": availability,
        "mapping_count": len(resolved),
        "mappings": resolved,
        "non_claims": non_claims,
        "publication_boundary": {
            "source_code_reproduction_claim_authorized": False,
            "methodological_inheritance_claim_authorized": True,
            "implemented_layer_claim_limited_to_mappings": True,
            "unimplemented_pspe_layers_claimed": False,
            "graph_score_monetization_authorized": False,
        },
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return report


def validate_pspe_method_lineage(
    root: Path, contract_path: Path, report_path: Path
) -> dict[str, Any]:
    expected = build_pspe_method_lineage(root, contract_path, None)
    actual = json.loads(report_path.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValidationError("PSPE method-lineage report is stale or unreconciled")
    return actual
