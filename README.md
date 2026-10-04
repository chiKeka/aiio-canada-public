# AI Infrastructure Impact Observatory Canada

AIIO Canada is a public research program for tracing how AI infrastructure capital expenditure changes the cost, capacity, and delivery of Canadian public infrastructure. Alberta is the first implementation; the data model is designed to expand province by province.

The product has four linked components:

1. a reproducible public-data evidence pipeline;
2. a typed graph propagation model adapted from the PSPE/S3 graph method;
3. an explicit scenario layer for counterfactual investment diagnostics plus a separate MW-based power overlay; and
4. public outputs: an interactive website, weekly digest, downloadable datasets and an auditable Excel workbook.

## Research question

> How, when, and where does AI infrastructure capital expenditure reshape cost, capacity, and delivery across Canada?

The Alberta pilot asks what happens if $50 billion of AI infrastructure investment lands in the province over 2027–2036: which trades tighten first, how much additional electricity and transmission capacity may be implicated, and which public projects are most exposed to competing demand.

## Non-negotiable publication rule

Every published value must be marked as **observed**, **corroborated**, **inferred**, **assumed**, or **scenario-only**. Scenario outputs are not forecasts. The v0.2 pressure scores are uncalibrated structural diagnostics—not empirical findings, probabilities, percentages or project-level delay estimates.

## Local development

```bash
npm install
npm run dev
```

`npm run dev`, `npm run build`, and `npm run start` use the native Next.js
runtime and are the canonical GitHub/Vercel path. The existing Sites-compatible
target remains available through `npm run dev:sites`, `npm run build:sites`, and
`npm run start:sites`.

The reproducible analytical gates are:

```bash
npm run research:validate
npm run labour:normalize
npm run labour:normalize:canada
npm run investment:normalize:canada
npm run macro:controls
npm run procurement:normalize
npm run outcomes:audit:normalize
npm run outcomes:quebec:normalize
npm run outcomes:quebec:vintages:fetch
npm run outcomes:quebec:vintages:normalize
npm run outcomes:quebec:review
npm run outcomes:quebec:archive:fetch
npm run outcomes:quebec:archive:normalize
npm run bcpi:normalize:provinces
npm run materials:screen
npm run materials:screen:provinces
npm run projects:exposure
npm run projects:normalize:provinces
npm run power:evidence
npm run power:planning:provinces
npm run digest:build
npm run digest:audit
npm run research-surface:build
npm run pspe:lineage
npm run program:audit
npm run attribution:readiness
npm run attribution:preflight
npm run attribution:panel
npm run attribution:estimate
npm run attribution:proxy-treatment
npm run attribution:proxy-association
npm run outcomes:pspc
npm run treatment:capex-screen
npm run treatment:announcement-ledger
npm run bcpi:normalize:reference-cmas
npm run cost:baseline:cmas
npm run cost:backcast:provinces
npm run cost:review:province-bridge
npm run cost:historical-envelope
npm run cost:historical-analogs
npm run cost:review-package
npm run model:run
npm run model:variants
npm run power:run
npm run research:test
npm run release:build
npm run release:verify
```

Research architecture and protocols live in `docs/`. The public application lives in `app/` and `components/`, with its evidence-led product language and visual rules in [`DESIGN.md`](DESIGN.md). Data, model, workbook and digest packages are added as the build advances.

The digest protocol is documented in
[`docs/methodology/weekly-evidence-digest.md`](docs/methodology/weekly-evidence-digest.md).
Edition dates use UTC, every source reference must match the source registry,
and the cadence audit fails when the latest intake is more than eight days old.

Program completeness is reported separately from publication readiness in
[`docs/release/program-readiness-audit.md`](docs/release/program-readiness-audit.md).
`npm run program:audit` permits documented pending or blocked research gates but
fails on structural defects. `npm run program:audit:release` fails unless every
decision-grade, independent-review and publication gate passes.

The committed labour extracts contain graph-relevant NOC vacancy and
offered-wage observations from Statistics Canada table 14-10-0444-01. One file
supports the Alberta pilot; the Canada-ready file preserves all 13 provincial
and territorial estimates without substituting a national average. Suppressed
values remain blank with their quality flags; they are never converted to zero.

Research integrity and AI assistance are documented in `docs/governance/dissertation-alignment.md` and `docs/governance/ai-assistance-log.md`.

Deployment and release provenance are documented in
`docs/release/vercel-deployment.md`.

GitHub runs the same lint, evidence-registry, model-test, and dual-build quality
gate on every change to `main` and on pull requests.

## Licence

AIIO Canada's original software and documentation are available under the
[Apache License 2.0](LICENSE). Third-party datasets and source documents retain
their original terms; see [THIRD_PARTY_DATA.md](THIRD_PARTY_DATA.md) and the
source registry before redistributing data.

## Review snapshot

This export is prepared for review only. Read [PUBLIC_SNAPSHOT.md](PUBLIC_SNAPSHOT.md) for the exact source omissions, public-mode checks, optional local acquisition boundaries and disabled deployment/refresh templates. Historical release receipts do not describe this transformed snapshot.
