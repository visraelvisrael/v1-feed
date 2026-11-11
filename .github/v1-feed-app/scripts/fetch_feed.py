import urllib.request
import json
import re
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/",
}


def fetch(url, max_bytes=300000, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(max_bytes).decode("utf-8", errors="replace")


def scrape():
    html = fetch("https://www.v-1.co.il/")

    thumbs    = re.findall(r'https://img\.mako\.co\.il/[^\s"\'<>]+?FirstFrame[^\s"\'<>]*?\.jpg', html)
    videos    = re.findall(r'https://kdsf\.akamaized\.net/[^\s"\'<>]+?master\.m3u8', html)
    links     = re.findall(r'https://www\.v-1\.co\.il/[a-z0-9_\-/]+/shorts-[a-z0-9]+\.htm', html)
    times     = list(dict.fromkeys(re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z', html)))
    md_titles = re.findall(r'##\s+\[([^\]]{3,200})\]\(https://www\.v-1\.co\.il', html)
    cats      = re.findall(r'\]\(https://www\.v-1\.co\.il/[^\)]+\)\s*\n\s*([^\n]{2,30})\n\s*\d{4}', html)

    items = []
    n = min(len(videos), len(times))

    for i in range(n):
        title = md_titles[i].strip() if i < len(md_titles) else f"קליפ {i+1}"
        items.append({
            "title": title,
            "link":  links[i] if i < len(links) else "https://www.v-1.co.il",
            "cat":   cats[i].strip() if i < len(cats) else "",
            "time":  times[i],
            "thumb": thumbs[i] if i < len(thumbs) else "",
            "video": videos[i],
            "desc":  "",
        })

    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    return items[:60]


if __name__ == "__main__":
    items = scrape()
    print(f"Fetched {len(items)} items")

    # Only save if we got real items
    if not items:
        print("No items fetched, keeping existing feed.json")
        exit(0)

    out_path = os.path.join(os.path.dirname(__file__), "../public/feed.json")
    out_path = os.path.normpath(out_path)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"ok": True, "items": items, "count": len(items)}, f, ensure_ascii=False)

    print(f"Saved to {out_path}")
