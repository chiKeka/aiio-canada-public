## Evidence or product change

Describe the decision, evidence vintage, and affected publication surfaces.

## Required checks

- [ ] Source identities, URLs, retrieval receipts, and licences are preserved.
- [ ] Observed, inferred, assumed, and scenario values remain distinguishable.
- [ ] No proxy is presented as realized AI construction activity or causal effect.
- [ ] `npm run research:test:public` passes; withheld-source skips remain explicit.
- [ ] `npm run lint` passes.
- [ ] `npm run build` and `npm run build:sites` pass.
- [ ] Generated digest and research-surface manifests reconcile.
- [ ] No frozen release or model parameter changed without its review gate.

## Deployment

Merge only after maintainer review of the exact head and successful relevant checks. Deployment is a separate decision; the live demo is maintained independently of this public snapshot.

## External contribution review

- [ ] Changes to dependencies, executable scripts, tests, configuration and workflows are identified for manual review before execution.
- [ ] No credentials, private source archives, client records or deployment bindings are needed.
- [ ] No workflow permissions or review gates are weakened.
- [ ] The final head SHA and relevant checks are recorded.

See [the external contribution policy](../docs/security/external-contributions.md).
