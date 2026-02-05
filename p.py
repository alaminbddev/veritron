import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote

visited = set()

# ---------- Helpers ----------
def get_file_path(url, base_url, base_folder="public"):
    """
    Convert a URL into a local file path inside base_folder,
    stripping the base_url path prefix.
    """
    parsed_base = urlparse(base_url)
    parsed = urlparse(url)

    # Strip base path (e.g., /local/)
    base_path = parsed_base.path.rstrip("/")
    path = unquote(parsed.path)

    if base_path and path.startswith(base_path):
        path = path[len(base_path):]

    if path.endswith("/") or path == "":
        path = os.path.join(path, "index.html")
    elif not path.endswith(".html") and "." not in os.path.basename(path):
        path = path + ".html"

    local_path = os.path.join(base_folder, path.lstrip("/"))
    folder = os.path.dirname(local_path)
    os.makedirs(folder, exist_ok=True)

    return local_path

def save_file(url, base_url, base_folder="public"):
    """
    Save an asset file (CSS, JS, Image).
    """
    file_path = get_file_path(url, base_url, base_folder)
    if os.path.exists(file_path):
        return

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"[OK] Saved asset: {file_path}")
    except Exception as e:
        print(f"[ERROR] {url} - {e}")

def download_assets(soup, page_url, base_url):
    """
    Download CSS, JS, Images from page.
    """
    for tag, attr in [("link", "href"), ("script", "src"), ("img", "src")]:
        for element in soup.find_all(tag):
            url = element.get(attr)
            if not url:
                continue
            full_url = urljoin(page_url, url)
            save_file(full_url, base_url)

# ---------- Crawler ----------
def crawl(url, base_url, domain, base_folder="public"):
    if url in visited:
        return
    visited.add(url)

    print(f"[CRAWL] {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url} - {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Save HTML with correct path
    file_path = get_file_path(url, base_url, base_folder)
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print(f"[OK] Saved HTML: {file_path}")
    else:
        print(f"[SKIP] HTML already exists: {file_path}")

    # Download assets
    download_assets(soup, url, base_url)

    # Crawl internal links
    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)

        # Only crawl same domain and HTML pages
        if parsed.netloc == domain and (parsed.path.endswith(".html") or parsed.path.endswith("/") or parsed.path == ""):
            crawl(full_url, base_url, domain, base_folder)

# ---------- Main ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <URL>")
        sys.exit(1)

    start_url = sys.argv[1]
    domain = urlparse(start_url).netloc

    os.makedirs("public", exist_ok=True)

    crawl(start_url, start_url, domain, "public")

if __name__ == "__main__":
    main()
