# Local esbuild-kit compatibility fork

This private fork retains the MIT-licensed implementation of `@esbuild-kit/core-utils@3.3.2` byte-for-byte. Only package identity and its esbuild dependency change: the legacy `~0.18.20` dependency becomes patched `0.25.12`. This is a project-maintained compatibility patch, not an upstream-endorsed release.

The implementation calls `transformSync`, `transform` and `version`; it does not start an esbuild server. Regression checks cover CommonJS and ESM TypeScript transforms, JSX, tsconfig compiler settings, dynamic imports, source maps, and offline Drizzle migration generation. `provenance.json` records upstream hashes. CI verifies retained code hashes and the installed dependency identity, alongside the unmodified npm audit. No advisory is ignored.

Revisit this fork when supported Drizzle releases remove the deprecated loader. Keep its source-map-support dependency under the ordinary registry audit.
