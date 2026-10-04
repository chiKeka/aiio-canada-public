from __future__ import annotations

from pathlib import Path


def repository_path(path: Path) -> str:
    """Return a stable repository-relative path for generated artifacts."""
    resolved = path.resolve()
    parts = resolved.parts
    for anchor in ("data", "public", "docs", "research"):
        if anchor in parts:
            return Path(*parts[parts.index(anchor) :]).as_posix()
    # Tests and callers may intentionally write to a temporary directory. A
    # basename preserves useful provenance without leaking a machine path.
    return resolved.name
