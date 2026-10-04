# Program readiness audit

AIIO Canada reports completion in four distinct states so a built research
component is never mistaken for a decision-grade finding or a publishable
release.

- `pass`: the artifact or gate exists and its machine-checkable contract holds.
- `pending`: the work is defined but evidence, calibration or review is not yet
  sufficient.
- `blocked`: completion currently depends on an explicit external condition,
  such as an independent reviewer or a publication hold.
- `fail`: a required artifact, hash, geography contract or fail-closed boundary
  is broken.

`npm run program:audit` writes
`data/model-runs/program_readiness_current.json`. It exits successfully when
structural integrity holds, even if honest pending or blocked gates remain. A
structural failure exits non-zero after writing the report. This local audit is
run after the generated workbook exists; it is intentionally not part of the
clean-clone quality workflow because generated workbooks are not committed.

`npm run program:audit:release` is the stricter publication command. It exits
non-zero unless every release gate passes. A release workflow must build and
inspect the workbook, run the quality workflow checks, and then use this stricter
command before publication.

The audit checks the named research program, source registry and raw manifests,
Alberta graph/scenario engine, Alberta evidence spine, Canada labour coverage,
BC/Ontario/Quebec evidence intakes, the hash-reconciled Quebec authorized-revision
candidate panel, threshold-aware archive milestones, complete-catalog transition
panel, official-XLSX fallback contract, pending parser-review package,
weekly digest hashes and cadence, dual-mode website, workbook
inspection receipt, the evolving research-surface provenance manifest, frozen
public release integrity,
decision-grade calibration, the hash-locked Alberta reference-cost review
instrument, independent review and publication state.

External review and deployment states live in
`data/governance/program-gates.json`. A prepared review package is not a passing
verdict. Changing an external status requires its cited evidence; authentication
or availability alone does not satisfy the review gate.
