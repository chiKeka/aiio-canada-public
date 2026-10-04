# Alberta briefing export

The construction workspace now generates an editable PowerPoint at `/api/briefing`. The Downloads page links to the same export. The approved Alberta deck supplies the layouts, colours, native tables and charts; the server fills the slides and chart workbooks from published evidence on each request. No external service or desktop presentation runtime is needed on the server.

The current evidence produces 16 slides: landscape, reported investments and completion years, construction packages, Alberta workforce observations and published recruitment forecast, construction component price changes, other capital projects, external procurement benchmarks, qualitative schedule/cost pathways, mitigation priorities and the complete project appendix. No scenario settings enter this briefing. Existing conditional scenario JSON and quarterly CSV exports remain separate.

## Updating evidence

Run `npm run construction:publish` after updating the canonical project inventory, research benchmark register or labour, price and capital model-run files. This publishes Alberta-only briefing inputs with source-file hashes and updates the construction manifest. Rebuild/deploy to expose the new snapshot. Generation does not fetch new research or assert that old observations are current. Source dates remain visible; detailed references and input hashes are in speaker notes.

The generator recalculates aggregates and chart/workbook values. Investment and completion overview slides display up to seven costs and six schedules respectively, with disclosure when truncated. Every project appears in the paginated appendix. Null values remain unpublished; scenarios and transfer benchmarks cannot be promoted into observed scalar facts. Published US procurement ranges retain their transfer-benchmark designation.

## Boundaries

This automates the approved briefing, not open-ended causal research. Resource intersections, schedule/cost pathways and mitigations are reviewed editorial text. It does not measure available Alberta crews, supplier spare throughput, material quantities, project delays or data-centre-attributable cost premiums. New evidence domains, changed forecast horizons, unusually long names or much larger charts require template/editorial review. The template has a maximum inventory guard of 700 records.

## Validation

`npm run test:briefing` covers editable package generation, evidence changes in native chart caches and Excel workbooks, appendix growth and shrinkage, missing data and invalid/unpublished inputs. The existing 11 construction-model tests remain applicable. `node scripts/briefing-workflow-test.mjs` checks the local browser download, failure/retry behaviour and narrow viewport.

The generated deck passed the presentation package integrity validator and was rendered with Artifact Tool and bundled LibreOffice for visual inspection. Type checking, targeted lint and the production build passed; the build trace includes the PPTX template. The local route returns an attachment with the evidence date and slide count. These checks do not claim native Microsoft PowerPoint testing or production deployment.

Update: automatic refresh and request-time loading supersede the manual snapshot delivery described above. See [Alberta overview refresh](alberta-overview-refresh.md) for source cadences, review boundaries and activation.
