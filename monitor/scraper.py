import json
import re
import urllib.request
from datetime import datetime
from html import unescape

from bs4 import BeautifulSoup

from .config import MAX_NEWS_ITEMS, NEWS_SOURCES, logger

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def _decode(raw: bytes, content_type: str = "") -> str:
    charset = ""
    if "charset=" in content_type:
        charset = content_type.split("charset=", 1)[1].split(";", 1)[0].strip()
    for encoding in [charset, "utf-8", "gb18030", "gbk"]:
        if not encoding:
            continue
        try:
            return raw.decode(encoding, errors="replace")
        except LookupError:
            continue
    return raw.decode("utf-8", errors="replace")


def _fetch(url: str, timeout: int = 12) -> str | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _decode(resp.read(), resp.headers.get("Content-Type", ""))
    except Exception as exc:
        logger.warning("Fetch failed %s: %s", url[:80], exc)
        return None


def _clean_title(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:160]


def _fetch_cls(source: dict) -> list[dict]:
    raw = _fetch(source["url"])
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    items = []
    for item in data.get("data", {}).get("roll_data", []):
        title = _clean_title(item.get("describes") or item.get("title") or item.get("content"))
        if title:
            items.append(
                {
                    "title": title,
                    "url": f"https://www.cls.cn/detail/{item.get('id', '')}",
                    "source": source["name"],
                    "source_weight": source["weight"],
                    "published_at": item.get("ctime") or item.get("time") or "",
                }
            )
    return items


def _fetch_sina(source: dict) -> list[dict]:
    raw = _fetch(source["url"])
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    items = []
    for item in data.get("result", {}).get("data", []):
        title = _clean_title(item.get("title", ""))
        if title:
            items.append(
                {
                    "title": title,
                    "url": item.get("url", ""),
                    "source": source["name"],
                    "source_weight": source["weight"],
                    "published_at": item.get("ctime") or "",
                }
            )
    return items


def _fetch_html(source: dict) -> list[dict]:
    raw = _fetch(source["url"])
    if not raw:
        return []
    soup = BeautifulSoup(raw, "lxml")
    items = []
    for link in soup.select("a"):
        title = _clean_title(link.get_text(" ", strip=True))
        href = link.get("href", "")
        if len(title) < 10:
            continue
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            root = re.match(r"^https?://[^/]+", source["url"])
            href = (root.group(0) if root else "") + href
        items.append(
            {
                "title": title,
                "url": href,
                "source": source["name"],
                "source_weight": source["weight"],
                "published_at": "",
            }
        )
    return items


def fetch_all_news() -> list[dict]:
    fetchers = {"cls": _fetch_cls, "sina": _fetch_sina, "html": _fetch_html}
    all_items = []
    for source in NEWS_SOURCES:
        items = fetchers[source["kind"]](source)
        logger.info("Source %s: %d items", source["name"], len(items))
        all_items.extend(items)

    seen = set()
    unique = []
    for item in all_items:
        key = re.sub(r"\W+", "", item["title"])[:48]
        if key in seen:
            continue
        seen.add(key)
        item["fingerprint"] = key
        item["scan_time"] = datetime.now().isoformat(timespec="seconds")
        unique.append(item)
    return unique[:MAX_NEWS_ITEMS]
