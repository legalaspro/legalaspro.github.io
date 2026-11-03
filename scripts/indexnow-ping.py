#!/usr/bin/env python3
"""Submit every URL in sitemap.xml to IndexNow.

Run after a GitHub Pages deploy has finished (see docs/indexnow.md).
Standard library only.

    python3 scripts/indexnow-ping.py --dry-run   # print the request, send nothing
    python3 scripts/indexnow-ping.py             # check the live key file, then POST
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HOST = "manajev.com"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITE_ROOT = Path(__file__).resolve().parent.parent
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
KEY_FILE_RE = re.compile(r"^[0-9a-f]{32}\.txt$")
TIMEOUT = 30
USER_AGENT = f"indexnow-ping (+https://{HOST}/)"


def fail(message):
    print(f"indexnow-ping: {message}", file=sys.stderr)
    sys.exit(1)


def find_key():
    """Return the key from the single <32 hex>.txt file at the site root."""
    keys = []
    for path in sorted(SITE_ROOT.iterdir()):
        if path.is_file() and KEY_FILE_RE.match(path.name):
            if path.read_text(encoding="utf-8").strip() != path.stem:
                fail(f"{path.name} must contain exactly its own name (the key)")
            keys.append(path.stem)
    if len(keys) != 1:
        fail(f"expected one <32 hex chars>.txt key file in {SITE_ROOT}, found {len(keys)}")
    return keys[0]


def read_sitemap(path):
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        fail(f"cannot read {path}: {exc}")
    urls = []
    for loc in root.iter(f"{SITEMAP_NS}loc"):
        url = (loc.text or "").strip()
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "https" or parts.netloc != HOST:
            fail(f"{url!r} in {path} is not an https://{HOST}/ URL")
        if url not in urls:
            urls.append(url)
    if not urls:
        fail(f"no <loc> URLs found in {path}")
    return urls


def check_key_live(key_location, key):
    """IndexNow fetches keyLocation to verify the key, so make sure it is deployed."""
    try:
        request = urllib.request.Request(key_location, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", "replace").strip()
    except (urllib.error.URLError, OSError) as exc:
        fail(f"key file {key_location} is not reachable ({exc}); has the deploy finished?")
    if body != key:
        fail(f"key file {key_location} does not contain the key; has the deploy finished?")


def submit(endpoint, payload):
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
            status = resp.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").strip()
        fail(f"HTTP {exc.code} {exc.reason} from {endpoint}" + (f": {body}" if body else ""))
    except (urllib.error.URLError, OSError) as exc:
        fail(f"request to {endpoint} failed: {exc}")
    if status not in (200, 202):
        fail(f"unexpected HTTP {status} from {endpoint}")
    print(f"HTTP {status}: submitted {len(payload['urlList'])} URLs to {endpoint}")


def main():
    parser = argparse.ArgumentParser(description="Submit sitemap URLs to IndexNow.")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the request that would be sent and exit; no network access")
    parser.add_argument("--sitemap", type=Path, default=SITE_ROOT / "sitemap.xml",
                        help="sitemap to read URLs from (default: %(default)s)")
    parser.add_argument("--endpoint", default=ENDPOINT,
                        help="IndexNow endpoint to POST to (default: %(default)s)")
    args = parser.parse_args()

    key = find_key()
    key_location = f"https://{HOST}/{key}.txt"
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": key_location,
        "urlList": read_sitemap(args.sitemap),
    }

    if args.dry_run:
        print(f"Dry run: would POST to {args.endpoint}")
        print(json.dumps(payload, indent=2))
        return

    check_key_live(key_location, key)
    submit(args.endpoint, payload)


if __name__ == "__main__":
    main()
