# Weekly evidence digest protocol

## Purpose

The AIIO Canada digest is the observatory's intake journal. It records newly
retrieved or newly transformed public evidence and states what the evidence may
mean for the research program. It is not a model changelog, a forecast, or an
approval mechanism.

## Cadence and clock

- Editions are dated in UTC so the edition date agrees with retrieval manifests.
- The normal tolerance is eight days between dated intake files.
- A scheduled repository check reports the digest as stale when the latest
  edition exceeds that tolerance.
- A stale digest is an operating alert. It does not invalidate a frozen release
  or cause the pipeline to invent an empty edition.

## Required item contract

Every item declares:

- a stable `item_id`;
- a headline;
- one or more source IDs and canonical URLs;
- an observed, corroborated, or inferred evidence status;
- the affected `PR_*` geography identifiers;
- the observed or inferred change;
- the potential model implication;
- a model action of `no_change`, `review_candidate`, or
  `promote_after_release`; and
- `automatic_model_change: false`.

The builder resolves each source ID against `data/registry/sources.json` and
requires the supplied URL to equal the registry's canonical URL. Assumptions and
scenarios cannot be presented as new evidence. Duplicate item or source IDs,
future model mutation, date disagreement, and incomplete references fail the
build.

## Immutable outputs

For an edition dated `YYYY-MM-DD`, the pipeline retains:

1. `data/digests/items/YYYY-MM-DD.json` — reviewed structured intake;
2. `data/digests/YYYY-MM-DD.md` — human-readable edition; and
3. `data/digests/YYYY-MM-DD.manifest.json` — input, registry, and rendered
   output hashes plus the publication boundary.

The manifest states that neither model parameters nor baselines changed and
that a versioned release is required for promotion.

## Promotion boundary

`review_candidate` means the item may motivate adapter, schema, calibration, or
scenario work. It does not authorize that work to enter Decision Mode.
`promote_after_release` may be used only after the relevant evidence and
modelling gates have passed; the actual promotion still occurs through a clean,
versioned release build. The digest builder has no code path that writes model
parameters.

## Operating commands

```bash
npm run digest:build
npm run digest:audit
npm run research:test
```

`digest:build` selects the newest valid `YYYY-MM-DD.json` intake, verifies that
its payload date matches its filename, and rebuilds that edition and manifest.
This keeps the CI determinism check aligned with future editions instead of a
hard-coded launch date.

The public website and workbook consume the digest contained in their release
manifest. A newer review edition may exist in the repository without changing
the current public release.
