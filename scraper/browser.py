"""
Shared fetching helpers for the DarGlobal and Wasalt scrapers.

Both sites sit behind bot protection (Imperva on darglobal.co.uk, Cloudflare on
wasalt.sa) that only serves pages to a browser that runs JavaScript. Plain
`requests` gets a challenge page, so pages are loaded in a real Chromium
browser through Playwright. Nothing here spoofs a fingerprint or solves a
CAPTCHA: if a site shows an interactive challenge, the page is skipped and the
pipeline keeps the last good snapshot.

Sitemaps are not protected, so URL discovery uses plain HTTP.
"""

import gzip
import json
import logging
import os
import re
import time
from html import unescape
from typing import Any, Dict, Iterable, List, Optional

import requests

logger = logging.getLogger("ScraperBrowser")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


class ScrapeBlocked(RuntimeError):
    """The site served a bot challenge instead of the page."""


# ---------------------------------------------------------------- text helpers
def clean_text(value: Any) -> str:
    """HTML or plain string -> single-spaced plain text."""
    if value is None:
        return ""
    text = unescape(TAG_RE.sub(" ", str(value)))
    return SPACE_RE.sub(" ", text.replace("�", "'")).strip()


def rich_text(blocks: Any) -> str:
    """Strapi rich-text blocks ([{type, children:[{text}]}]) or a string -> plain text."""
    if blocks is None:
        return ""
    if isinstance(blocks, str):
        return clean_text(blocks)
    out: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("text"), str):
                out.append(node["text"])
            for child in node.get("children", []) or []:
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(blocks)
    return clean_text(" ".join(out))


def next_data(html: str) -> Dict[str, Any]:
    """pageProps from a Next.js page (both sites are Next.js)."""
    match = NEXT_DATA_RE.search(html or "")
    if not match:
        raise ScrapeBlocked("page has no __NEXT_DATA__ (likely a bot challenge page)")
    return json.loads(match.group(1)).get("props", {}).get("pageProps", {})


# ------------------------------------------------------------- sitemap helpers
def fetch_sitemap(url: str, timeout: int = 60) -> List[str]:
    """Return every <loc> in a sitemap (handles .xml and .xml.gz)."""
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    body = resp.content
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body.decode("utf-8", "replace"))


# ------------------------------------------------------------- browser session
class BrowserSession:
    """
    One Chromium window per site. The first navigation lets the site's JavaScript
    check finish like it would for any visitor; later pages are fetched from
    inside that same page (same origin, same cookies) to keep it fast.
    """

    def __init__(self, base_url: str, headless: Optional[bool] = None, delay: float = 0.6,
                 timeout_ms: int = 60000):
        self.base_url = base_url.rstrip("/")
        if headless is None:
            env = os.getenv("SCRAPER_HEADLESS")
            if env is not None:
                headless = env.strip().lower() in ("1", "true", "yes")
            else:
                # A visible window is needed for Cloudflare's automatic check;
                # servers without a display fall back to headless.
                headless = os.name != "nt" and not os.getenv("DISPLAY")
        self.headless = headless
        self.delay = delay
        self.timeout_ms = timeout_ms
        self._pw = self._browser = self.page = None

    def __enter__(self) -> "BrowserSession":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # keeps the app usable without Playwright installed
            raise RuntimeError("Playwright is not installed: pip install playwright && "
                               "python -m playwright install chromium") from exc
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        context = self._browser.new_context(locale="en-US", viewport={"width": 1366, "height": 900})
        self.page = context.new_page()
        self.open(self.base_url + "/")
        return self

    def __exit__(self, *exc) -> None:
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._pw:
                self._pw.stop()

    def open(self, url: str) -> str:
        """Navigate the window to a URL and return the rendered HTML."""
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        try:
            # The automatic check normally clears in a few seconds; an interactive one never will.
            self.page.wait_for_function("() => !!document.getElementById('__NEXT_DATA__')",
                                        timeout=min(self.timeout_ms, 25000))
        except Exception as exc:
            raise ScrapeBlocked(f"{url}: site check did not clear ({self.page.title()!r})") from exc
        return self.page.content()

    def get(self, url: str, retries: int = 2) -> str:
        """Fetch a same-site URL's HTML from inside the open page."""
        last: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                result = self.page.evaluate(
                    """async (u) => { const r = await fetch(u, {credentials: 'include'});
                                      return [r.status, await r.text()]; }""", url)
                status, html = result
                time.sleep(self.delay)
                if status == 200 and "__NEXT_DATA__" in html:
                    return html
                if status in (404, 410):
                    raise FileNotFoundError(f"{url}: HTTP {status}")
                last = ScrapeBlocked(f"{url}: HTTP {status}")
                logger.info("retry %s (HTTP %s, attempt %d)", url, status, attempt + 1)
                if status in (403, 429, 503):
                    # Let the site re-check this window, then retry once.
                    self.open(self.base_url + "/")
            except FileNotFoundError:
                raise
            except ScrapeBlocked as exc:
                last = exc
                logger.info("retry %s (%s)", url, exc)
            except Exception as exc:  # network hiccup
                last = exc
                logger.info("retry %s (%s)", url, exc)
            time.sleep(2 * (attempt + 1))
        raise last or ScrapeBlocked(url)

    def get_many(self, urls: Iterable[str]) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for url in urls:
            try:
                out[url] = self.get(url)
            except Exception as exc:
                logger.warning("skip %s: %s", url, exc)
        return out
