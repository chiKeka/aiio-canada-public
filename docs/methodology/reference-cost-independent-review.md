# Reference-cost independent-review protocol

## Purpose

The Alberta E1 baseline cannot enter Decision Mode merely because its code is reproducible or one horizon passes the internal validation rules. This protocol turns independent modelling review into a versioned, machine-checkable evidence step while preserving the separation between review, adjudication and publication authority.

The deterministic packet is generated with:

```bash
npm run cost:baseline
npm run cost:review-package
```

Its two outputs are:

- `data/model-runs/alberta_reference_cost_review_package_v0.1.json`, the machine-readable contract; and
- `docs/reviews/2026-09-01-reference-cost-review-prompt.md`, the reviewer-facing prompt with the exact packet hash.

## Locked scope

The packet locks the normalized Alberta BCPI input, baseline artifact, implementation, review packager, calibration tests, artifact tests, calibration protocol, PSPE boundary audit and Decision Mode contract. It also records the exact 8-series/40-horizon status inventory. For v0.1 only one horizon passes the internal gate: Edmonton government and civic facilities at one year. That fact does not authorize publication.

The reviewer must assess ten required criteria: estimand boundary, temporal integrity, predeclared model selection, validation adequacy, interval semantics, fail-closed outputs, reference-class mapping, graph/unit separation, reproducibility and the public claim boundary.

## Verdict rules

A verdict is valid only when it locks the exact packet hash, records a non-author reviewer identity and independence declaration, dispositions every criterion and test, and supplies evidence for every finding. A `pass` is rejected when any criterion is conditional or failed, any declared test failed or was not run, or an open critical/high finding remains. A passing recommendation is limited to `authorize_baseline_only`; every E2, project-budget, province-wide, graph-monetization and failed-horizon claim remains prohibited.

Validate a returned verdict with:

```bash
PYTHONPATH=research/src python3 -m aiio.cli --root . validate-reference-cost-verdict \
  data/model-runs/alberta_reference_cost_review_package_v0.1.json \
  path/to/independent-verdict.json
```

Verdict validation is intentionally non-mutating. It does not alter the baseline artifact, `program-gates.json`, the public manifest or the website. The research lead must separately adjudicate findings and approve any release-state change.

## Reviewer channels

The contract accepts a human subject-matter expert, Claude CLI or Grok CLI reviewer. Tool availability or authentication is not evidence of review. Each reviewer must inspect the same hash-locked packet and return the same verdict schema; prose-only approval does not pass the gate.
