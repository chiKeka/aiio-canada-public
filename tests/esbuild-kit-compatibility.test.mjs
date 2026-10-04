import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import vm from 'node:vm';
const require = createRequire(import.meta.url);
const core = require('@esbuild-kit/core-utils');
const corePath = require.resolve('@esbuild-kit/core-utils');
const coreRequire = createRequire(corePath);
const esbuildManifest = JSON.parse(readFileSync(coreRequire.resolve('esbuild/package.json')));

function commonJS(code, globals = {}) {
  const evaluatedModule = { exports: {} };
  vm.runInNewContext(code, { module: evaluatedModule, exports: evaluatedModule.exports, require, ...globals });
  return evaluatedModule.exports;
}

function sourceMap(result, original) {
  assert.equal(result.map.version, 3);
  assert.ok(result.map.sources.some((p) => p.endsWith(original)));
  assert.ok(result.map.sourcesContent.some((s) => s.includes('answer')));
  assert.ok(result.map.mappings.length > 0);
}

test('installed loader dependency uses the exact patched transform engine', () => {
  assert.equal(esbuildManifest.version, '0.25.12');
  assert.equal(typeof core.transformSync, 'function');
  assert.equal(typeof core.transform, 'function');
});

test('sync TypeScript CommonJS transform preserves values, exports and source maps', () => {
  const result = core.transformSync('interface Item { value:number }; const item:Item={value:40}; export const answer:number=item.value+2;', '/tmp/compat-answer.ts');
  assert.equal(commonJS(result.code).answer, 42);
  sourceMap(result, 'compat-answer.ts');
});

test('async ESM transform preserves top-level await and executable exports', async () => {
  const result = await core.transform('const value:number=await Promise.resolve(40); export const answer:number=value+2;', '/tmp/compat-answer.mts', { format: 'esm', target: 'esnext' });
  const resultModule = await import(`data:text/javascript;base64,${Buffer.from(result.code).toString('base64')}`);
  assert.equal(resultModule.answer, 42);
  sourceMap(result, 'compat-answer.mts');
});

test('JSX compiler options invoke supplied JSX factory and preserve children', () => {
  const result = core.transformSync('export const answer=<span id="x">hello</span>;', '/tmp/compat-answer.tsx', { jsxFactory: 'makeElement' });
  const evaluatedModule = commonJS(result.code, { makeElement: (tag, props, child) => ({ tag, props, child }) });
  assert.equal(evaluatedModule.answer.tag, 'span');
  assert.equal(evaluatedModule.answer.props.id, 'x');
  assert.equal(evaluatedModule.answer.child, 'hello');
  sourceMap(result, 'compat-answer.tsx');
});

test('explicit transform options control replacement constants and target syntax', () => {
  const result = core.transformSync('export const answer:number=BUILD_VALUE; export const label=({name:"ok"} as {name:string}).name;', '/tmp/compat-answer.ts', { define: { BUILD_VALUE: '42' }, target: 'es2018' });
  const evaluatedModule = commonJS(result.code);
  assert.equal(evaluatedModule.answer, 42);
  assert.equal(evaluatedModule.label, 'ok');
});

test('dynamic import interop unwraps transpiled CJS namespace while preserving native ESM', async () => {
  const folder = mkdtempSync(join(tmpdir(), 'aiio-core-interop-'));
  try {
    writeFileSync(join(folder, 'value.cjs'), 'module.exports = {__esModule:true, answer:42};');
    writeFileSync(join(folder, 'value.mjs'), 'export const answer=43;');
    const cjsUrl = pathToFileURL(join(folder, 'value.cjs')).href;
    const esmUrl = pathToFileURL(join(folder, 'value.mjs')).href;
    const original = `export const cjs=await import(${JSON.stringify(cjsUrl)}); export const esm=await import(${JSON.stringify(esmUrl)});`;
    const rewritten = core.transformDynamicImport(join(folder, 'entry.mjs'), original);
    assert.ok(rewritten);
    const entry = await import(`data:text/javascript;base64,${Buffer.from(rewritten.code).toString('base64')}`);
    // Node 22+ may expose module.exports as a second namespace key, so the
    // upstream one-default-only rule deliberately retains that native namespace.
    const cjsExports = entry.cjs.answer === undefined ? entry.cjs.default : entry.cjs;
    assert.equal(cjsExports.answer, 42);
    assert.equal(cjsExports.__esModule, true);
    const synthetic = core.transformDynamicImport('/tmp/interop.js', 'import("synthetic")');
    const expression = synthetic.code.replace('import("synthetic")', 'Promise.resolve({default:{__esModule:true,answer:44}})');
    const unwrapped = await vm.runInNewContext(expression);
    assert.equal(unwrapped.answer, 44);
    assert.equal(entry.esm.answer, 43);
    assert.equal(rewritten.map.version, 3);
    assert.equal(core.transformDynamicImport('/tmp/plain.js', 'const answer = 42;'), undefined);
  } finally { rmSync(folder, { recursive: true, force: true }); }
});

test('malformed TypeScript fails instead of silently returning executable output', () => {
  assert.throws(() => core.transformSync('export const answer: number = ;', '/tmp/compat-invalid.ts'));
});
