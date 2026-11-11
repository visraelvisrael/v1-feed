from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import re


def fetch_title(url):
    """Fetch og:title from a V1 article page."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "he-IL,he;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read(8000).decode("utf-8", errors="replace")

        # Try og:title first
        m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            return m.group(1).strip()

        # Try regular title tag
        m = re.search(r'<title>([^<]+)</title>', html)
        if m:
            t = m.group(1).strip()
            # Remove site suffix like " - V1" or " | mako"
            t = re.sub(r'\s*[-|]\s*(V1|mako|וואן).*$', '', t, flags=re.IGNORECASE)
            return t.strip()
    except:
        pass
    return ""


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

    items = []
    n = min(len(videos), len(times), 20)  # limit to 20

    for i in range(n):
        link = links[i] if i < len(links) else ""

        # Fetch real title from article page
        title = fetch_title(link) if link else ""

        # Fallback if fetch failed
        if not title:
            title = f"קליפ {i+1}"

        items.append({
            "title": title,
            "link":  link,
            "cat":   "",
            "time":  times[i],
            "thumb": thumbs[i] if i < len(thumbs) else "",
            "video": videos[i],
            "desc":  "",
        })

    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    return items


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
