from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import re
import threading

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": "https://www.v-1.co.il/",
}


def fetch_url(url, max_bytes=8000, timeout=5):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(max_bytes).decode("utf-8", errors="replace")


def fetch_title(url, results, idx):
    """Fetch title and store in results[idx]."""
    try:
        html = fetch_url(url, max_bytes=5000, timeout=4)
        if "Radware" in html or "Block Page" in html:
            results[idx] = ""
            return
        m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']{5,200})["\']', html)
        if m:
            results[idx] = m.group(1).strip()
            return
        m = re.search(r'<title>([^<]{5,200})</title>', html)
        if m:
            t = re.sub(r'\s*[-|]\s*(V1|וואן|mako|קשת).*$', '', m.group(1), flags=re.IGNORECASE)
            results[idx] = t.strip()
            return
    except:
        pass
    results[idx] = ""


def scrape_v1():
    html = fetch_url("https://www.v-1.co.il/", timeout=10)

    thumbs = re.findall(r'https://img\.mako\.co\.il/[^\s"\'<>]+?FirstFrame[^\s"\'<>]*?\.jpg', html)
    videos = re.findall(r'https://kdsf\.akamaized\.net/[^\s"\'<>]+?master\.m3u8', html)
    links  = re.findall(r'https://www\.v-1\.co\.il/[a-z0-9_\-/]+/shorts-[a-z0-9]+\.htm', html)
    times  = list(dict.fromkeys(re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z', html)))
    md_titles = re.findall(r'##\s+\[([^\]]{3,200})\]\(https://www\.v-1\.co\.il', html)

    n = min(len(videos), len(times), 20)

    # Fetch titles in parallel using threads
    title_results = [""] * n
    threads = []
    for i in range(n):
        if i < len(md_titles):
            title_results[i] = md_titles[i].strip()
        elif i < len(links):
            t = threading.Thread(target=fetch_title, args=(links[i], title_results, i))
            t.daemon = True
            threads.append(t)
            t.start()

    # Wait max 7 seconds for all threads
    for t in threads:
        t.join(timeout=7)

    items = []
    for i in range(n):
        title = title_results[i] or f"קליפ {i+1}"
        items.append({
            "title": title,
            "link":  links[i] if i < len(links) else "",
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
