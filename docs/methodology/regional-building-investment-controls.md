# Regional building-investment controls

## Question

How much seasonally adjusted non-residential building activity is occurring in
each published province, territory and census metropolitan area, independently
of the BCPI price signal?

The source is Statistics Canada table 34-10-0293-01, Investment in Building
Construction. AIIO retrieves the complete public ZIP and content-hashes the raw
vintage. The source publishes monthly values from 2017 onward.

## Locked selection

The v0.1 adapter selects four mutually nested/related aggregates:

- total non-residential;
- total industrial;
- total commercial; and
- total institutional and governmental.

It retains both seasonally adjusted current-dollar and constant-dollar values
and only `Types of work, total`. The adapter includes all 13 provinces and
territories and the 36 CMAs or CMA parts for which the selected seasonally
adjusted series are published in the current cube.

Monthly source values are summed into calendar quarters. A quarter is emitted
only when all three source months exist. If any monthly value is unavailable,
the quarterly value remains null with a quality flag; it is never converted to
zero. The monthly values are observed, while the quarterly sum is an inferred
arithmetic transformation.

## Current artifact

The 2026-06 vintage produces 14,896 observations across 49 geographies, 38
quarters, four structures and two investment bases. The run report records the
raw ZIP hash, retrieval-manifest hash, output hash, coverage and fail-closed
publication boundary.

## Interpretation boundary

This is a regional construction-activity control. It is not:

- realized AI/data-centre construction spend;
- public-project estimate-to-outturn performance;
- an engineering-construction measure for roads, rail, utilities or grid assets;
- a construction price index; or
- evidence of an AI-attributable effect.

The constant-dollar series is deflated by Statistics Canada using BCPI-derived
quarterly deflators. Analyses using BCPI as an outcome must avoid presenting the
constant-dollar control as an independent price measure and must run a
current-dollar sensitivity specification.
