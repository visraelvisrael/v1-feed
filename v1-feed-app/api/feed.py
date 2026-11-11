from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import re


def scrape_v1():
    url = "https://www.v-1.co.il/"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    items = []

    # The V1 homepage contains structured blocks like:
    # ## [title](link)
    # category
    # 2026-11-11T06:16:50.000Z
    # optional description
    # https://kdsf.akamaized.net/.../master.m3u8

    # Find all blocks anchored by an ISO timestamp followed by a kdsf video URL
    block_pattern = re.compile(
        r'##\s+\[(.+?)\]\((https://www\.v-1\.co\.il/[^\)]+)\)'  # title + link
        r'\s+([^\n]+)\n'                                          # category
        r'\s*(\d{4}-\d{2}-\d{2}T[\d:.Z]+)\s*\n'                # timestamp
        r'(.*?)'                                                   # optional desc
        r'\s*(https://kdsf\.akamaized\.net/[^\s]+master\.m3u8)', # video
        re.DOTALL
    )

    # Thumbnails in order
    thumbs = re.findall(
        r'https://img\.mako\.co\.il/\d{4}/\d{2}/\d{2}/[^\s"\'<>]+?FirstFrame[^\s"\'<>]*?\.jpg',
        html
    )

    thumb_idx = 0
    for m in block_pattern.finditer(html):
        title    = m.group(1).strip()
        link     = m.group(2).strip()
        cat      = m.group(3).strip()
        time_str = m.group(4).strip()
        desc_raw = m.group(5).strip()
        video    = m.group(6).strip()

        # Clean description — skip if it looks like a URL or is too short
        desc = ""
        if desc_raw and not desc_raw.startswith("http") and len(desc_raw) > 10:
            desc = desc_raw[:250]

        thumb = thumbs[thumb_idx] if thumb_idx < len(thumbs) else ""
        thumb_idx += 1

        items.append({
            "title": title,
            "link":  link,
            "cat":   cat,
            "time":  time_str,
            "thumb": thumb,
            "video": video,
            "desc":  desc,
        })

    # Sort newest first
    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    return items[:60]


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

        try:
            items = scrape_v1()
            payload = json.dumps({
                "ok": True,
                "items": items,
                "count": len(items)
            }, ensure_ascii=False)
        except Exception as e:
            payload = json.dumps({
                "ok": False,
                "error": str(e),
                "items": []
            }, ensure_ascii=False)

        self.wfile.write(payload.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def log_message(self, format, *args):
        pass
