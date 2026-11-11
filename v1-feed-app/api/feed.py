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

    return html


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/api/debug":
            # Return raw HTML snippet for debugging
            try:
                html = scrape_v1()
                # Return first 5000 chars + counts of key patterns
                thumbs = re.findall(r'img\.mako\.co\.il', html)
                kdsf   = re.findall(r'kdsf\.akamaized\.net', html)
                h2s    = re.findall(r'<h2', html)
                isos   = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', html)
                shorts = re.findall(r'shorts-[a-z0-9]+\.htm', html)
                payload = json.dumps({
                    "length": len(html),
                    "thumbs_count": len(thumbs),
                    "kdsf_count": len(kdsf),
                    "h2_count": len(h2s),
                    "iso_count": len(isos),
                    "shorts_count": len(shorts),
                    "sample_1000": html[:1000],
                    "sample_mid": html[5000:6000],
                }, ensure_ascii=False)
            except Exception as e:
                payload = json.dumps({"error": str(e)}, ensure_ascii=False)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))
            return

        # Normal feed endpoint
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        try:
            html = scrape_v1()

            # Try multiple extraction strategies
            items = []

            # Strategy 1: markdown-style blocks
            block_pattern = re.compile(
                r'##\s+\[(.+?)\]\((https://www\.v-1\.co\.il/[^\)]+)\)'
                r'\s+([^\n]+)\n'
                r'\s*(\d{4}-\d{2}-\d{2}T[\d:.Z]+)',
                re.DOTALL
            )
            thumbs = re.findall(
                r'(https://img\.mako\.co\.il/[^\s"\'<>]+?FirstFrame[^\s"\'<>]*?\.jpg)',
                html
            )
            videos = re.findall(
                r'(https://kdsf\.akamaized\.net/[^\s"\'<>]+?master\.m3u8)',
                html
            )
            links_all = re.findall(
                r'(https://www\.v-1\.co\.il/[a-z0-9_\-/]+/shorts-[a-z0-9]+\.htm)',
                html
            )

            matches = list(block_pattern.finditer(html))

            if matches:
                for i, m in enumerate(matches):
                    items.append({
                        "title": m.group(1).strip(),
                        "link":  m.group(2).strip(),
                        "cat":   m.group(3).strip(),
                        "time":  m.group(4).strip(),
                        "thumb": thumbs[i] if i < len(thumbs) else "",
                        "video": videos[i] if i < len(videos) else "",
                        "desc":  "",
                    })
            else:
                # Strategy 2: extract from JSON-LD or structured data
                json_ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
                for jl in json_ld:
                    try:
                        data = json.loads(jl)
                        if isinstance(data, list):
                            for d in data:
                                if d.get("headline"):
                                    items.append({
                                        "title": d.get("headline", ""),
                                        "link":  d.get("url", ""),
                                        "cat":   "",
                                        "time":  d.get("datePublished", ""),
                                        "thumb": d.get("image", {}).get("url", "") if isinstance(d.get("image"), dict) else "",
                                        "video": "",
                                        "desc":  d.get("description", ""),
                                    })
                    except:
                        pass

                # Strategy 3: just extract what we can
                if not items:
                    isos = list(dict.fromkeys(re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z', html)))
                    for i, (t, lnk, vid) in enumerate(zip(isos, links_all, videos)):
                        items.append({
                            "title": f"פריט {i+1}",
                            "link":  lnk,
                            "cat":   "",
                            "time":  t,
                            "thumb": thumbs[i] if i < len(thumbs) else "",
                            "video": vid,
                            "desc":  "",
                        })

            items.sort(key=lambda x: x.get("time", ""), reverse=True)

            payload = json.dumps({
                "ok": True,
                "items": items[:60],
                "count": len(items),
                "debug": {
                    "html_len": len(html),
                    "thumbs": len(thumbs),
                    "videos": len(videos),
                    "links": len(links_all),
                    "matches": len(matches),
                }
            }, ensure_ascii=False)

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
