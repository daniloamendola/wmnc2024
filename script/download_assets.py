#!/usr/bin/env python3
"""
Downloads all CSS, JS, and image assets from www.unive.it referenced in home.html,
then rewrites the HTML to use relative local paths for offline use.
"""
import re
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent
HTML_SRC  = BASE_DIR / "html.txt"
HTML_DEST = BASE_DIR / "www.unive.it/web/en/6439/home.html"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0'
}

SKIP_DOMAINS = ("matomo.unive.it", "connect.facebook.net", "ingestion.webanalytics")

ASSET_EXTS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".webp", ".woff", ".woff2", ".ttf", ".eot", ".pdf",
}


def is_asset(url: str) -> bool:
    path = url.split("?")[0]
    return Path(path).suffix.lower() in ASSET_EXTS


def url_to_local(url: str) -> Path:
    path = urllib.parse.urlparse(url.split("?")[0]).path.lstrip("/")
    return BASE_DIR / "www.unive.it" / path


def download(url: str) -> Path | None:
    if any(d in url for d in SKIP_DOMAINS):
        return None
    if not is_asset(url):
        return None
    local = url_to_local(url)
    if local.exists():
        print(f"  [skip] {local.relative_to(BASE_DIR)}")
        return local
    local.parent.mkdir(parents=True, exist_ok=True)
    clean_url = url.split("?")[0]
    try:
        req = urllib.request.Request(clean_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        local.write_bytes(data)
        print(f"  [ok]   {local.relative_to(BASE_DIR)}")
        time.sleep(0.3)
        return local
    except Exception as e:
        print(f"  [err]  {clean_url}: {e}")
        return None


def find_unive_urls(text: str) -> list[str]:
    return re.findall(r'https://www\.unive\.it/[^"\'() \n><]+', text)


# --- 1. Read source HTML ---
html = HTML_SRC.read_text(encoding="utf-8")
urls = sorted(set(find_unive_urls(html)))
print(f"Found {len(urls)} www.unive.it URLs in HTML\n")

# --- 2. Download all assets ---
css_files: list[Path] = []
for url in urls:
    local = download(url)
    if local and local.suffix == ".css":
        css_files.append(local)

# --- 3. Parse CSS files for additional assets (fonts, images) ---
print(f"\nScanning {len(css_files)} CSS files for additional assets...")
for css_path in css_files:
    try:
        css = css_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    # absolute URLs inside CSS
    for url in find_unive_urls(css):
        download(url)
    # relative url() inside CSS — resolve against the CSS file location
    rel_urls = re.findall(r'url\(["\']?(?!https?://)([^"\'()]+)["\']?\)', css)
    for rel in rel_urls:
        rel = rel.strip()
        if not rel or rel.startswith("data:"):
            continue
        abs_url = "https://www.unive.it/" + str(
            (css_path.parent / rel).resolve().relative_to(BASE_DIR / "www.unive.it")
        ).replace("\\", "/")
        download(abs_url)

# --- 4. Rewrite HTML with relative paths ---
print("\nRewriting absolute URLs to relative paths in HTML...")
new_html = html
for url in sorted(set(find_unive_urls(html)), key=len, reverse=True):
    if any(d in url for d in SKIP_DOMAINS):
        continue
    local = url_to_local(url)
    rel = os.path.relpath(local, HTML_DEST.parent).replace("\\", "/")
    new_html = new_html.replace(url, rel)

HTML_DEST.parent.mkdir(parents=True, exist_ok=True)
HTML_DEST.write_text(new_html, encoding="utf-8")
print(f"\nSaved rewritten HTML to: {HTML_DEST.relative_to(BASE_DIR)}")
print("Done!")
