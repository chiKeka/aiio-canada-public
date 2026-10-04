# System architecture

AIIO Canada is a research system with several publication surfaces. The website and workbook consume versioned outputs; neither contains the authoritative logic.

## Pipeline

```text
Public sources
    ↓
Source register + immutable retrieval records
    ↓
Normalized observations + claim/evidence coding
    ↓
Provincial baseline and project inventory
    ├── guarded labour recruitment screen
    ├── material-cost component screen
    ├── public-delivery asset overlap screen
    └── observed power request/contract boundary
    ↓
Held-out reference-class baseline
    ↘ AI-attributable increment (withheld pending identification)
    ↓
Typed CAD-pressure graph + scenario shocks
    ↓
Propagation, sensitivity and validation runs
    ↘ independent MW-based power overlay
    ↓
Versioned releases
    ├── public website
    ├── weekly digest
    ├── CSV/JSON downloads
    └── Excel workbook
```

## Components

### 1. Evidence registry

Stores source identity, publisher, URL, access method, publication and retrieval dates, geography, licence/access notes, content hash and status. A source may support many observations or claims. Revisions are additive and remain auditable.

### 2. Ingestion and normalization

Source-specific adapters retrieve machine-readable files where available. Raw responses are retained by content hash. Transformation code emits normalized records and validation results. Manual extraction is permitted only with a reviewer and page/table locator.

Independent model review is also artifact-based. The Alberta E1 review instrument hash-locks the normalized input, model artifact, implementation, tests and claim-boundary documents, then requires a separate criterion-level JSON verdict. Verdict validation is non-mutating: review evidence cannot silently authorize a projection or publish a release.

### 3. Baseline

The baseline describes the observed system before a scenario shock: public projects, employment and vacancies by occupation, wages, construction price indices, material supply proxies, generation and transmission outlooks, and known AI/data-centre projects. Detailed current vacancies and the 2021 Census workforce stock remain separately dated. Their guarded cross-vintage ratio is an inferred recruitment screen, not a vacancy rate or graph calibration input.

### 4. Cost baseline and attribution

The cost-translation pipeline is modular. A reference-class baseline forecasts
an observed BCPI model-building index through locked rolling-origin calibration
and validation partitions. Failed asset/geography/horizon combinations remain
null. The AI-attributable increment is a separate causal estimand and remains
null until a historical treatment, counterfactual and project-outcome panel
passes the protocol in
[`docs/methodology/calibration-protocol.md`](methodology/calibration-protocol.md).
The graph never supplies a multiplier for the reference baseline.

A separate historical envelope publishes descriptive one- through five-year
BCPI change distributions for the Alberta model-building reference classes. It
is available for decision context even when the forecast gate fails because it
does not project the next period or translate an index into project cost. The
product reports overlapping- and non-overlapping-window counts and labels short
histories explicitly. Its method is documented in
[`docs/methodology/historical-cost-envelope.md`](methodology/historical-cost-envelope.md).

The E2 readiness pipeline validates a locked regional panel contract against the
source registry and writes an explicit missing-data/gate artifact. It separates
authorizing realized treatment measures from permit, announcement and grid
proxies, and it separates tender timing from physical schedule outcomes. The
protocol is documented in
[`docs/methodology/ai-attribution-identification.md`](methodology/ai-attribution-identification.md).

The Quebec project-dashboard intake adds a source-faithful candidate panel of
authorized cost and completion-month revisions. Stable publisher lifecycle IDs,
field-dictionary anchors, event arithmetic and revision-chain endpoints are
hash-checked before a record can enter the panel. A separate archive module
inventories all 69 official CSV resources and now represents every snapshot date.
The complete panel exposes 43,044 project observations, adjacent-snapshot stable-ID
transitions and publisher-declared retirement markers. One malformed CSV is
paired with the publisher's official XLSX for the same date under an explicit
substitution contract. A deterministic 57-project review packet carries exact
source text and blank reviewer fields. None of these artifacts supplies audited
final outturns, a causal AI effect or a transferable Alberta cost factor.

### 5. Graph model

Nodes represent shocks, resources, materials, cost signals and public-delivery delay pressure. Directed typed edges encode mechanisms. Each edge records sign, magnitude range, lag, absorption, supporting evidence, confidence, author, version and assumption ID. Resource, material, signal and outcome nodes may retain part of a pressure state into later years using an explicit low/central/high retention factor. The engine reports signed totals and the paths that produced them.

### 6. Scenario layer

A scenario is an explicit set of non-observed inputs: investment quantum, timing, construction share, local capture and normalization denominators. It produces a versioned structural diagnostic against a named graph. The Alberta suite adds four full model runs that hold the $50 billion total and graph constant while isolating timing concentration, timing extension and local capture. Their comparison matrix is the product-facing stress-test layer; the existing denominator, absorption and retention sensitivities remain research-facing diagnostics. Neither is a probability interval.

Power-system quantities are deliberately separate. An observed evidence screen records AESO request, allocation and contract quantities without turning them into a forecast. An independent scenario overlay starts with IT load in MW, uses energy PUE only for annual energy, applies a distinct peak-to-IT factor to peak demand, and stages load using an annual commissioning profile. It cannot be inferred from the CAD scenario and is not an AESO needs assessment.

### 7. Publication layer

All outputs read an immutable release manifest containing input hashes, code version, model configuration and run time. The public interface must expose evidence status and uncertainty. Excel reproduces key tables through exported data, not duplicated hidden logic.

## Technology plan

- Public application: React/TypeScript with server rendering and accessible interactive controls.
- Current persistence: versioned JSON/CSV evidence, digest items and release
  manifests in Git. This keeps every public result reproducible and reviewable;
  the deployed dashboard remains read-only and requires no runtime database.
- Future transactional persistence: add managed Postgres only when the product
  needs saved user scenarios, accounts, runtime calculations, annotations or a
  multi-user review queue. Keep research evidence and immutable releases in Git
  even after that addition.
- Analytical pipeline: Python packages with typed schemas, tests and deterministic command-line entry points.
- Raw and derived research files: versioned local directories with manifests and hashes; object storage can be added at publication scale.
- Workbook: generated `.xlsx` with formulas, named assumptions, data dictionary, provenance and reconciliation checks.

## Release gates

1. Schema and source validation.
2. Baseline series integrity, historical-window reconciliation, rolling-origin partition and fail-closed output checks.
3. Labour geography/NOC coverage, missingness, zero-filler and cross-vintage formula checks.
4. Material-series coverage and aligned-period checks.
5. Public-project classification, schedule-missingness and cost-allocation checks.
6. Quebec field-dictionary anchors, lifecycle-ID uniqueness, complete-catalog
   coverage, source-representation substitution, vintage hashes, duplicate-row
   handling, revision arithmetic, endpoint reconciliation, parser-review state
   and fail-closed publication checks.
7. Power source-hash, requested-load ordering and Phase 1 reconciliation checks.
8. Graph DAG, self-loop, validity, retention and edge-metadata checks.
9. Scenario identity, sign, lag, mass-bound, additivity, sensitivity, deterministic and golden-run tests.
10. Workbook-to-release reconciliation.
11. Accessibility and public-language review.
12. Independent methodological review and documented disposition.
13. AI-attributable cost and schedule fields remain null unless the separate identification gate passes.
