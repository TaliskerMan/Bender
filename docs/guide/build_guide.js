/**
 * Author: Chuck Talk, <chuck@nordheim.online>
 * Project: Bender
 * Purpose: Hardened user-guide PDF builder with canonical path containment and linear-time parsers.
 * Updated: 2026-11-15
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { marked } from 'marked';
import { chromium } from 'playwright';

const DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = fs.realpathSync(path.resolve(DIR, '..', '..'));
const ALLOWED_EXTENSIONS = new Set(['.md', '.png', '.pdf']);
const CALLOUT_KINDS = ['Note', 'Tip', 'Important', 'Warning'];

/**
 * Resolves and validates that a candidate file path stays strictly within REPO_ROOT
 * and carries an expected file extension.
 *
 * @param {string | undefined} rawInput Optional CLI path override resolved from caller CWD.
 * @param {string} fallbackRelative Default path relative to DIR.
 * @param {boolean} mustExist Whether the target file must already exist on disk.
 * @returns {string} Canonical validated path.
 */
function resolveContainedPath(rawInput, fallbackRelative, mustExist = true) {
  const candidate = rawInput
    ? path.resolve(process.cwd(), String(rawInput))
    : path.resolve(DIR, fallbackRelative);
  const ext = path.extname(candidate).toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    throw new Error(`Disallowed file extension for guide build path: ${ext}`);
  }

  const parentDir = fs.realpathSync(path.dirname(candidate));
  const canonicalTarget = mustExist
    ? fs.realpathSync(candidate)
    : path.join(parentDir, path.basename(candidate));

  const relativeToRoot = path.relative(REPO_ROOT, canonicalTarget);
  if (relativeToRoot.startsWith('..') || path.isAbsolute(relativeToRoot)) {
    throw new Error(`Path traversal rejected outside repository root: ${canonicalTarget}`);
  }
  return canonicalTarget;
}

/**
 * Parses top-of-file key:value metadata headers in O(n) time without backtracking regexes.
 *
 * @param {string} rawMarkdown Raw markdown source text.
 * @returns {{ meta: Record<string, string>, markdownBody: string }}
 */
function parseFrontMatter(rawMarkdown) {
  const meta = {};
  const lines = rawMarkdown.split('\n');
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].endsWith('\r')
      ? lines[index].slice(0, -1)
      : lines[index];
    const colonIndex = line.indexOf(':');
    if (colonIndex <= 0) {
      break;
    }
    const key = line.slice(0, colonIndex).trim();
    if (!/^\w+$/.test(key)) {
      break;
    }
    meta[key] = line.slice(colonIndex + 1).trim();
    index += 1;
  }

  return {
    meta,
    markdownBody: lines.slice(index).join('\n'),
  };
}

/**
 * Strips HTML tags in linear O(n) time without regex backtracking.
 *
 * @param {string} input Input string that may contain angle-bracket markup.
 * @returns {string} Plain text with tags removed.
 */
function stripHtmlTags(input) {
  let output = '';
  let insideTag = false;
  for (const ch of String(input)) {
    if (ch === '<') {
      insideTag = true;
    } else if (ch === '>') {
      insideTag = false;
    } else if (!insideTag) {
      output += ch;
    }
  }
  return output;
}

/**
 * Removes empty table headers (`<thead><tr><th></th>...</tr></thead>`) in O(n) time.
 *
 * @param {string} html Rendered HTML string.
 * @returns {string} HTML without empty table header blocks.
 */
function removeEmptyTableHeaders(html) {
  const openTag = '<thead>';
  const closeTag = '</thead>';
  let result = '';
  let cursor = 0;

  while (cursor < html.length) {
    const start = html.indexOf(openTag, cursor);
    if (start === -1) {
      result += html.slice(cursor);
      break;
    }
    const end = html.indexOf(closeTag, start + openTag.length);
    if (end === -1) {
      result += html.slice(cursor);
      break;
    }
    result += html.slice(cursor, start);
    const inner = html.slice(start + openTag.length, end);
    if (stripHtmlTags(inner).trim().length > 0) {
      result += html.slice(start, end + closeTag.length);
    }
    cursor = end + closeTag.length;
  }

  return result;
}

