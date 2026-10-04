# Alberta data-centre power evidence screen

## Purpose

This screen separates observed connection evidence from the independent AIIO
power scenario. It records what the Alberta Electric System Operator (AESO) has
published about requested data-centre load, the Phase 1 interim connection limit,
executed load contracts, and the boundary of its transmission statement.

## Sources and extraction

Three AESO sources are retained by content hash:

- the September 2025 data-centre update PDF;
- the current Large Load Projects page; and
- the June 2025 interim-approach announcement.

The six cumulative requested-load bars on page 1 of the PDF are manually
transcribed with a page/chart locator and bound to the PDF SHA-256 hash. Grok
CLI independently re-extracted all six labels and values from the embedded
chart image, recomputed the hash, and found no discrepancies. This is a recorded
independent machine review, not human peer review. HTML values are parsed by
explicit source-language patterns and must reconcile: the 970 MW and 230 MW
executed load contracts sum to the 1,200 MW allocated Phase 1 limit.

## Quantity distinctions

Requested MW, allocated-limit MW, executed-contract MW, connected MW, coincident
peak demand, generation capacity, and transmission capability are distinct. The
screen preserves these meanings rather than treating a request queue as a load
forecast.

The Q3 2025 request quantity and the later executed-contract record are shown as
separate source facts. AIIO does not publish their quotient because their
vintages and project scopes differ and it could be misread as a realization
probability or queue-conversion rate.

## Transmission boundary

AESO stated that no new transmission reinforcements or upgrades were required
for its scoped 1,200 MW interim approach through 2028. This does not establish
the needs of larger, later, or differently located loads. AIIO therefore leaves
the additional transmission requirement for the $50 billion counterfactual
null. Locations, connection studies, and a system needs assessment are required
before a physical addition can be stated.
