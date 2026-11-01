"""Tests for the defuddle web_extract provider.

Run with Hermes's own interpreter (it has httpx and the Hermes modules on the path):

    hermes --run-module unittest discover -s plugins/defuddle/tests -t plugins/defuddle/tests -v

They start a throwaway HTTP server on 127.0.0.1 and need `npm ci` to have been run in plugins/defuddle.
Nothing touches the Hermes home. Set DEFUDDLE_LIVE=1 to also fetch one real page.
"""
from __future__ import annotations

import asyncio
import http.server
import importlib.util
import os
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

PLUGIN_DIR = Path(__file__).resolve().parents[1]


def _load_provider():
    spec = importlib.util.spec_from_file_location(
        "web_defuddle", PLUGIN_DIR / "__init__.py", submodule_search_locations=[str(PLUGIN_DIR)])
    assert spec is not None and spec.loader is not None
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["web_defuddle"] = pkg
    spec.loader.exec_module(pkg)
    return sys.modules["web_defuddle.provider"]


provider = _load_provider()

BODY = " ".join(f"Sentence {i} explains how the lethal trifecta lets an attacker steal private data." for i in range(30))
ARTICLE = f"""<!doctype html><html><head><title>The Article Title</title>
<meta name="author" content="Ada Lovelace"></head><body>
<div class="cookie-banner">We use cookies. Accept all cookies?</div>
<nav><a href="/">Home</a> <a href="/about">About</a> <a href="/subscribe">Subscribe to our newsletter</a></nav>
<main><article><h1>The Article Title</h1><p>{BODY}</p><p>See <a href="/next">the follow-up</a>.</p></article></main>
<footer>Copyright 2026. Privacy policy. Terms of service.</footer></body></html>"""
SHELL = """<!doctype html><html><head><title>App</title></head><body><div id="root"></div>
<script src="/bundle.js"></script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    seen_uas: list[tuple[str, str]] = []  # (path, User-Agent) per request

    def log_message(self, format, *args):
        pass

    def _send(self, status, ctype, body: bytes, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        ua = self.headers.get("User-Agent", "")
        Handler.seen_uas.append((self.path, ua))
        if self.path == "/article":
            self._send(200, "text/html; charset=utf-8", ARTICLE.encode())
        elif self.path == "/redirect":
            self._send(302, "text/html", b"", {"Location": "/article"})
        elif self.path == "/prerendered-for-bots":  # JS shell for browsers, real page for bots
            self._send(200, "text/html", (ARTICLE if ua.endswith(" bot") else SHELL).encode())
        elif self.path == "/shell":
            self._send(200, "text/html", SHELL.encode())
        elif self.path == "/doc.pdf":
            self._send(200, "application/pdf", b"%PDF-1.4 fake")
        else:
            self._send(404, "text/html", b"<h1>Not found</h1>")



def plain_client():
    import httpx
    return httpx.AsyncClient(follow_redirects=True, max_redirects=5, timeout=5)


class ProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.seen_uas.clear()
        patcher = mock.patch.object(provider, "_make_client", plain_client)  # the SSRF guard blocks 127.0.0.1
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_extract(self, *paths):
        return asyncio.run(provider.extract_urls([self.base + p for p in paths]))

    def test_article_is_clean_full_markdown(self):
        [r] = self.run_extract("/article")
        self.assertNotIn("error", r)
        self.assertEqual(r["title"], "The Article Title")
        self.assertIn("Sentence 29 explains", r["content"])  # nothing elided
        for chrome in ("Accept all cookies", "Subscribe to our newsletter", "Privacy policy"):
            self.assertNotIn(chrome, r["content"])
        self.assertIn(f"{self.base}/next", r["content"])  # relative links resolved
        self.assertEqual(r["raw_content"], r["content"])
        self.assertEqual(r["metadata"]["sourceURL"], self.base + "/article")
        self.assertEqual(r["metadata"]["author"], "Ada Lovelace")
        self.assertGreaterEqual(r["metadata"]["word_count"], 300)

    def test_redirect_keeps_requested_url_and_records_final(self):
        [r] = self.run_extract("/redirect")
        self.assertNotIn("error", r)
        self.assertEqual(r["url"], self.base + "/redirect")
        self.assertEqual(r["metadata"]["final_url"], self.base + "/article")

    def test_pdf_is_a_per_url_error(self):
        [r] = self.run_extract("/doc.pdf")
        self.assertIn("not an HTML page", r["error"])
        self.assertEqual(r["content"], "")

    def test_http_error_is_a_per_url_error(self):
        [r] = self.run_extract("/missing")
        self.assertIn("HTTP 404", r["error"])

    def test_js_shell_retries_as_bot_then_errors(self):
        [r] = self.run_extract("/shell")
        self.assertIn("needs JavaScript", r["error"])
        uas = [ua for path, ua in Handler.seen_uas if path == "/shell"]
        self.assertEqual(uas, [provider.UA, provider.BOT_UA])

    def test_bot_retry_recovers_prerendered_page(self):
        [r] = self.run_extract("/prerendered-for-bots")
        self.assertNotIn("error", r)
        self.assertIn("Sentence 29 explains", r["content"])

    def test_batch_preserves_order(self):
        results = self.run_extract("/missing", "/article", "/doc.pdf")
        self.assertEqual([r["url"] for r in results], [self.base + p for p in ("/missing", "/article", "/doc.pdf")])
        self.assertEqual([bool(r.get("error")) for r in results], [True, False, True])

    def test_oversized_page_is_refused(self):
        with mock.patch.object(provider, "MAX_BYTES", 100):
            [r] = self.run_extract("/article")
        self.assertIn("larger than 5 MB", r["error"])


class SsrfGuardTest(unittest.TestCase):
    """The real (guarded) client must refuse a live page on 127.0.0.1 that the plain client can read."""

    def test_real_client_refuses_private_addresses(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_address[1]}/article"
        [r] = asyncio.run(provider.extract_urls([url]))
        # Connect-time check, so it covers every redirect hop too, not just the first URL.
        self.assertIn("Blocked request to private/internal address", r["error"])


class RescueTests(unittest.TestCase):
    URLS = ["https://a.example/1", "https://b.example/2.pdf", "https://c.example/3"]

    def run_rescue(self, results, eligible=True):
        calls = []

        def fake_rescue(name, urls, failed):
            calls.append((name, list(urls)))
            return [{"url": u, "title": "rescued", "content": "free tier text", "metadata": {"rescued_from": name}}
                    for u in urls]

        with mock.patch("tools.web_tools_rescue._rescue_eligible", return_value=eligible), \
             mock.patch("tools.web_tools_rescue._rescue_extract", side_effect=fake_rescue):
            merged = asyncio.run(provider.DefuddleExtractProvider()._rescue_partial(self.URLS, results))
        return merged, calls

    def ok(self, url):
        return {"url": url, "title": "t", "content": "c"}

    def err(self, url):
        return {"url": url, "title": "", "content": "", "error": "defuddle: not an HTML page"}

    def test_partial_failure_rescues_only_failed_entries(self):
        merged, calls = self.run_rescue([self.ok(self.URLS[0]), self.err(self.URLS[1]), self.ok(self.URLS[2])])
        self.assertEqual(calls, [("defuddle", [self.URLS[1]])])
        self.assertEqual([m["title"] for m in merged], ["t", "rescued", "t"])

    def test_total_failure_is_left_for_hermes(self):
        merged, calls = self.run_rescue([self.err(u) for u in self.URLS])
        self.assertEqual(calls, [])
        self.assertTrue(all(m.get("error") for m in merged))

    def test_rescue_disabled_keeps_errors(self):
        merged, calls = self.run_rescue([self.ok(self.URLS[0]), self.err(self.URLS[1]), self.ok(self.URLS[2])],
                                        eligible=False)
        self.assertEqual(calls, [])
        self.assertIn("error", merged[1])


class AvailabilityTest(unittest.TestCase):
    def test_available_and_extract_only(self):
        p = provider.DefuddleExtractProvider()
        self.assertTrue(p.is_available(), "run `npm ci` in plugins/defuddle first")
        self.assertTrue(p.supports_extract())
        self.assertFalse(p.supports_search())
        self.assertEqual(p.name, "defuddle")


@unittest.skipUnless(os.environ.get("DEFUDDLE_LIVE"), "set DEFUDDLE_LIVE=1 to fetch a real page")
class LiveTest(unittest.TestCase):
    def test_real_article(self):
        [r] = asyncio.run(provider.extract_urls(["https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/"]))
        self.assertNotIn("error", r)
        self.assertIn("lethal trifecta", r["content"].lower())
        self.assertGreater(len(r["content"]), 8000)


if __name__ == "__main__":
    unittest.main()
