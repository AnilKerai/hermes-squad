"""Defuddle ``web_extract`` provider.

Fetches each URL locally with Hermes's SSRF-guarded httpx client (every connection, including each
redirect hop, is checked against private/internal addresses), then runs ``extract.mjs`` (defuddle) once
per batch to turn the HTML into clean markdown.

A URL fails, per entry, when it isn't HTML (PDFs), is over 5 MB, returns an HTTP error, or still yields
almost no text after a retry with defuddle's bot user agent (a page rendered by JavaScript). Hermes
rescues a batch on the keyless free tier only when EVERY entry failed; for a partly failed batch this
provider rescues the failed entries itself, so one PDF in a batch of three still comes back.
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)

PLUGIN_DIR = Path(__file__).resolve().parent
SCRIPT = PLUGIN_DIR / "extract.mjs"
DEFUDDLE_PKG = PLUGIN_DIR / "node_modules" / "defuddle" / "package.json"

# Same user agents as the defuddle CLI, so sites treat us the way they treat defuddle.md.
UA = "Mozilla/5.0 (compatible; Defuddle/1.0; +https://defuddle.md)"
BOT_UA = UA + " bot"
BOT_UA_DOMAINS = ("github.com",)  # serve server-rendered pages to bots
HTML_TYPES = ("text/html", "application/xhtml+xml")
MAX_BYTES = 5 * 1024 * 1024
FETCH_TIMEOUT_S = 20.0
PARSE_TIMEOUT_S = 60.0
MIN_WORDS = 25  # below this a page is treated as empty (JS shell, consent wall, error page)


class PageError(Exception):
    """A per-URL failure reported in that URL's result entry."""


def _make_client():
    """SSRF-guarded async client. Module-level so tests can swap in a plain client for a localhost server."""
    from tools.url_safety import create_ssrf_safe_async_client

    return create_ssrf_safe_async_client(follow_redirects=True, max_redirects=10, timeout=FETCH_TIMEOUT_S)


def _node() -> str | None:
    try:
        from hermes_constants import find_node_executable

        found = find_node_executable("node")
    except Exception:  # older Hermes or no managed Node: fall back to PATH
        found = None
    return found or shutil.which("node")


