## Evidence or product change

Describe the decision, evidence vintage, and affected publication surfaces.

## Required checks

- [ ] Source identities, URLs, retrieval receipts, and licences are preserved.
- [ ] Observed, inferred, assumed, and scenario values remain distinguishable.
- [ ] No proxy is presented as realized AI construction activity or causal effect.
- [ ] `npm run research:test` passes.
- [ ] `npm run lint` passes.
- [ ] `npm run build` and `npm run build:sites` pass.
- [ ] Generated digest and research-surface manifests reconcile.
- [ ] No frozen release or model parameter changed without its review gate.

## Deployment

Merge only after the quality gate succeeds. Merging to `main` triggers the Vercel production deployment.
