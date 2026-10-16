// Builds a Nordheim Online user guide PDF from Markdown.
// Usage: node build_guide.js <guide.md> <icon.png> <out.pdf>
// Front matter (first lines):  title: / subtitle: / version: / platforms:
const fs = require('fs');
const path = require('path');
const { marked } = require('marked');
const { chromium } = require('playwright');

const [, , MD, ICON, OUT] = process.argv;
let src = fs.readFileSync(MD, 'utf8');
const meta = {};
while (/^(\w+):\s*(.*)\n/.test(src)) {
  const m = src.match(/^(\w+):\s*(.*)\n/);
  meta[m[1]] = m[2];
  src = src.slice(m[0].length);
}
const iconB64 = fs.readFileSync(ICON).toString('base64');
const logoB64 = fs.readFileSync(path.join(__dirname, 'logo.png')).toString('base64');

// Callouts: lines starting with "> **Note:**" etc. render as styled blockquotes.
let body = marked.parse(src, { mangle: false, headerIds: true });
body = body.replace(/<thead>\s*<tr>(\s*<th[^>]*>\s*<\/th>)+\s*<\/tr>\s*<\/thead>/g, '');
body = body.replace(/<blockquote>\s*<p><strong>(Note|Tip|Important|Warning):<\/strong>/g,
  (m, k) => `<blockquote class="${k.toLowerCase()}"><p><strong>${k}:</strong>`);

// Table of contents from h2s
const toc = [];
let n = 0;
body = body.replace(/<h2([^>]*)>(.*?)<\/h2>/g, (m, attrs, txt) => {
  n += 1;
  const id = 'sec' + n;
  toc.push(`<li><span class="num">${n}</span>${txt}</li>`);
  return `<h2 id="${id}"><span class="num">${n}</span>${txt}</h2>`;
});

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
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
  <div class="top"><img src="data:image/png;base64,${logoB64}"></div>
  <div class="mid">
    <img class="icon" src="data:image/png;base64,${iconB64}">
    <h1>${meta.title}</h1>
    <p class="sub">${meta.subtitle}</p>
  </div>
  <div class="meta">
    <b>Version</b> ${meta.version} &nbsp;·&nbsp; <b>Platforms</b> ${meta.platforms} &nbsp;·&nbsp; <b>Updated</b> October 2026<br>
    Nordheim Online, LLC · nordheim.online · support@nordheim.online
  </div>
</section>
<section class="toc"><h2 style="page-break-before:auto">Contents</h2><ol>${toc.join('')}</ol></section>
${body}
</body></html>`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'load' });
  await page.pdf({
    path: OUT, format: 'Letter', printBackground: true, displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: `<div style="font-family:Arial;font-size:8px;color:#6a7385;width:100%;padding:0 0.85in;display:flex;justify-content:space-between;"><span>${meta.title.replace(/<[^>]+>/g, '')} · ${meta.version}</span><span class="pageNumber"></span></div>`,
    margin: { top: '0.8in', bottom: '0.9in', left: '0.85in', right: '0.85in' },
  });
  await browser.close();
  console.log('wrote', OUT);
})();