def _initial_ua(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return BOT_UA if any(host == d or host.endswith("." + d) for d in BOT_UA_DOMAINS) else UA


def _ok(url: str, final_url: str, page: dict[str, Any]) -> dict[str, Any]:
    title, content = page.get("title", ""), page.get("content", "")
    meta = {"sourceURL": url, "title": title, "extractor": "defuddle", "word_count": page.get("wordCount", 0)}
    if final_url and final_url != url:
        meta["final_url"] = final_url
    for key in ("author", "published", "site", "description"):
        if page.get(key):
            meta[key] = page[key]
    return {"url": url, "title": title, "content": content, "raw_content": content, "metadata": meta}


def _err(url: str, error: str) -> dict[str, Any]:
    return {"url": url, "title": "", "content": "", "error": f"defuddle: {error}"}


async def _fetch(client, url: str, ua: str) -> tuple[str, str]:
    """Return (final_url, html). Raises PageError for anything that isn't a usable HTML page."""
    headers = {"User-Agent": ua, "Accept": "text/html,application/xhtml+xml"}
    async with client.stream("GET", url, headers=headers) as resp:
        if resp.status_code >= 400:
            raise PageError(f"HTTP {resp.status_code}")
        ctype = resp.headers.get("content-type", "").lower()
        if not any(t in ctype for t in HTML_TYPES):
            raise PageError(f"not an HTML page (content-type: {ctype or 'unknown'})")
        declared = resp.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > MAX_BYTES:
            raise PageError("page larger than 5 MB")
        body = bytearray()
        async for chunk in resp.aiter_bytes():
            body += chunk
            if len(body) > MAX_BYTES:
                raise PageError("page larger than 5 MB")
        return str(resp.url), bytes(body).decode(resp.encoding or "utf-8", errors="replace")


async def _fetch_all(urls: list[str], ua_for: Callable[[str], str]) -> list[tuple[str, str] | str]:
    """(final_url, html) per URL, or an error string, in input order."""
    async def one(client, url):
        try:
            return await _fetch(client, url, ua_for(url))
        except PageError as exc:
            return str(exc)
        except Exception as exc:  # network errors, SSRF refusals, timeouts
            return f"fetch failed: {type(exc).__name__}: {exc}"[:300]

    async with _make_client() as client:
        return list(await asyncio.gather(*(one(client, u) for u in urls)))


async def _parse(pages: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Run extract.mjs over [{url, html}] and return its per-page results, same order."""
    if not pages:
        return []
    node = _node()
    if not node:
        return [{"error": "node not found"} for _ in pages]
    proc = await asyncio.create_subprocess_exec(
        node, str(SCRIPT), cwd=str(PLUGIN_DIR),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(json.dumps(pages).encode()), PARSE_TIMEOUT_S)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return [{"error": f"parse timed out after {PARSE_TIMEOUT_S:.0f}s"} for _ in pages]
    if proc.returncode != 0:
        msg = err.decode(errors="replace").strip().splitlines()[-1:] or ["no output"]
        return [{"error": f"extract.mjs exited {proc.returncode}: {msg[0][:200]}"} for _ in pages]
    parsed = json.loads(out)
    if len(parsed) != len(pages):
        return [{"error": "extract.mjs returned the wrong number of results"} for _ in pages]
    return parsed


def _thin(page: dict[str, Any]) -> bool:
    return not page.get("error") and page.get("wordCount", 0) < MIN_WORDS


async def extract_urls(urls: list[str]) -> list[dict[str, Any]]:
    """Fetch and parse *urls*; one result entry per URL, in order. No rescue."""
    results: list[dict[str, Any] | None] = [None] * len(urls)
    fetched = await _fetch_all(urls, _initial_ua)
    todo = []
    for i, (url, got) in enumerate(zip(urls, fetched)):
        if isinstance(got, str):
            results[i] = _err(url, got)
        else:
            todo.append((i, got[0], got[1]))
    parsed = await _parse([{"url": final, "html": html} for _, final, html in todo])

    # Pages that came back (nearly) empty: try once more as a bot, which some sites serve pre-rendered.
    retry = [(i, final) for (i, final, _), page in zip(todo, parsed) if _thin(page) and _initial_ua(urls[i]) != BOT_UA]
    retried: dict[int, tuple[str, dict[str, Any]]] = {}
    if retry:
        refetched = await _fetch_all([urls[i] for i, _ in retry], lambda _u: BOT_UA)
        ok = [(i, got) for (i, _), got in zip(retry, refetched) if not isinstance(got, str)]
        reparsed = await _parse([{"url": got[0], "html": got[1]} for _, got in ok])
        for (i, got), page in zip(ok, reparsed):
            retried[i] = (got[0], page)

    for (i, final, _), page in zip(todo, parsed):
        if i in retried and not retried[i][1].get("error") and retried[i][1].get("wordCount", 0) > page.get("wordCount", 0):
            final, page = retried[i]
        if page.get("error"):
            results[i] = _err(urls[i], page["error"])
        elif _thin(page):
            results[i] = _err(urls[i], f"only {page.get('wordCount', 0)} words extracted "
                                       "(the page probably needs JavaScript or shows a consent/bot wall)")
        else:
            results[i] = _ok(urls[i], final, page)
    return [r for r in results if r is not None]


class DefuddleExtractProvider(WebSearchProvider):
    @property
    def name(self) -> str:
        return "defuddle"

    @property
    def display_name(self) -> str:
        return "Defuddle (local)"

    def is_available(self) -> bool:
        return DEFUDDLE_PKG.is_file() and SCRIPT.is_file() and _node() is not None

    def supports_search(self) -> bool:
        return False

    def supports_extract(self) -> bool:
        return True

    async def extract(self, urls: list[str], **kwargs: Any) -> list[dict[str, Any]]:
        results = await extract_urls(list(urls))
        return await self._rescue_partial(list(urls), results)

    async def _rescue_partial(self, urls: list[str], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Send the failed entries of a partly failed batch to Hermes's keyless rescue.

        A wholly failed batch is left alone: Hermes rescues that itself. The rescue helpers are private
        Hermes internals, so the import is guarded; on a Hermes that moved them, failed entries simply
        stay failed. Rescued entries carry ``metadata.rescued_from = "defuddle"``.
        """
        failed = [i for i, r in enumerate(results) if r.get("error")]
        if not failed or len(failed) == len(results):
            return results
        try:
            from tools.web_tools_rescue import _rescue_eligible, _rescue_extract
        except Exception as exc:
            logger.debug("defuddle: keyless rescue unavailable: %s", exc)
            return results
        if not _rescue_eligible(self):
            return results
        sub_urls = [urls[i] for i in failed]
        rescued = await asyncio.to_thread(_rescue_extract, self.name, sub_urls, [results[i] for i in failed])
        if len(rescued) != len(failed):
            return results
        merged = list(results)
        for i, entry in zip(failed, rescued):
            merged[i] = entry
        return merged
