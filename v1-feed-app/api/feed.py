from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error
import json
import re
from html.parser import HTMLParser


class V1Parser(HTMLParser):
    """Parse V1 homepage and extract feed items."""

    def __init__(self):
        super().__init__()
        self.items = []
        self._current = {}
        self._in_h2 = False
        self._in_time = False
        self._in_p = False
        self._capture_text = False
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "article" or (tag == "div" and "shorts-item" in attrs.get("class", "")):
            self._current = {}

        if tag == "h2":
            self._in_h2 = True
            self._capture_text = True
            self._current["_title_buf"] = ""

        if tag == "time":
            self._in_time = True
            dt = attrs.get("datetime", "")
            if dt:
                self._current["time"] = dt

        if tag == "p" and not self._current.get("desc"):
            self._in_p = True
            self._capture_text = True
            self._current["_desc_buf"] = ""

        if tag == "a" and attrs.get("href", "").startswith("https://www.v-1.co.il"):
            if not self._current.get("link"):
                self._current["link"] = attrs["href"]

        if tag == "img":
            src = attrs.get("src", "")
            if "mako.co.il" in src and not self._current.get("thumb"):
                self._current["thumb"] = src

        if tag == "source":
            src = attrs.get("src", "")
            if "akamaized" in src and not self._current.get("video"):
                self._current["video"] = src

    def handle_endtag(self, tag):
        if tag == "h2":
            self._in_h2 = False
            self._capture_text = False
            if self._current.get("_title_buf"):
                self._current["title"] = self._current.pop("_title_buf").strip()

        if tag == "time":
            self._in_time = False

        if tag == "p":
            self._in_p = False
            self._capture_text = False
            if self._current.get("_desc_buf"):
                self._current["desc"] = self._current.pop("_desc_buf").strip()

    def handle_data(self, data):
        if self._in_h2 and "_title_buf" in self._current:
            self._current["_title_buf"] += data
        if self._in_p and "_desc_buf" in self._current:
            self._current["_desc_buf"] += data


def scrape_v1():
    """Fetch V1 homepage and extract feed items via regex (more reliable than HTML parser for this site)."""
    url = "https://www.v-1.co.il/"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    items = []

    # Extract each article/item block by finding h2 anchors with v-1.co.il links
    # Pattern: ## [title](link)\ncategory\nISO_time\ndesc\nvideo_url
    
    # Find all h2 sections
    h2_pattern = re.compile(
        r'##\s+\[([^\]]+)\]\((https://www\.v-1\.co\.il/[^\)]+)\)\s*\n+'
        r'([^\n]+)\s*\n+'          # category
        r'(\d{4}-\d{2}-\d{2}T[\d:.Z]+)\s*\n+'  # time
        r'(.*?)\s*\n+'             # description (optional)
        r'(https://kdsf[^\s]+)',   # video url
        re.DOTALL
    )

    for m in h2_pattern.finditer(html):
        title = m.group(1).strip()
        link = m.group(2).strip()
        cat = m.group(3).strip()
        time_str = m.group(4).strip()
        desc = m.group(5).strip()
        video = m.group(6).strip()
        items.append({
            "title": title,
            "link": link,
            "cat": cat,
            "time": time_str,
            "desc": desc if len(desc) < 300 else desc[:300] + "…",
            "video": video,
            "thumb": "",
        })

    # Extract thumbnails from img tags
    thumb_pattern = re.compile(r'!\[\]\((https://img\.mako\.co\.il/[^\)]+FirstFrame[^\)]*)\)')
    thumbs = thumb_pattern.findall(html)

    # Assign thumbs by order
    for i, item in enumerate(items):
        if i < len(thumbs):
            item["thumb"] = thumbs[i]

    # Sort by time descending
    def time_key(x):
        return x.get("time", "")
    items.sort(key=time_key, reverse=True)

    return items[:60]


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # CORS headers — allow any origin so your frontend can call this
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

        try:
            items = scrape_v1()
            payload = json.dumps({"ok": True, "items": items, "count": len(items)}, ensure_ascii=False)
        except Exception as e:
            payload = json.dumps({"ok": False, "error": str(e), "items": []}, ensure_ascii=False)

        self.wfile.write(payload.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # silence default logging
