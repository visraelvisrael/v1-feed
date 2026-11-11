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
            "Referer": "https://www.google.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    thumbs = re.findall(r'https://img\.mako\.co\.il/[^\s"\'<>]+?FirstFrame[^\s"\'<>]*?\.jpg', html)
    videos = re.findall(r'https://kdsf\.akamaized\.net/[^\s"\'<>]+?master\.m3u8', html)
    links  = re.findall(r'https://www\.v-1\.co\.il/[a-z0-9_\-/]+/shorts-[a-z0-9]+\.htm', html)
    times  = list(dict.fromkeys(re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z', html)))

    # Try to get titles from markdown links
    titles = re.findall(r'##\s+\[([^\]]{3,300})\]\(https://www\.v-1\.co\.il', html)

    items = []
    n = min(len(videos), len(times))

    for i in range(n):
        if i < len(titles):
            title = titles[i].strip()
        else:
            # Use link slug as title fallback
            if i < len(links):
                parts = links[i].rstrip('/').split('/')
                slug = parts[-2] if len(parts) >= 2 else parts[-1]
                slug = re.sub(r'[-_]', ' ', slug)
                slug = re.sub(r'\d{4,}', '', slug).strip()
                title = slug if len(slug) > 3 else f"קליפ {i+1}"
            else:
                title = f"קליפ {i+1}"

        items.append({
            "title": title,
            "link":  links[i] if i < len(links) else "https://www.v-1.co.il",
            "cat":   "",
            "time":  times[i],
            "thumb": thumbs[i] if i < len(thumbs) else "",
            "video": videos[i],
            "desc":  "",
        })

    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    return items[:60]


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
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
        pass
