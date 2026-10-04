# Alberta public-delivery asset exposure method

## Purpose

This screen identifies projects in delivery windows that could plausibly share
labour, materials, procurement capacity, or schedules with AI infrastructure.
It is a portfolio-overlap diagnostic, not evidence that a project has already
experienced competition, delay, or cost escalation.

## Source and classification

The source is the Alberta Major Projects inventory. Core AI facilities and their
classified enabling-power projects are excluded to avoid counting the shock on
both sides of the screen. Remaining records are mapped through a controlled
project-type taxonomy to:

- health facilities;
- schools and post-secondary facilities;
- government and civic facilities;
- roads, transit, and airports;
- municipal water and resilience assets; and
- broad power-sector infrastructure.

The power category deliberately includes generation and other power projects; it
is not labelled as regulated utilities. Sponsor signals use declared developer
names and are reported as government/public-institution, municipal/public-utility,
or unresolved. They are classification inferences, not legal ownership findings.

## Schedule and cost transformations

A record with complete start and end years overlaps the counterfactual window if
the intervals intersect. A record with an incomplete schedule remains
`indeterminate_incomplete_schedule` unless the available boundary proves that it
falls outside the window.

Reported cost is divided uniformly across inclusive project years only when cost,
start year, and end year are all present. Annual rows show the resulting
indicative annualized cost. Portfolio summaries show the indicative portion
allocated to the scenario window. Neither quantity is an expenditure forecast or
a construction-curve estimate.

## Coverage limits

The Alberta Major Projects inventory has a publication threshold and is not a
complete public capital plan, procurement register, or municipal project census.
Missing costs remain null. Coverage counts and unresolved sponsor counts must be
shown alongside any aggregate.

