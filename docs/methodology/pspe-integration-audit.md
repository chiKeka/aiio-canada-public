# PSPE/S3 integration audit

## Role in AIIO Canada

The graph-based programme-simulation method is the conceptual
starting point for the analysis engine, not a complete Observatory
architecture. AIIO Canada independently implements a bounded adaptation of its
documented graph and propagation concepts while adding source provenance,
scenario governance, calibration, temporal resolution and public
explainability.

## Source-lineage status

Historical methodological-source receipts support conceptual inheritance, not code reproduction. The source materials and upstream implementation are not bundled in this public snapshot. Source hashes remain as provenance; they do not establish public access, code equivalence or redistribution permission. No local research folders or private repository identities are disclosed.

Accordingly, AIIO does not claim a code fork, exact reproduction or verified
behavioural equivalence to unavailable PSPE engine source. The generated
lineage report hash-locks five specific concept-to-AIIO mappings and the tests
that support each claim. If the original repository becomes available, it must
enter a separate comparison review before this status changes.

## Reusable concepts

- Directed graphs connecting decisions, activities, resources and outcomes.
- Signed effects and explicit propagation paths.
- Absorption/damping to prevent unconstrained cascading.
- Flow-oriented metrics for dense dependency networks.
- Sensitivity analysis across uncertain edge parameters.
- Case-study pattern: encode a domain system, apply shocks, trace affected nodes and interpret critical paths.

## Known limitations that must not be inherited

1. **Dense-graph compression.** Conventional centrality measures converge in dense networks and can cease to discriminate important nodes. AIIO will emphasize mechanism-specific flow, exposure and bottleneck measures.
2. **Degenerate cascade-origin ranking.** Prior methodological notes describe
   an HS2 workflow that row-normalized propagation and then ranked origins by
   conserved total mass, producing equivalent scores. The underlying engine
   source is not locally available for independent code verification. AIIO therefore
   does not reproduce or use that ranking construction and tests its own graph
   invariants on synthetic graphs.
3. **Edge semantics changed across prototypes.** Valence, threat and influence were used differently. AIIO defines one edge ontology and migrates explicitly.
4. **Positive and negative effects were sometimes pooled.** Netting can hide simultaneous upside and downside. AIIO retains positive, negative and absolute pathways separately.
5. **Absorption dominates results.** Damping is a material assumption, so it requires domain-specific ranges, sensitivity plots and disclosure.
6. **Temporal, Bayesian and calibration layers were incomplete or untested.** These are new workstreams, not capabilities to claim from the source repository.

## AIIO graph contract

Every node requires: stable ID, type, label, geography, unit where applicable, valid time and provenance state.

Every edge requires: stable ID, source and target, mechanism type, sign, weight or distribution, lag, scope condition, evidence reference, confidence, author and version.

Every result requires: baseline version, scenario version, code version, parameter set, random seed where relevant, output unit/index definition and traceable contributing paths.

## First engine implementation

The v0.2 engine implements deterministic signed propagation with explicit lag, absorption and node-level state retention. It preserves positive, negative and absolute contributions, rejects self-loops and directed cycles, and records calendar-year paths. Low, central and high cases co-move declared weights and retention; they are structural cases, not confidence intervals.

Sensitivity covers normalization denominators at 0.5× and 2×, absorption at ±0.10, local capture at 0.40/0.72/0.90, low/high retention and joint lower-/higher-pressure diagnostics. A separate four-run Alberta suite operationalizes the S3 **Stress-Test Nodes/Ties** step by isolating front-loaded timing, constrained timing and high local capture against a staggered reference. Validation covers identity, zero shock, sign, path, state decay, absorption monotonicity, multi-shock additivity, signed-path accounting, mass bounds on unbranched paths, self-loops, cycles, determinism, committed golden runs and cross-variant invariant checks. Monte Carlo and empirical probability distributions remain future calibration work and are not claimed.

Physical quantities such as MW, worker-hours and dollars are not mixed with dimensionless propagation scores. The first power overlay is an independent MW artifact with separate annual-energy and peak-demand factors; it is not a conversion from capex.
