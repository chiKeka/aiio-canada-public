/** Local replacements are outside npm advisory coverage; fail closed on identity,
 * byte provenance and every lockfile consumer's actual runtime resolution. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { readFileSync, readdirSync, realpathSync, existsSync } from 'node:fs';
import { dirname, join, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = (path) => JSON.parse(readFileSync(path, 'utf8'));
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex');
const lock = read(join(root, 'package-lock.json'));
const packageManifest = read(join(root, 'package.json'));
assert.ok(lock.packages, 'Modern lockfile package inventory required');
function safeFile(base, name) {
  const path = resolve(base, name);
  assert.ok(path.startsWith(`${base}/`), `Manifest file escapes vendor: ${name}`);
  return path;
}
function enumerate(base, dir = base) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    if (entry.name === 'node_modules') return [];
    const path = join(dir, entry.name);
    assert.ok(!entry.isSymbolicLink(), `Vendor symlink not permitted: ${path}`);
    return entry.isDirectory() ? enumerate(base, path) : [relative(base, path)];
  });
}
function manifestAt(entry) {
  let directory = dirname(realpathSync(entry));
  while (directory !== dirname(directory)) {
    const path = join(directory, 'package.json');
    if (existsSync(path)) return { path, directory, manifest: read(path) };
    directory = dirname(directory);
  }
  throw Error(`No package manifest found for ${entry}`);
}
const forks = [
  { dependency: '@esbuild-kit/core-utils', directory: 'vendor/esbuild-kit-core-utils', name: '@aiio/esm-core-utils-compatible', manifest: 'provenance.json', upstream: '@esbuild-kit/core-utils@3.3.2' },
  { dependency: 'braces', directory: 'vendor/braces-depth-guard', name: '@aiio/braces-depth-guard', manifest: 'patch-manifest.json', upstream: 'braces@3.0.3' },
];
const forkPaths = new Map();
for (const fork of forks) {
  const directory = join(root, fork.directory);
  const packageJson = read(join(directory, 'package.json'));
  const provenance = read(join(directory, fork.manifest));
  assert.equal(packageJson.name, fork.name, 'Fork must have its own identity');
  assert.equal(packageJson.version, '1.0.0');
  assert.equal(packageJson.license, 'MIT');
  assert.ok(readFileSync(join(directory, 'LICENSE'), 'utf8').includes('MIT'), 'Upstream license must be retained');
  assert.ok(provenance.forkFiles && Object.keys(provenance.forkFiles).length >= 5, 'Patched file hash inventory required');
  for (const [name, expected] of Object.entries(provenance.forkFiles)) {
    assert.match(expected, /^[a-f0-9]{64}$/, `Invalid pinned hash for ${name}`);
    assert.equal(hash(safeFile(directory, name)), expected, `Fork byte drift: ${fork.directory}/${name}`);
  }
  const exclusions = new Set([fork.manifest, 'upstream-provenance.json']);
  for (const name of enumerate(directory)) {
    assert.ok(exclusions.has(name) || name in provenance.forkFiles, `Unpinned vendor file: ${fork.directory}/${name}`);
  }
  if (fork.dependency === '@esbuild-kit/core-utils') {
    assert.equal(provenance.upstream, fork.upstream);
    assert.match(provenance.origin, /^https:\/\/registry\.npmjs\.org\/@esbuild-kit\/core-utils\//);
    for (const name of ['dist/index.js', 'dist/index.d.ts', 'LICENSE']) {
      assert.equal(hash(join(directory, name)), provenance.files[name], `Core implementation/license differs from upstream: ${name}`);
    }
    assert.equal(packageJson.dependencies.esbuild, '0.25.12');
  } else {
    const upstream = read(join(directory, 'upstream-provenance.json'));
    assert.equal(upstream.upstreamPackage, 'braces');
    assert.equal(upstream.upstreamVersion, '3.0.3');
    assert.match(upstream.resolved, /^https:\/\/registry\.npmjs\.org\/braces\//);
    assert.equal(provenance.upstreamProvenanceSha256, hash(join(directory, 'upstream-provenance.json')));
    assert.equal(hash(join(directory, 'LICENSE')), upstream.files.LICENSE);
    assert.equal(provenance.maxNesting, 64);
    assert.ok(provenance.forkFiles['upstream.patch'], 'Reviewed upstream patch must be pinned');
  }
  assert.equal((packageManifest.dependencies?.[fork.dependency] ?? packageManifest.devDependencies?.[fork.dependency]), `file:${fork.directory}`, 'Root local dependency missing');
  assert.equal(packageManifest.overrides[fork.dependency], `$${fork.dependency}`, 'Global local override missing');
  const installed = manifestAt(createRequire(join(root, 'package.json')).resolve(fork.dependency));
  assert.equal(installed.manifest.name, fork.name);
  assert.equal(installed.manifest.version, '1.0.0');
  // npm may install a copied package instead of a link. Check runtime bytes too.
  for (const [name, expected] of Object.entries(provenance.forkFiles)) {
    if (existsSync(join(installed.directory, name))) assert.equal(hash(join(installed.directory, name)), expected, `Installed fork differs: ${name}`);
    else assert.ok(['README.md', 'UPSTREAM-README.md', 'upstream.patch', 'upstream-fixtures.json', 'upstream-provenance.json'].includes(name), `Installed implementation missing: ${name}`);
  }
  forkPaths.set(fork.dependency, { directory, name: fork.name, forkFiles: provenance.forkFiles });
}
let consumers = 0;
for (const [location, metadata] of Object.entries(lock.packages)) {
  if (!location.includes('node_modules/')) continue;
  if (/(^|\/)node_modules\/esbuild$/.test(location) && metadata.version) {
    const parts = metadata.version.split('.').map(Number);
    assert.ok(parts[0] > 0 || parts[1] >= 25, `Vulnerable esbuild remains locked: ${location}@${metadata.version}`);
  }
  for (const dependency of ['braces', '@esbuild-kit/core-utils']) {
    if (location.endsWith(`node_modules/${dependency}`)) {
      assert.ok(metadata.link || metadata.name === forkPaths.get(dependency).name || metadata.resolved?.startsWith('file:'), `Registry original remains locked: ${location}`);
    }
  }
  const manifestPath = join(root, location, 'package.json');
  if (!existsSync(manifestPath) && metadata.optional) continue; // Cross-platform optional binaries need not be installed.
  assert.ok(existsSync(manifestPath), `Locked dependency not installed: ${location}`);
  const installed = read(manifestPath);
  assert.ok(!['braces', '@esbuild-kit/core-utils'].includes(installed.name), `Registry original still installed: ${location}`);
  if (/(^|\/)node_modules\/esbuild$/.test(location)) {
    const parts = installed.version.split('.').map(Number);
    assert.ok(parts[0] > 0 || parts[1] >= 25, `Vulnerable esbuild still installed: ${location}@${installed.version}`);
  }
  for (const dependency of ['braces', '@esbuild-kit/core-utils']) {
    if (location.endsWith(`node_modules/${dependency}`)) {
      assert.equal(installed.name, forkPaths.get(dependency).name, `Registry original remains: ${location}`);
      assert.equal(installed.version, '1.0.0');
      for (const [name, expected] of Object.entries(forkPaths.get(dependency).forkFiles)) {
        const runtimeFile = join(dirname(manifestPath), name);
        if (existsSync(runtimeFile)) assert.equal(hash(runtimeFile), expected, `Nested installed fork drift: ${location}/${name}`);
        else assert.ok(['README.md', 'UPSTREAM-README.md', 'upstream.patch', 'upstream-fixtures.json', 'upstream-provenance.json'].includes(name), `Nested implementation missing: ${location}/${name}`);
      }
      assert.ok(metadata.link || metadata.name === installed.name || metadata.resolved?.startsWith('file:'), `Unrecognized locked fork: ${location}`);
    }
    if (installed.dependencies?.[dependency] || installed.optionalDependencies?.[dependency]) {
      const resolved = manifestAt(createRequire(manifestPath).resolve(dependency));
      assert.equal(resolved.manifest.name, forkPaths.get(dependency).name, `${location} loads registry ${dependency}`);
      assert.equal(resolved.manifest.version, '1.0.0');
      for (const [name, expected] of Object.entries(forkPaths.get(dependency).forkFiles)) {
        const runtimeFile = join(resolved.directory, name);
        if (existsSync(runtimeFile)) assert.equal(hash(runtimeFile), expected, `Consumer fork drift: ${location}/${name}`);
        else assert.ok(['README.md', 'UPSTREAM-README.md', 'upstream.patch', 'upstream-fixtures.json', 'upstream-provenance.json'].includes(name), `Consumer implementation missing: ${location}/${name}`);
      }
      consumers++;
      if (dependency === '@esbuild-kit/core-utils') {
        const engine = read(createRequire(join(resolved.directory, 'package.json')).resolve('esbuild/package.json'));
        assert.equal(engine.version, '0.25.12', `${location} loader uses wrong esbuild`);
      }
    }
  }
}
assert.ok(consumers >= 2, 'Expected micromatch and loader consumers not found');
console.log(`Verified local fork identities, licenses, reviewed hashes and ${consumers} locked consumer resolutions. npm audit is supplementary and does not cover these local patches.`);
