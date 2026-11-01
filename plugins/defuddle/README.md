# web-defuddle: a local `web_extract` backend

Hermes's keyless `web_extract` (the free Exa / Parallel / Firecrawl / Keenable tiers) returns
excerpts: sections are cut out and replaced with `...`, and menus and other site chrome come along.
This plugin fetches pages on your own machine and extracts the main content with
[defuddle](https://github.com/kepano/defuddle), so agents get the whole article as clean markdown.
On four test pages it returned 1.4x to 12x as much text, with nothing cut out.

- **Fetching** uses Hermes's SSRF-guarded client. Every connection, including each redirect hop, is
  checked, so a public page can't redirect the agent into `localhost` or your LAN.
- **Results** go through Hermes's normal `web_extract` pipeline: the untrusted-content wrapper,
  truncation with the full text saved to disk, and the result cache.
- **Failures** fall back to the keyless free tier, one URL at a time. A URL fails when it isn't HTML
  (PDFs), returns an HTTP error, is over 5 MB, or yields fewer than 25 words even after a retry with
  defuddle's bot user agent (pages that need JavaScript, consent walls).
- **Search** is unchanged. This plugin only provides extract.

## Install (one profile)

Needs Node, which Hermes already manages in `~/.hermes/tools`.

```bash
dst="${HERMES_HOME:-$HOME/.hermes}/plugins/web/defuddle"    # or ~/.hermes/profiles/<role>/plugins/web/defuddle
mkdir -p "$dst"
rsync -a --delete --exclude node_modules --exclude tests --exclude __pycache__ plugins/defuddle/ "$dst/"
(cd "$dst" && npm ci --omit=dev)
hermes [-p <role>] plugins enable web/defuddle
hermes [-p <role>] config set web.extract_backend defuddle
```

To undo, run `hermes config set web.extract_backend ""` and `hermes plugins disable web/defuddle`.

## Test

```bash
(cd plugins/defuddle && npm ci)
hermes --run-module unittest discover -s plugins/defuddle/tests -t plugins/defuddle/tests -v
DEFUDDLE_LIVE=1 hermes --run-module unittest discover -s plugins/defuddle/tests -t plugins/defuddle/tests   # also fetch one real page
```

## Coupling to watch on Hermes upgrades

The plugin rescues partly failed batches with `tools.web_tools_rescue._rescue_extract`, which is a
private Hermes helper. The import is guarded: if a Hermes release moves it, failed URLs in a mixed
batch just stay failed until an agent retries them on their own. Hermes still rescues batches
where every URL failed. defuddle is pinned to 0.19.6, which still accepts the HTML-string input
`extract.mjs` uses.
