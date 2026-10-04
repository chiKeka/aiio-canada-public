"""Offline path triage from a trusted checkout; never a code-safety verdict."""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import sys


EXECUTABLE_SUFFIXES = {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd', '.wasm', '.exe', '.dll', '.so', '.dylib'}
CONFIG_NAMES = {'package.json', 'package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock', 'pnpm-lock.yaml', '.npmrc', 'pyproject.toml', 'requirements.txt', 'pipfile', 'pipfile.lock', 'dockerfile', 'makefile', 'vercel.json', '.gitleaks.toml', '.gitleaksignore'}
SENSITIVE_ROOTS = {'.github', '.openai', '.vercel', 'vendor', 'publication', 'data', 'research', 'scripts', 'tests'}


def reason(path: str) -> str | None:
    """Classify strings only. No file reads, imports or contributor execution."""
    path = path.strip()
    parts = PurePosixPath(path).parts
    if not path or not parts or '\\' in path or path.startswith('/') or any(part in {'.', '..'} for part in parts) or any(ord(c) < 32 for c in path):
        return 'invalid or ambiguous path; inspect manually'
    normalized = path.casefold()
    filename = PurePosixPath(normalized).name
    if PurePosixPath(normalized).parts[0] in SENSITIVE_ROOTS:
        return 'execution, workflow, dependency or publication-boundary area'
    if filename in CONFIG_NAMES or filename.startswith(('.env', 'vite.config.', 'next.config.', 'wrangler.')):
        return 'dependency, environment or build/security configuration'
    if PurePosixPath(normalized).suffix in EXECUTABLE_SUFFIXES:
        return 'executable code or library'
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paths-file', type=Path, required=True, help='Trusted metadata export with one changed path per line')
    args = parser.parse_args(argv)
    paths = args.paths_file.read_text(encoding='utf-8').splitlines()
    flagged = [(path, reason(path)) for path in paths]
    print('Path triage only: manually inspect the complete diff and exact head before execution or merge.')
    for path, finding in flagged:
        if finding:
            print(f'REVIEW: {path!r}: {finding}')
    if not paths:
        print('No filenames supplied; this is incomplete evidence.')
        return 2
    print(f'{len(paths)} paths inspected; this does not validate file contents, identity, secrets or safety.')
    return 2 if any(finding for _, finding in flagged) else 0


if __name__ == '__main__':
    sys.exit(main())
