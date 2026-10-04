# Frozen narrow planning validation packet

`data/reviews/planning_validation_packet_v0.1.json` makes the existing Alberta
benchmark, full-schedule comparison, permit analyst review, source files and
implementation hashes reviewable together. It authorizes source auditing,
assumption sensitivity and retrospective diagnostics only. It does not authorize
project cost/delay estimates, causal attribution or fiscal commitments.

Reproduce or check from the repository root:

```sh
PYTHONPATH=research/src python3 research/scripts/freeze_planning_validation.py --check
```

The existing contract's explicit provisional thresholds are embedded verbatim:
eight held-out quarters, at least 5% MAE improvement over baseline, MAE at most
2 percentage points, subgroup MAE ratio at most 1.1, ten independently linked
events, point-in-time vintages, interval coverage and width checks, and independent
review. These thresholds require review; they are not retrospective authorization.
The combined v0.2 proxy worsens MAE by approximately 2.35%. Its held-out rows
are checked for strictly ordered training cutoff, forecast origin and target,
and unique market/asset/quarter keys. Known reused test quarters remain exploratory.

Project-only and permit-only arms provide source-removal sensitivity. There is
only one costed construction project, so project removal cannot demonstrate
population generalization; individual-project leave-one-out remains unassessed.
No new validation claim is inferred from these diagnostic comparisons.

The overlap resolver accepts exclusion only when a permit is evidence-confirmed
as included in the same project's budget scope. Candidate facility identity is
insufficient. Duplicate links, invalid amounts, unknown identifiers, absent scope
evidence and incompatible permit/project amounts fail validation. The packet
computes conservative union bounds for the retained costed project and reviewed
permits; these are sums of reported estimate proxies across different dates,
not time-aligned expenditure, AI-specific investment, or fiscal impacts. Unknown
links remain unresolved and the frozen model is not silently deduplicated.

Milestone alignment accepts dated construction-start and completion evidence;
permit issuance does not establish construction timing. No CAL-3 milestone
receipt is supplied in this packet, so timing stays unassessed. Even a dated
milestone does not itself validate quarterly expenditure allocation.

A reviewer should resolve cited budget-scope overlap, supply construction
milestones and publication vintages, assess the locked baseline comparisons
and thresholds, and delimit supported use. Bind any future reviewer receipt to
the frozen packet's byte hash and input manifest. The packet contains no reviewer
identity or verdict and transmits nothing to third parties. Historical blocked
review records in `program-gates.json` are preserved.