/**
 * Adds callout classes to blockquotes starting with `<strong>Note:</strong>` etc.
 *
 * @param {string} html Rendered HTML string.
 * @returns {string} HTML with styled callout blockquotes.
 */
function styleCalloutBlockquotes(html) {
  let updated = html;
  for (const kind of CALLOUT_KINDS) {
    const lower = kind.toLowerCase();
    const needle = `<p><strong>${kind}:</strong>`;
    updated = updated
      .split(`<blockquote>\n${needle}`)
      .join(`<blockquote class="${lower}">\n${needle}`)
      .split(`<blockquote>${needle}`)
      .join(`<blockquote class="${lower}">${needle}`);
  }
  return updated;
}

/**
 * Numbers `<h2>` sections and builds the table of contents in linear O(n) time.
 *
 * @param {string} html Rendered HTML string.
 * @returns {{ html: string, tocHtml: string }}
 */
function injectHeadingIdsAndBuildToc(html) {
  const toc = [];
  let sectionNum = 0;
  let result = '';
  let cursor = 0;

  while (cursor < html.length) {
    const h2Start = html.indexOf('<h2', cursor);
    if (h2Start === -1) {
      result += html.slice(cursor);
      break;
    }
    const openEnd = html.indexOf('>', h2Start + 3);
    const closeStart = openEnd === -1 ? -1 : html.indexOf('</h2>', openEnd + 1);
    if (openEnd === -1 || closeStart === -1) {
      result += html.slice(cursor);
      break;
    }

    result += html.slice(cursor, h2Start);
    const innerText = html.slice(openEnd + 1, closeStart);
    sectionNum += 1;
    const sectionId = `sec${sectionNum}`;
    toc.push(`<li><span class="num">${sectionNum}</span>${innerText}</li>`);
    result += `<h2 id="${sectionId}"><span class="num">${sectionNum}</span>${innerText}</h2>`;
    cursor = closeStart + 5;
  }

  return { html: result, tocHtml: toc.join('') };
}

const mdPath = resolveContainedPath(process.argv[2], 'Bender_User_Guide.md', true);
const iconPath = resolveContainedPath(process.argv[3], '../../data/bender.png', true);
const outPath = resolveContainedPath(process.argv[4], '../Bender_User_Guide.pdf', false);
const primaryLogoPath = path.resolve(DIR, 'logo.png');
const logoPath = fs.existsSync(primaryLogoPath)
  ? resolveContainedPath(undefined, 'logo.png', true)
  : resolveContainedPath(undefined, '../../data/noln.png', true);

const rawSource = fs.readFileSync(mdPath, 'utf8');
const { meta, markdownBody } = parseFrontMatter(rawSource);
const iconB64 = fs.readFileSync(iconPath).toString('base64');
const logoB64 = fs.readFileSync(logoPath).toString('base64');

const rawHtml = marked.parse(markdownBody, { mangle: false, headerIds: true });
const withoutEmptyHeaders = removeEmptyTableHeaders(String(rawHtml));
const withCallouts = styleCalloutBlockquotes(withoutEmptyHeaders);
const { html: bodyHtml, tocHtml } = injectHeadingIdsAndBuildToc(withCallouts);

const cleanTitle = stripHtmlTags(meta.title || 'Bender');
const cleanSubtitle = stripHtmlTags(meta.subtitle || 'Installation and User Guide');
const cleanVersion = stripHtmlTags(meta.version || '0.1.15');
const cleanPlatforms = stripHtmlTags(meta.platforms || 'Linux (GNOME)');

