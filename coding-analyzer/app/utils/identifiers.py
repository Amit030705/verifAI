from __future__ import annotations

from urllib.parse import urlparse


def extract_username(value: str | None, platform: str) -> str | None:
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    if "://" not in raw:
        return raw.strip("/@")

    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    host_map = {
        "github": ["github.com", "www.github.com"],
        "leetcode": ["leetcode.com", "www.leetcode.com"],
        "codeforces": ["codeforces.com", "www.codeforces.com"],
    }

    if host not in host_map.get(platform, []):
        return raw.strip("/@")

    if not path_parts:
        return None

    # Handles LeetCode profile urls like /u/<username>/ or /<username>/
    if platform == "leetcode" and path_parts[0] in {"u", "profile"} and len(path_parts) > 1:
        return path_parts[1].strip("/@")

    return path_parts[0].strip("/@")
