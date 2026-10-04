# Quebec authorized project-revision panel

## Purpose

The Quebec authorized project-revision panel turns the lifecycle history already
published in the official infrastructure dashboard into a reproducible,
source-preserving research table. It is the first AIIO intake with a
publisher-stable project identifier and multi-project cost and schedule revision
chains. It is not a final-cost outturn panel and does not identify an AI effect.

The machine outputs are:

- `data/model-runs/quebec_pqi_authorized_project_revisions_v0.1.json`;
- `data/processed/quebec_pqi_authorized_project_revisions.csv`; and
- `data/processed/quebec_pqi_authorized_revision_events.csv`.

Rebuild them with `npm run outcomes:quebec:normalize`.

## Official source contract

The input dashboard is the [Quebec infrastructure project dashboard](https://www.tresor.gouv.qc.ca/infrastructures-publiques/tableau-de-bord).
The separate [official field-description PDF](https://www.donneesquebec.ca/recherche/dataset/67d85a7a-10af-4af0-b4da-abc64cfd735a/resource/d94c4be0-7ac6-46e6-86f4-5c40c9a6d47a/download/description-des-champs.pdf)
defines three fields that control this transformation:

- `no_projet` is a unique number retained throughout the project lifecycle;
- `cout_total` is total authorized cost; and
- `suivi_modifications` presents project changes authorized during the project
  lifecycle and their effective dates.

Both source files have retrieval manifests and content hashes. The normalizer
rechecks the manifest hashes and three field-definition text anchors before
reading any project history.

## Parsing rules

The source history is French prose grouped under effective month/year headings.
AIIO preserves the source event text as a SHA-256 trace and parses only narrowly
declared patterns:

1. A cost event requires an explicit previous authorized cost and new authorized
   cost in the same statement. A stated increase or decrease must reconcile to
   the difference within CAD 110,000, allowing the source's one-decimal-million
   rounding.
2. A cost chain passes only when each event's new value equals the next event's
   previous value and the final event equals current `cout_total`.
3. A schedule event requires an explicit previous and revised complete-service
   month. Events that combine partial and complete dates ambiguously are
   excluded.
4. A schedule chain passes only when adjacent revisions reconcile and the final
   revision equals current `date_fin_mise_en_service`.
5. A fiscal-year statement that complete service was achieved is retained as a
   fiscal-year marker. It is not converted to an exact date.
6. Publisher sector and work type remain observed. The common AIIO asset class
   is a separate inference using the existing provincial-project taxonomy.

Rows with incomplete or inconsistent chains remain in the summary with quality
flags, but their gated baseline/current comparison fields stay null.

## Current coverage

The 2026-08-20 source vintage contains 649 projects, all with stable lifecycle
identifiers and a published history field. The parser finds:

| Measure | Count |
| --- | ---: |
| Authorized cost-revision events | 228 |
| Projects with a cost-revision event | 142 |
| Reconciled cost-revision chains | 141 |
| Authorized completion-revision events | 276 |
| Projects with a completion-revision event | 176 |
| Reconciled completion-revision chains | 168 |
| Projects with both reconciled chains | 111 |
| Fiscal-year complete-service markers | 87 |

The reconciled candidate set covers health facilities, schools and
postsecondary institutions, roads/transit/airports, government and civic
facilities, housing, municipal water/resilience and other public
infrastructure.

## Descriptive statistics boundary

The model artifact calculates transparent descriptive summaries so the parser
can be audited and a later reference-class protocol can be designed. Across the
currently surviving dashboard projects with reconciled chains, the median
cumulative authorized-cost change is 19.07% and the median authorized
complete-service change is 12 months. These are historical descriptions of
authorized revisions in one Quebec dashboard vintage. They are not forecasts,
causal effects, final outturn distributions or transferable Alberta escalation
factors.

Asset-class summaries are retained internally for research review. They remain
outside Decision Mode until the source-vintage selection design, parser review,
price-basis treatment and reference-class protocol are independently approved.

## Publication boundary

The panel closes several field-discovery gaps, but four decisive limitations
remain:

- the current dashboard is a survivor snapshot and omits projects retired from
  earlier vintages;
- the publication threshold changed from $50 million to $20 million in November
  2020;
- authorized cost is not final audited outturn and has no estimate price-basis
  date; and
- exact actual start and completion dates are generally unavailable.

Therefore:

```text
authorized revision reference panel: not authorized
public-project cost outcome panel: not authorized
public-project schedule outcome panel: not authorized
AI-attributable effect: not authorized
```

The archived-catalog inventory, threshold-aware ten-vintage milestone panel and
57-project stratified parser-review packet are now implemented. The milestone
panel shows that 472 of 1,121 observed stable IDs are absent from the latest
snapshot, but does not infer exit causes. See
`docs/methodology/quebec-milestone-longitudinal-panel.md`. The next evidence step
is to complete the independent parser review and test the milestone design
against the full 69-vintage panel before any reference distribution is promoted.
