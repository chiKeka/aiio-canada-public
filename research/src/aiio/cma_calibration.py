from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .calibration import build_reference_class_baseline


MODEL_ID = "AIIO_CA_VAN_TOR_MTL_BCPI_REFERENCE_BASELINE_0_1"
GEOGRAPHY_LABELS = {
    "CMA_462": "Montréal CMA",
    "CMA_535": "Toronto CMA",
    "CMA_933": "Vancouver CMA",
}
LIMITATIONS = [
    "BCPI measures contractor bid-price change for model buildings, not the realized cost of a particular project.",
    "Vancouver, Toronto and Montréal CMA results are local market references and are not province-wide substitutes.",
    "Institutional, school and office reference classes have histories from 1981; the bus-depot reference begins in 2017 and may remain not assessed.",
    "Empirical error bands are historical forecast-error ranges, not confidence intervals or probability guarantees.",
    "The baseline contains no AI-attributable effect and no coefficient is transferred between CMAs or provinces.",
]


def _implementation_manifest() -> dict[str, str]:
    calibration_path = Path(__file__).with_name("calibration.py")
    adapter_path = Path(__file__).parent / "adapters" / "statcan.py"
    wrapper_path = Path(__file__)
    return {
        "adapter_sha256": hashlib.sha256(adapter_path.read_bytes()).hexdigest(),
        "calibration_sha256": hashlib.sha256(calibration_path.read_bytes()).hexdigest(),
        "cma_wrapper_sha256": hashlib.sha256(wrapper_path.read_bytes()).hexdigest(),
    }


def _implementation_sha256(manifest: dict[str, str]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_cma_reference_class_baseline(
    bcpi_path: Path,
    output_path: Path,
    *,
    horizons_years: Iterable[int] = range(1, 6),
) -> dict[str, Any]:
    result = build_reference_class_baseline(
        bcpi_path,
        horizons_years=horizons_years,
        geography_labels=GEOGRAPHY_LABELS,
        model_id=MODEL_ID,
        limitations=LIMITATIONS,
    )
    implementation_manifest = _implementation_manifest()
    result["code_manifest"] = implementation_manifest
    result["code_sha256"] = _implementation_sha256(implementation_manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
