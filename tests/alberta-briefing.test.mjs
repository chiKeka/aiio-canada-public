import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { unzipSync, strFromU8 } from 'fflate';
import { buildAlbertaBriefing } from '../lib/alberta-briefing.mjs';
const read = (name) =>
  JSON.parse(
    fs.readFileSync(
      new URL(`../public/data/construction/${name}.json`, import.meta.url),
    ),
  );
const input = {
  projects: read('projects'),
  benchmarks: read('benchmarks'),
  evidence: read('briefing'),
  manifest: read('manifest'),
};
const template = fs.readFileSync(
  new URL(
    '../assets/presentations/alberta-briefing-template.pptx',
    import.meta.url,
  ),
);
const generate = (value) =>
  buildAlbertaBriefing(template, value, new Date('2026-09-06T12:00:00Z'));
const text = (files, path) => strFromU8(files[path]);
test('generates complete editable deck with chart workbooks and source notes', () => {
  const result = generate(input),
    files = unzipSync(result.bytes);
  assert.equal(result.slideCount, 16);
  assert.equal(
    Object.keys(files).filter((p) =>
      /^ppt\/slides\/charts\/chart\d+\.xml$/.test(p),
    ).length,
    5,
  );
  assert.match(text(files, 'ppt/slides/slide3.xml'), /49.01/);
  assert.match(text(files, 'ppt/notesSlides/notesSlide6.xml'), /statcan/);
  assert.match(text(files, 'ppt/slides/slide10.xml'), /8–78 weeks/);
  assert.match(text(files, 'ppt/slides/slide6.xml'), /Not published/);
  for (const [p, v] of Object.entries(files))
    if (/^ppt\/slides\/slide\d+\.xml$/.test(p)) {
      assert.doesNotMatch(
        strFromU8(v),
        /platform|construction-presentation-inputs|Canada pipeline/i,
      );
    }
  fs.writeFileSync('/tmp/alberta-generated-briefing.pptx', result.bytes);
});
test('changed costs update title, native chart cache and embedded workbook', () => {
  const changed = structuredClone(input);
  changed.projects.find((p) => p.cost === 15e9).cost = 16e9;
  const files = unzipSync(generate(changed).bytes);
  assert.match(text(files, 'ppt/slides/slide3.xml'), /50.01/);
  assert.match(text(files, 'ppt/slides/charts/chart2.xml'), /<c:v>16<\/c:v>/);
  const workbook = unzipSync(
    files['ppt/embeddings/chart-data-snapshot-002.xlsx'],
  );
  assert.match(text(workbook, 'xl/worksheets/sheet1.xml'), /<v>16<\/v>/);
});
test('added records paginate without dropping names or losing package relationships', () => {
  const changed = structuredClone(input);
  for (let i = 0; i < 11; i++)
    changed.projects.push({
      ...changed.projects[0],
      id: `extra-${i}`,
      name: `Extra project ${i}`,
      cost: null,
      end: null,
    });
  const result = generate(changed),
    files = unzipSync(result.bytes);
  assert.equal(result.slideCount, 18);
  assert.match(text(files, 'ppt/slides/slide18.xml'), /Extra project 10/);
  assert.match(text(files, 'ppt/_rels/presentation.xml.rels'), /slide18.xml/);
  assert.match(text(files, '[Content_Types].xml'), /notesSlide18.xml/);
});
test('missing costs and dates remain unavailable and shortened inventory removes old appendices', () => {
  const changed = structuredClone(input);
  changed.projects = changed.projects
    .slice(0, 2)
    .map((p) => ({ ...p, cost: null, end: null }));
  const result = generate(changed),
    files = unzipSync(result.bytes);
  assert.equal(result.slideCount, 14);
  assert.equal(files['ppt/slides/slide15.xml'], undefined);
  assert.match(text(files, 'ppt/slides/slide3.xml'), /costs are unavailable/);
  assert.equal(files['ppt/slides/charts/chart2.xml'], undefined);
  assert.equal(files['ppt/embeddings/chart-data-snapshot-002.xlsx'], undefined);
  assert.match(text(files, 'ppt/slides/slide4.xml'), /Not published/);
});
test('unpublished benchmarks, mixed periods and invalid observations fail closed', () => {
  const changed = structuredClone(input);
  changed.benchmarks.parameters.find(
    (p) => p.id === 'recruitment_requirement_to2035',
  ).status = 'analyst_assumption';
  assert.throws(() => generate(changed), /published benchmark/);
  const mixed = structuredClone(input);
  mixed.evidence.prices[0].period_end = '2027-03-31';
  assert.throws(() => generate(mixed), /Mixed price/);
  const invalid = structuredClone(input);
  invalid.projects[0].cost = NaN;
  assert.throws(() => generate(invalid), /Invalid project/);
});
