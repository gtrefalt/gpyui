"""Check built local HTML links, card previews and anchors, including Pages subpaths."""

import tomllib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
project = tomllib.loads((ROOT / "zensical.toml").read_text())["project"]
site = ROOT / project["site_dir"]
prefix = urlsplit(project["site_url"]).path


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.ids = set()
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        attribute = "href" if tag in {"a", "link"} else "src" if tag in {"img", "script"} else None
        if attribute and attribute in attrs:
            self.links.append(attrs[attribute])


if __name__ == "__main__":
    pages = {path: Page(path) for path in site.rglob("*.html")}
    if not pages:
        raise SystemExit("Build the Zensical site first.")
    broken = []
    for path, page in pages.items():
        for target in page.links:
            if urlsplit(target).scheme or target.startswith("//"):
                continue
            url = urlsplit(urljoin(prefix + path.relative_to(site).as_posix(), target))
            relative = unquote(url.path)
            if relative.startswith(prefix):
                relative = relative[len(prefix) :]
            actual = site / relative.lstrip("/")
            if not actual.exists():
                broken.append((str(path.relative_to(site)), target))
                continue
            if actual.is_dir():
                actual /= "index.html"
            if url.fragment and actual in pages and unquote(url.fragment) not in pages[actual].ids:
                broken.append((str(path.relative_to(site)), target))
    if broken:
        raise SystemExit(f"Broken local links/assets/anchors: {broken}")
    print(f"Verified local links, assets and anchors across {len(pages)} built pages.")
