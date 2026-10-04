# Research-surface provenance manifest

## Why it exists

AIIO Canada has two legitimate states during development:

1. the immutable public release bundle; and
2. the evolving research workspace that can expose newer, still-withheld
   diagnostics before the next publication gate.

The workspace must not describe every visible artifact as a member of the
frozen release. `public/data/research-surface.json` therefore hash-locks every
supplemental JSON artifact imported by the current website and identifies the
frozen release underneath it.

## Contract

The manifest records each artifact path, evidence role and SHA-256 hash plus an
aggregate manifest hash. Its publication boundary always states that the
workspace is not a frozen public release, is not decision-grade, does not
authorize an AI-attributable effect or project-cost forecast, and is not a
deployment authorization.

The manifest does not copy artifacts into a release, alter the release
manifest, or change website values. It makes the mixed lifecycle explicit and
machine-checkable.

## Operating commands

```bash
npm run research-surface:build
npm run program:audit
```

The quality workflow rebuilds the manifest and fails on any uncommitted drift.
The program-readiness audit independently reconciles it. Adding or removing a
website data import requires updating the declared artifact inventory and
reviewing its evidence role.
