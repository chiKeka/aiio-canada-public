import fs from 'node:fs';
import path from 'node:path';

// Only check the three onboarding documents from Issue #3
export const DEFAULT_DOCUMENTS = [
  'README.md',
  'CONTRIBUTING.md',
  'docs/project-assessment-walkthrough.md',
];

// Convert a Markdown heading into a GitHub-style anchor
export function slugify(text) {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-');
}

// Find all Markdown headings in a document
export function extractHeadings(content) {
  const headings = new Set();
  const headingRegex = /^#{1,6}\s+(.+)$/gm;

  let match;

  while ((match = headingRegex.exec(content)) !== null) {
    headings.add(slugify(match[1]));
  }

  return headings;
}

// Find Markdown links, Markdown images, and HTML img src paths
export function extractLinks(content) {
  const links = [];
  const lines = content.split('\n');

  lines.forEach((lineText, index) => {
    const lineNum = index + 1;

    // Markdown links and images
    const mdRegex =
      /(?:!\[.*?\]|\[.*?\])\(([^)\s]+)(?:\s+"[^"]*")?\)/g;

    let match;

    while ((match = mdRegex.exec(lineText)) !== null) {
      links.push({
        raw: match[1],
        line: lineNum,
      });
    }

    // HTML <img src="...">
    const htmlImgRegex = /<img[^>]+src=["']([^"']+)["']/gi;

    while ((match = htmlImgRegex.exec(lineText)) !== null) {
      links.push({
        raw: match[1],
        line: lineNum,
      });
    }
  });

  return links;
}

// Verify one document
export function verifyDocument(
  docRelativePath,
  rootDir = process.cwd()
) {
  const errors = [];

  const fullDocPath = path.resolve(
    rootDir,
    docRelativePath
  );

  if (!fs.existsSync(fullDocPath)) {
    return [
      {
        file: docRelativePath,
        line: 1,
        target: docRelativePath,
        message: 'Document does not exist',
      },
    ];
  }

  const docDir = path.dirname(fullDocPath);
  const content = fs.readFileSync(fullDocPath, 'utf8');

  const docHeadings = extractHeadings(content);
  const links = extractLinks(content);

  for (const { raw, line } of links) {
    // Ignore external/non-file links
    if (
      /^(https?:|mailto:|tel:|javascript:|\/\/)/i.test(raw)
    ) {
      continue;
    }

    let filePathPart = raw;
    let fragmentPart = null;

    if (raw.includes('#')) {
      const hashIndex = raw.indexOf('#');

      filePathPart = raw.slice(0, hashIndex);
      fragmentPart = raw.slice(hashIndex + 1);
    }

    // Same-page anchor
    if (!filePathPart && fragmentPart) {
      if (!docHeadings.has(fragmentPart.toLowerCase())) {
        errors.push({
          file: docRelativePath,
          line,
          target: raw,
          message:
            `Heading anchor "#${fragmentPart}" not found in ${docRelativePath}`,
        });
      }

      continue;
    }

    // Local file link
    const targetFullPath = path.resolve(
      docDir,
      filePathPart
    );

    if (!fs.existsSync(targetFullPath)) {
      errors.push({
        file: docRelativePath,
        line,
        target: raw,
        message:
          `Referenced file does not exist: "${filePathPart}"`,
      });

      continue;
    }

    // Check anchor in another Markdown file
    if (
      fragmentPart &&
      targetFullPath.endsWith('.md')
    ) {
      const targetContent = fs.readFileSync(
        targetFullPath,
        'utf8'
      );

      const targetHeadings =
        extractHeadings(targetContent);

      if (
        !targetHeadings.has(
          fragmentPart.toLowerCase()
        )
      ) {
        errors.push({
          file: docRelativePath,
          line,
          target: raw,
          message:
            `Heading anchor "#${fragmentPart}" not found in referenced file "${filePathPart}"`,
        });
      }
    }
  }

  return errors;
}

// Run as a command-line script
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) ===
    path.resolve(
      new URL(import.meta.url).pathname
        .replace(/^\/([A-Za-z]:)/, '$1')
    )
) {
  const filesToCheck =
    process.argv.slice(2).length > 0
      ? process.argv.slice(2)
      : DEFAULT_DOCUMENTS;

  let hasErrors = false;

  console.log(
    `Checking offline links and images in ${filesToCheck.length} onboarding documents...\n`
  );

  for (const doc of filesToCheck) {
    const docErrors = verifyDocument(doc);

    if (docErrors.length === 0) {
      console.log(
        `✅ ${doc}: all links and image references verified`
      );
    } else {
      hasErrors = true;

      console.error(
        `❌ ${doc} (${docErrors.length} errors found):`
      );

      for (const err of docErrors) {
        console.error(
          `    Line ${err.line}: ${err.message}`
        );
      }
    }
  }

  if (hasErrors) {
    process.exit(1);
  } else {
    console.log(
      '\nAll onboarding links and screenshot references verified successfully.'
    );

    process.exit(0);
  }
}