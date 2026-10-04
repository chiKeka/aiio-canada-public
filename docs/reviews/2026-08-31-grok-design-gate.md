# Independent design gate — Grok CLI

**Date:** 2026-08-31  
**Stage:** Research architecture before data ingestion  
**Status:** Reviewed; controls accepted into implementation

The reviewer identified five critical implementation gates:

1. Freeze one typed, signed graph schema—including lag, damping, ranges, provenance and epistemic status—before ingestion.
2. Reject public-source facts that lack a resolvable entity ID, citation, as-of date or epistemic label.
3. Make lag, damping and range composition deterministic so the same graph and scenario reproduce exactly.
4. Keep the $50B scenario as a sealed overlay that cannot mutate observed or corroborated records.
5. Require the website and workbook to consume the same immutable schema-versioned release artifact.

## Disposition

- Gates 1–2 are enforced in the registry schemas and validation layer.
- Gate 3 is part of the graph engine contract and deterministic test suite.
- Gate 4 is enforced by separate baseline and scenario types, paths and release manifests.
- Gate 5 is a release-blocking reconciliation test.

Claude CLI review was attempted at this gate but the locally installed CLI has no authenticated session. No credentials were requested or accessed; Claude review remains a later release gate.