const documentHtml = `<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: Letter; margin: 0.8in 0.85in 0.9in 0.85in; }
:root { --navy:#0E1E4A; --blue:#1F5FE6; --ink:#1f2937; --muted:#5b6475; --rule:#dce3ee; --tint:#eef3fc; }
* { box-sizing: border-box; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; color: var(--ink); font-size: 10.5pt; line-height: 1.5; margin: 0; }
.cover { page-break-after: always; height: 9.2in; display: flex; flex-direction: column; justify-content: space-between; }
.cover .top img { height: 46px; }
.cover .mid img.icon { width: 150px; height: 150px; object-fit: contain; margin-bottom: 28px; }
.cover h1 { font-size: 34pt; line-height: 1.1; color: var(--navy); margin: 0 0 10px; }
.cover .sub { font-size: 15pt; color: var(--muted); margin: 0 0 24px; }
.cover .meta { border-top: 3px solid var(--blue); padding-top: 14px; font-size: 10pt; color: var(--muted); }
.cover .meta b { color: var(--ink); }
.toc { page-break-after: always; }
.toc h2 { border: none; }
.toc ol { list-style: none; padding: 0; margin: 0; }
.toc li { padding: 7px 0; border-bottom: 1px solid var(--rule); font-size: 11.5pt; }
.num { display: inline-block; min-width: 36px; color: var(--blue); font-weight: 700; }
h2 { font-size: 17pt; color: var(--navy); margin: 30px 0 10px; padding-bottom: 6px; border-bottom: 2px solid var(--rule); page-break-after: avoid; }
h2:not(:first-of-type) { page-break-before: always; }
h3 { font-size: 12.5pt; color: var(--navy); margin: 20px 0 6px; page-break-after: avoid; }
h4 { font-size: 10.5pt; margin: 14px 0 4px; page-break-after: avoid; }
p { margin: 0 0 9px; }
ul, ol { margin: 0 0 10px; padding-left: 22px; }
li { margin: 3px 0; }
code { font-family: 'DejaVu Sans Mono', Menlo, monospace; font-size: 9pt; background: var(--tint); padding: 1px 4px; border-radius: 3px; }
pre { background: var(--navy); color: #eef3fc; padding: 11px 14px; border-radius: 6px; font-size: 8.8pt; line-height: 1.45; overflow-wrap: anywhere; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; }
table { width: 100%; border-collapse: collapse; margin: 6px 0 14px; font-size: 9.5pt; page-break-inside: avoid; }
th { text-align: left; background: var(--tint); color: var(--navy); padding: 6px 8px; border-bottom: 2px solid var(--rule); }
td { padding: 6px 8px; border-bottom: 1px solid var(--rule); vertical-align: top; }
blockquote { margin: 10px 0 14px; padding: 9px 14px; border-left: 4px solid var(--blue); background: var(--tint); border-radius: 0 6px 6px 0; page-break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
blockquote.warning, blockquote.important { border-left-color: #c2410c; background: #fff4ec; }
strong { color: var(--navy); }
</style></head><body>
<section class="cover">
  <div class="top"><img src="data:image/png;base64,${logoB64}" alt="Nordheim Online"></div>
  <div class="mid">
    <img class="icon" src="data:image/png;base64,${iconB64}" alt="${cleanTitle}">
    <h1>${cleanTitle}</h1>
    <p class="sub">${cleanSubtitle}</p>
  </div>
  <div class="meta">
    <b>Version</b> ${cleanVersion} &nbsp;·&nbsp; <b>Platforms</b> ${cleanPlatforms} &nbsp;·&nbsp; <b>Updated</b> November 2026<br>
    Nordheim Online, LLC · nordheim.online · support@nordheim.online
  </div>
</section>
<section class="toc"><h2 style="page-break-before:auto">Contents</h2><ol>${tocHtml}</ol></section>
${bodyHtml}
</body></html>`;

const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.setContent(documentHtml, { waitUntil: 'load' });
  await page.pdf({
    path: outPath,
    format: 'Letter',
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: `<div style="font-family:Arial;font-size:8px;color:#6a7385;width:100%;padding:0 0.85in;display:flex;justify-content:space-between;"><span>${cleanTitle} · ${cleanVersion}</span><span class="pageNumber"></span></div>`,
    margin: { top: '0.8in', bottom: '0.9in', left: '0.85in', right: '0.85in' },
  });
  console.log('wrote', outPath);
} finally {
  await browser.close();
}
