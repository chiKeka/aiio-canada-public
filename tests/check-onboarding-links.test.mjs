import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

import {
  slugify,
  extractHeadings,
  verifyDocument,
} from '../scripts/check-onboarding-links.mjs';

test('slugify generates correct markdown heading anchors', () => {
  assert.equal(slugify('Run locally'), 'run-locally');

  assert.equal(
    slugify('Try it in two minutes'),
    'try-it-in-two-minutes'
  );

  assert.equal(
    slugify('Hypothetical $50M school'),
    'hypothetical-50m-school'
  );
});

test('extractHeadings finds all header slugs in content', () => {
  const sample =
    '# Title\n## Section One\n### Sub-Section';

  const headings = extractHeadings(sample);

  assert.equal(headings.has('title'), true);
  assert.equal(headings.has('section-one'), true);
  assert.equal(headings.has('sub-section'), true);
  assert.equal(headings.has('missing'), false);
});

test('verifyDocument verifies valid links, reports missing files and anchors, and skips URLs', () => {
  // Create a temporary directory for testing
  const tmpDir = fs.mkdtempSync(
    path.join(os.tmpdir(), 'link-check-test-')
  );

  try {
    // Create a valid Markdown file
    fs.writeFileSync(
      path.join(tmpDir, 'target.md'),
      '# Target Section\nContent here.\n'
    );

    // Create a valid image
    fs.mkdirSync(path.join(tmpDir, 'images'));

    fs.writeFileSync(
      path.join(tmpDir, 'images', 'pic.png'),
      ''
    );

    const docContent = [
      '# Main Doc',
      '## Local Heading',
      '1. [Valid local anchor](#local-heading)',
      '2. [Valid relative link](target.md)',
      '3. [Valid relative with anchor](target.md#target-section)',
      '4. ![Valid image](images/pic.png)',
      '5. <img src="images/pic.png">',
      '6. [External link](https://github.com/chiKeka)',
      '7. [External mail](mailto:test@example.com)',
      '8. [Broken file](non-existent-file.md)',
      '9. [Broken anchor](#does-not-exist)',
      '10. [Broken foreign anchor](target.md#bad-heading)',
    ].join('\n');

    fs.writeFileSync(
      path.join(tmpDir, 'index.md'),
      docContent
    );

    const errors = verifyDocument(
      'index.md',
      tmpDir
    );

    // Exactly 3 errors are expected:
    // missing file + missing local anchor + missing foreign anchor
    assert.equal(errors.length, 3);

    assert.ok(
      errors.some(
        (e) => e.target === 'non-existent-file.md'
      )
    );

    assert.ok(
      errors.some(
        (e) => e.target === '#does-not-exist'
      )
    );

    assert.ok(
      errors.some(
        (e) => e.target === 'target.md#bad-heading'
      )
    );
  } finally {
    // Remove temporary test files
    fs.rmSync(tmpDir, {
      recursive: true,
      force: true,
    });
  }
});