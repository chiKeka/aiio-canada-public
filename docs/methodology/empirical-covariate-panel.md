# E2 empirical covariate panel

## Purpose

This pipeline assembles the balanced, quarterly comparison-market spine required by the E2 AI-attribution design. It covers Calgary, Edmonton, Vancouver, Toronto and Montréal from 2017 Q1 through the latest common quarter, repeated for health facilities, schools/postsecondary and government/civic facilities.

The panel is an estimation input, not an effect estimate. It provides observed market-price proxies, non-residential building investment, provincial macro controls and trade labour indicators. The locked treatment and public-project outcome fields remain empty until authorizing evidence is acquired.

## Grain and inputs

The grain is `region × quarter × asset class`. Inputs are the hash-locked BCPI CMA extracts, quarterly building-investment controls, regional macro-control panel, labour availability panel and the E2 attribution and acquisition contracts.

BCPI movements describe market bid-price conditions. They do not substitute for estimate-to-outturn public-project cost outcomes. Provincial labour and macro values are repeated across CMAs within a province and retain that geographic limitation.

## Fail-closed boundary

Every row explicitly sets treatment presence, outcome presence and estimation eligibility to false. The builder rejects missing required region–asset–quarter price or investment cells, scope drift, duplicate keys, and any attempted population of treatment or outcome fields. Announced capital expenditure, permit value, requested electricity load, scenarios and graph pressure scores are never converted into realized treatment.

The estimator may run only after a separate authorization step verifies at least two treated regions, three eligible controls per cohort, two asset classes, eight pre-treatment quarters, four post-treatment quarters, common support, and the required outcome fields.

## Reproduction

Run `npm run attribution:panel`. The command writes the processed CSV and a JSON receipt containing input hashes, output hash, coverage, field completeness and publication boundaries.
