# Grok Canada workforce and recruitment-screen gate

## Scope

The read-only review covered the Statistics Canada 2021 Census selected-coordinate adapter, the normalized 78-cell provincial/territorial workforce stock, the cross-vintage JVWS recruitment screen, release hashes, website language, workbook formula checks and tests for v0.5.0-dev. The reviewer did not provide evidence, parameters or code and was instructed not to edit or deploy.

## Initial gate

Grok returned `GO` for a labelled research prototype and independently reproduced all 78 occupation ratios with zero mismatches. It confirmed 13-geography/six-NOC coverage, the six archived WDS code-2 zero fillers, trade completeness exclusions, manifest and publication hashes, workbook checks, and separation from the unchanged graph and power layers.

The initial report nevertheless identified one High public-label defect and four Medium hardening items:

- Census code-2 zero fillers were displayed on the website as “rounded” rather than explicitly as published zero fillers;
- tests did not lock published-zero vacancy behaviour, complete-trade aggregation or ranking exclusions;
- the workbook dashboard disclaimer used a fixed row that could overwrite a future fourth complete trade;
- dual-missing cells did not disclose both an unpublished vacancy and a zero workforce denominator;
- incomplete constructed trade rows were labelled observed rather than inferred.

It also noted that the methods page omitted the labour-screen limitations and that the source register incorrectly referred to LFS rather than Census quality flags.

## Disposition

All High and Medium findings were addressed before publication. The website now says `published zero filler`; the diagnostic exposes the combined dual-missing state; all trade-diagnostic rows are inferred; the dashboard note position is data-dependent; and tests cover published zero, aggregate arithmetic, evidence status and ranking exclusion. Labour-screen limitations are displayed on the methods page and the source-register wording now names Census and JVWS.

## Post-fix gate

The exact rebuilt candidate at source commit `c4749145575ff5c95ddd508b22c8be48384cddb9` received `GO` with no remaining Blocker, High or Medium finding. Grok confirmed:

- all prior findings were closed;
- all 14 input hashes, 11 release-output hashes and eight public-artifact hashes reconciled;
- the release, public manifest and publication-artifact record identify the same source commit;
- all 78 occupation diagnostics recomputed exactly;
- all workbook release checks passed;
- graph and power inputs remained byte-identical to v0.4.

## Retained limitations

The screen remains sparse: 54 of 78 occupation ratios are unavailable and 44 of 52 trade aggregates are incomplete. Six cells have both an unpublished vacancy numerator and a Census zero-filler denominator. The denominator predates the numerator by 1,788 days, uses the 2021 Census 25% long-form sample and random rounding, and reflects the COVID-19 third-wave reference week. Several published JVWS cells carry quality code E. The diagnostic is not a vacancy rate, current-capacity estimate, spare-capacity measure, project-delay estimate or graph calibration input.
