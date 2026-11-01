// Reads a JSON array of {url, html} on stdin; writes a JSON array of results, same order, on stdout.
// Each result is {title, content, description, author, published, site, wordCount} or {error}.
// Fetching happens in Python (provider.py) so the SSRF guard covers every redirect; this only parses.
import { Defuddle } from 'defuddle/node';

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const pages = JSON.parse(Buffer.concat(chunks).toString('utf8'));

const results = [];
for (const { url, html } of pages) {
  try {
    // An HTML string (not a Document) makes defuddle apply its own linkedom polyfills and set the
    // base URL, exactly as its CLI does. String input is deprecated for defuddle 1.x; the version is
    // pinned in package.json.
    const r = await Defuddle(html, url, { markdown: true });
    results.push({
      title: r.title || '',
      content: r.content || '',
      description: r.description || '',
      author: r.author || '',
      published: r.published || '',
      site: r.site || '',
      wordCount: r.wordCount || 0,
    });
  } catch (err) {
    results.push({ error: `defuddle failed: ${err?.message || err}` });
  }
}
process.stdout.write(JSON.stringify(results));
