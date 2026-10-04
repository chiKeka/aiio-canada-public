# Security remediation options — 2026-10-03

This records local imports, installed dependency paths and official npm registry metadata checked on 2026-10-03. Package manifests and lockfiles are owned by the implementation coordinator; this analysis changes neither. Audit count reduction alone is not proof that application or build behavior is preserved.

## shadcn: CLI removal requires preserving its stylesheet

`shadcn@4.18.0` is not imported by application JavaScript, and no repository package script invokes its CLI. However, `app/globals.css` imports `shadcn/tailwind.css`. Removing the package without replacing this asset breaks a real application dependency. `@shadcn/react` is a separate package used by `components/ui/message-scroller.tsx`; keep it and the checked-in UI components.

A narrow auditable removal path is to copy the exact installed `shadcn/dist/tailwind.css` to a local vendor asset, preserve its MIT license and attribution, record source package/version and SHA-256, update the CSS import, then remove the unused CLI package. Initial stylesheet SHA-256 is `bc7d83425702955b4cb67cb14ede9d603f9d912376d57a2d81d661094d2a782a`. Validate both native and Sites builds and visual/accessibility checks. Component generation would subsequently require an explicitly managed tooling environment; do not silently reintroduce the affected CLI using an unpinned `npx` command.

Moving shadcn to devDependencies retains the vulnerable build tooling and the CSS import. It changes `--omit=dev` classification, not full audit exposure. That is not remediation.

Official [shadcn latest metadata](https://registry.npmjs.org/shadcn/latest) returns 4.21.1, still depending on fast-glob `^3.3.3` and ts-morph `^26.0.0`. Canary 4.2.0-canary.0, rc 4.10.0-rc.674ae44 and beta 0.0.0-beta-20261001093212 tags are not evidence of a supported security fix. The installed paths are:

- shadcn → fast-glob → micromatch → braces.
- shadcn → ts-morph → @ts-morph/common → fast-glob → micromatch → braces.

## vinext: preserve the supported Sites architecture

`vite.config.ts` imports and runs `vinext()`, configures `vinext/server/fetch-handler` as the worker entry, and `tsconfig.json` references `vinext/types`. Package scripts use vinext for Sites build and development. These are real build and alternative runtime integration points, even though native `next start` does not invoke vinext.

Installed `vinext/dist/config/next-config.js` imports `vite-plugin-commonjs` and invokes its transform during configuration loading. Its path is vinext → vite-plugin-commonjs → vite-plugin-dynamic-import → fast-glob → micromatch → braces. Removing or disabling the plugin may break CommonJS config/module interoperability; it cannot be replaced with an inert stub merely to make npm audit pass.

Official [vinext latest metadata](https://registry.npmjs.org/vinext/latest) returns 1.0.1 with vite-plugin-commonjs `^0.10.4`; beta points to older 1.0.0-beta.0. Official [vite-plugin-commonjs metadata](https://registry.npmjs.org/vite-plugin-commonjs/latest) returns 0.10.4 with vite-plugin-dynamic-import `^1.6.0`. Updating to the stable vinext release may be useful independently, but does not remove the affected chain. Retiring Sites would be an architectural scope change, requiring explicit review of deployment configuration and CI; it is not a routine dependency fix.

## braces: no released patch; auditable fork or upstream repair required

[GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) affects braces ≤3.0.3 and lists no patched version. Official [braces latest metadata](https://registry.npmjs.org/braces/latest) returns 3.0.3; [micromatch latest](https://registry.npmjs.org/micromatch/latest) returns 4.0.8 with braces `^3.0.3`.

There is no compatible released update that resolves this leaf. An auditable fork must retain the package API, bound parser and recursive walker nesting, test deeply nested adversarial inputs and existing glob behavior, pin the patched artifact and source hash, and validate all consumers and both builds. A reviewed upstream patch is preferable. Such a fork remains a documented divergence from upstream, and an unchanged upstream package version may still trigger audit; do not suppress that evidence or fabricate a patched release number. Unreviewed substitutes, forced shadcn 1.0.0/vinext 0.0.15 downgrades, or audit configuration exclusions are unsuitable.

## Drizzle: supported prerelease migration versus tested override

`drizzle.config.ts` uses `defineConfig` from drizzle-kit and `db:generate` invokes the CLI. No application import of drizzle-kit was found. Installed drizzle-kit 0.31.10 → @esbuild-kit/esm-loader 2.6.5 → @esbuild-kit/core-utils 3.3.2 → esbuild 0.18.20 is affected by [GHSA-67mh-4wv8-2f99](https://github.com/advisories/GHSA-67mh-4wv8-2f99), affecting esbuild ≤0.24.2. The advisory concerns the development server; installed core-utils calls `transform`/`transformSync`, and no exposed esbuild server was found. This narrows known usage but does not constitute a risk acceptance.

Official [drizzle-kit latest metadata](https://registry.npmjs.org/drizzle-kit/latest) returns 0.31.11 and still depends on `@esbuild-kit/esm-loader ^2.5.5`. Updating only that patch does not remove the old nested esbuild. Official esbuild-kit metadata marks both loader and core-utils deprecated, merged into tsx; their latest releases still retain esbuild `~0.18.20`.

Two concrete paths require different review:

1. **Upstream migration:** current official drizzle-kit rc 1.0.0-rc.4 and beta 1.0.0-beta.22 use jiti `^2.6.1` and esbuild `^0.25.10`, without esbuild-kit. This removes the chain, but is a major prerelease migration rather than a compatible patch. Confirm Drizzle ORM/schema/config compatibility and generate migrations in an isolated fixture without modifying production migration history. Do not adopt it solely for an audit count.
2. **Scoped override:** override only `@esbuild-kit/core-utils`'s esbuild to a released patched version and test its exact `transform`/`transformSync` options plus `db:generate` against isolated SQLite schema fixtures. Esbuild is pre-1.0; changing 0.18 to 0.25 crosses its declared minor constraint and is **not upstream-supported compatibility**. If accepted, document the override and its evidence, retain full audit output, and arrange replacement by a supported loader release/migration. A global esbuild override risks unrelated Vite/tsx consumers and is broader than necessary.

## Acceptance record

Retain production and full dependency audit outputs, lockfile diff, artifact hashes for any vendored patch, clean install results, both builds, DB generator fixtures where relevant, and desktop/mobile browser evidence. Residual findings require upstream remediation or explicit reviewed risk acceptance. No dependency exception or AIIO deployment is approved by this document.
