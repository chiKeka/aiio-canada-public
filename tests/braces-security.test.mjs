import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const braces = require('../vendor/braces-depth-guard');
const parser = require('../vendor/braces-depth-guard/lib/parse');
const walkers = Object.fromEntries(['compile','expand','stringify'].map(name => [name,require(`../vendor/braces-depth-guard/lib/${name}`)]));
const syntaxGuard = error => error instanceof SyntaxError && !(error instanceof RangeError) && /fixed limit|Cyclic|fixed node/.test(error.message);
const nested = (n, left='{',right='}') => left.repeat(n)+'x'+right.repeat(n);
function astChain(depth) {
 const root={type:'root',nodes:[]};let node=root;
 for(let i=0;i<depth;i++){const child={type:'paren',nodes:[],parent:node};node.nodes.push(child);node=child;}
 node.nodes.push({type:'text',value:'x',parent:node});return root;
}
test('all public methods reject deeply nested brace/paren/mixed patterns below maxLength', () => {
 const patterns=[nested(3000),nested(3000,'(',')'),'{('.repeat(1500)+'x'+')}'.repeat(1500),'{'.repeat(3000)+'x'];
 for(const pattern of patterns){assert.ok(pattern.length<10000);
  for(const method of ['parse','compile','expand','stringify','create'])assert.throws(()=>braces[method](pattern,{maxDepth:Infinity,depthLimit:false,rangeLimit:false}),syntaxGuard);
  assert.throws(()=>braces(pattern),syntaxGuard);
  assert.throws(()=>braces([pattern],{expand:true}),syntaxGuard);
  assert.throws(()=>parser(pattern),syntaxGuard);
 }
});
test('fixed64 parser boundary includes both brace and paren containers', () => {
 for(const [left,right] of [['{','}'],['(',')']]) {
  assert.doesNotThrow(()=>braces.stringify(nested(64,left,right)));
  assert.throws(()=>braces.parse(nested(65,left,right),{maxDepth:99999}),syntaxGuard);
 }
 assert.doesNotThrow(()=>braces.compile('{('.repeat(32)+'x'+')}'.repeat(32)));
 assert.throws(()=>braces.parse('{('.repeat(33)+'x'+')}'.repeat(33)),syntaxGuard);
});
test('direct public and lib AST walkers validate before recursion', () => {
 for(const name of ['compile','expand','stringify']) {
  assert.throws(()=>braces[name](astChain(5000)),syntaxGuard);
  assert.throws(()=>walkers[name](astChain(5000)),syntaxGuard);
  assert.doesNotThrow(()=>walkers[name](astChain(64)));
 }
});
test('nodes cycles reject safely; legal parent and prev cycles remain compatible', () => {
 for(const name of ['compile','expand','stringify']) {
  const root={type:'root',nodes:[]};root.nodes.push(root);
  assert.throws(()=>braces[name](root),syntaxGuard);
  assert.throws(()=>walkers[name](root),syntaxGuard);
  const ast=braces.parse('a/{b,c}/d');
  assert.doesNotThrow(()=>walkers[name](ast));
  const leaf={type:'text',value:'safe'};leaf.parent=leaf;leaf.prev=leaf;
  assert.doesNotThrow(()=>walkers[name]({type:'root',nodes:[leaf]}));
 }
});
test('expand parent loops are bounded separately from permitted backreferences', () => {
 const root={type:'root',nodes:[]};const node={type:'paren',nodes:[{type:'text',value:'x'}]};node.parent=node;root.nodes.push(node);
 assert.throws(()=>walkers.expand(root),syntaxGuard);
});
test('iterative validation has bounded work even for shared DAGs', () => {
 for(const name of ['compile','expand','stringify']) {
  let node={type:'text',value:'x'};
  for(let i=0;i<18;i++)node={type:'paren',nodes:[node,node]};
  assert.throws(()=>walkers[name]({type:'root',nodes:[node]}),syntaxGuard);
 }
});
test('normal ranges nesting escaping quotes and option behavior match captured upstream', () => {
 const fixture=JSON.parse(readFileSync(new URL('../vendor/braces-depth-guard/upstream-fixtures.json',import.meta.url)));
 for(const row of fixture.fixtures) for(const [method,expected] of Object.entries(row.results)) {
  const actual=method==='default'?braces(row.pattern,row.options):braces[method](row.pattern,row.options);
  assert.deepEqual(actual,expected,`${method}: ${row.pattern} ${JSON.stringify(row.options)}`);
 }
});
test('existing range and length limits still reject excessive inputs', () => {
 assert.throws(()=>braces.expand('{1..100000}'),RangeError);
 assert.throws(()=>braces.parse('x'.repeat(65537)),SyntaxError);
 assert.deepEqual(braces.expand('{1..3}',{rangeLimit:3}),['1','2','3']);
});
