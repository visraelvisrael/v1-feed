from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import re

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": "https://www.v-1.co.il/",
}


def fetch_url(url, max_bytes=500000, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(max_bytes).decode("utf-8", errors="replace")


def scrape_v1():
    html = fetch_url("https://www.v-1.co.il/")

    if BS4_OK:
        return scrape_with_bs4(html)
    else:
        return scrape_with_regex(html)


def scrape_with_bs4(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for art in soup.select("section[class*=SeoArticles] article"):
        a      = art.find("a")
        h2     = art.find("h2")
        t      = art.find("time")
        ps     = art.find_all("p", recursive=False)
        video  = art.find("video")
        source = art.find("source")

        title  = h2.get_text(strip=True) if h2 else ""
        desc   = ps[1].get_text(strip=True) if len(ps) > 1 else ""
        cat    = ps[0].get_text(strip=True) if ps else ""
        link   = a.get("href") if a else "https://www.v-1.co.il"
        time_  = t.get("datetime") if t else ""
        thumb  = video.get("poster") if video else ""
        video_ = source.get("src") if source else ""

        if not video_:
            continue

        items.append({
            "title": title or f"קליפ",
            "desc":  desc if (desc and desc != title) else "",
            "cat":   cat,
            "time":  time_,
            "link":  link,
            "thumb": thumb,
            "video": video_,
        })

    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    return items[:60]


def scrape_with_regex(html):
    # Fallback if bs4 not available
    thumbs = re.findall(r'https://img\.mako\.co\.il/[^\s"\'<>]+?FirstFrame[^\s"\'<>]*?\.jpg', html)
    videos = re.findall(r'https://kdsf\.akamaized\.net/[^\s"\'<>]+?master\.m3u8', html)
    links  = re.findall(r'https://www\.v-1\.co\.il/[a-z0-9_\-/]+/shorts-[a-z0-9]+\.htm', html)
    times  = list(dict.fromkeys(re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z', html)))

    items = []
    n = min(len(videos), len(times))
    for i in range(n):
        items.append({
            "title": f"קליפ {i+1}",
            "desc":  "",
            "cat":   "",
            "time":  times[i],
            "link":  links[i] if i < len(links) else "https://www.v-1.co.il",
            "thumb": thumbs[i] if i < len(thumbs) else "",
            "video": videos[i],
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
