# Construction workspace implementation — 6 September 2026

Route: `/construction`. Linked from the navigation, scenario, methods and downloads pages.

Delivered: 19 existing Alberta core phase records; 36 benchmark/assumption entries from 13 sources; 10 formulas; editable 3/5/10-year quarterly cost-to-labour scenarios; recurring fiscal capital envelopes and calibrated 4/5-year cohorts; conditional capacity gaps; supplier lead-time exposure; separate user-entered delay escalation; CSV and JSON presentation exports with input and model SHA-256 fingerprints.

Refresh the public evidence snapshot with `python3 scripts/build-construction-inputs.py`. It copies the research register and requirements and converts the existing project CSV; it does not fetch new evidence or promote calibrated model parameters. Run it after model edits so the exported model fingerprint remains accurate.

Validation: 11 model/provenance tests passed using `node --experimental-strip-types --test tests/construction-model.test.mjs`; TypeScript and targeted lint passed; the production build generated all 14 pages; the local construction route returned HTTP 200. Interactive browser/visual testing was not performed.

Local build limitation: this checkout's warm Webpack cache repeatedly caused `WasmHash._updateWithBuffer` to fail. Moving `.next/cache/webpack` to a temporary backup allowed a complete clean-cache build. No dependency or global build-configuration change was made. Recheck this cache issue if a subsequent incremental production build fails; the validated source builds with a fresh cache.

Boundaries: the initial screen selects no projects. Costs and dates require explicit scenario selection; missing costs require entry. Package mix, labour fractions, loaded wages, public construction scope and constant available FTE are analyst assumptions. Public and DC work currently share the same provisional package mix. Other private construction and industrial maintenance are omitted from background demand. Hours outside the selected horizon are retained. The existing national inventory remains incomplete. Actual unit-rate estimating, physical quantity take-offs, measured contractor capacity, supplier throughput and resource-constrained critical-path delays remain future extensions. The escalation illustration uses an entered delay and cannot be described as a delay predicted by this model.

This implementation is available in the local preview. It has not been deployed to Vercel and does not change evidence/publication gates.
