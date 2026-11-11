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

    # Extract thumbnails
    thumbs = re.findall(r'https://img\.mako\.co\.il/[^\s"\'<>]+?FirstFrame[^\s"\'<>]*\.jpg', html)

    # Extract video URLs
    videos = re.findall(r'https://kdsf\.akamaized\.net/[^\s"\'<>]+?master\.m3u8', html)

    # Extract article links
    links = re.findall(r'https://www\.v-1\.co\.il/[a-z0-9_\-/]+/shorts-[a-z0-9]+\.htm', html)

    # Extract titles from h2 tags
    titles_raw = re.findall(r'<h2[^>]*>\s*<a[^>]*>([^<]+)</a>\s*</h2>', html)
    if not titles_raw:
        # try another pattern
        titles_raw = re.findall(r'##\s+\[([^\]]{5,200})\]', html)

    # Extract categories
    cats_raw = re.findall(r'<span[^>]*class="[^"]*category[^"]*"[^>]*>([^<]+)</span>', html)
    if not cats_raw:
        cats_raw = re.findall(r'\n([^\n]{2,20})\n\n\d{4}-\d{2}-\d{2}', html)

    # Extract timestamps
    times_raw = re.findall(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)', html)
    # deduplicate while preserving order
    seen = set()
    times_unique = []
    for t in times_raw:
        if t not in seen:
            seen.add(t)
            times_unique.append(t)

    # Extract descriptions (text between timestamp and video url in markdown-like structure)
    # Pattern: timestamp \n\n description \n\n video_url
    desc_pattern = re.compile(
        r'\d{4}-\d{2}-\d{2}T[\d:.Z]+\s*\n+\s*([^\n]{20,400}?)\s*\n+\s*https://kdsf',
        re.DOTALL
    )
    descs = []
    for m in desc_pattern.finditer(html):
        d = m.group(1).strip()
        if len(d) > 15:
            descs.append(d)
        else:
            descs.append("")

    # Build items — use the minimum length across all lists
    n = min(len(titles_raw), len(links), len(videos), len(times_unique))

    for i in range(n):
        items.append({
            "title": titles_raw[i].strip(),
            "link":  links[i] if i < len(links) else "",
            "cat":   cats_raw[i].strip() if i < len(cats_raw) else "",
            "time":  times_unique[i] if i < len(times_unique) else "",
            "thumb": thumbs[i] if i < len(thumbs) else "",
            "video": videos[i] if i < len(videos) else "",
            "desc":  descs[i][:250] if i < len(descs) else "",
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
