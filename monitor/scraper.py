import json, urllib.request, hashlib
from datetime import datetime
from bs4 import BeautifulSoup

from .config import NOTIFY_THRESHOLD, HISTORY_PATH, logger
from .analyzer import score_all_news

HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
           "Accept":"text/html,application/json,*/*","Accept-Language":"zh-CN,zh;q=0.9"}
KNOWN_CACHE = set()

def _fetch(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ct = resp.headers.get("Content-Type","")
            if "charset=" in ct:
                cs = ct.split("charset=")[-1].split(";")[0].strip()
                return raw.decode(cs, errors="replace")
            try: return raw.decode("utf-8")
            except: return raw.decode("gbk", errors="replace")
    except Exception as e:
        logger.warning(f"Fetch fail [{url[:50]}]: {e}")
        return None

def _east():
    r = []
    html = _fetch("https://finance.eastmoney.com/a/czqyw.html")
    if not html: return r
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.select("a"):
            t = a.get_text(strip=True); h = a.get("href","")
            if t and len(t) > 10:
                if h.startswith("/"): h = f"https://finance.eastmoney.com{h}"
                r.append({"title":t,"url":h,"source":"东方财富"})
    except: pass
    return r

def _cls():
    r = []
    data = _fetch("https://www.cls.cn/v1/roll/get_roll_list?app=Cailianshe&os=web&sv=8.8.8")
    if not data: return r
    try:
        parsed = json.loads(data)
        for item in parsed.get("data",{}).get("roll_data",[]):
            s = item.get("describes","") or item.get("title","") or item.get("content","")
            if s: r.append({"title":s[:120],"url":f"https://www.cls.cn/detail/{item.get('id','')}","source":"财联社"})
    except: pass
    return r

def _sina():
    r = []
    data = _fetch("https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=20")
    if not data: return r
    try:
        parsed = json.loads(data)
        for item in parsed.get("result",{}).get("data",[]):
            t = item.get("title","").strip()
            if t: r.append({"title":t,"url":item.get("url",""),"source":"新浪财经"})
    except: pass
    return r

FETCHERS = [("东方财富头条",_east),("财联社电报",_cls),("新浪财经",_sina)]

def fetch_all():
    alln = []
    for name,fn in FETCHERS:
        try:
            lst = fn(); logger.info(f"{name}: {len(lst)} items"); alln.extend(lst)
        except: pass
    seen = set(); uq = []
    for n in alln:
        k = n["title"][:40]
        if k not in seen: seen.add(k); uq.append(n)
    logger.info(f"Total unique: {len(uq)}")
    return uq

def load_cache():
    global KNOWN_CACHE
    if HISTORY_PATH.exists():
        try: KNOWN_CACHE = set(json.loads(HISTORY_PATH.read_text("utf-8")).get("known_fingerprints",[]))
        except: pass

def save_cache(fps):
    try:
        HISTORY_PATH.write_text(json.dumps({"known_fingerprints":list(fps),
            "last_updated":datetime.now().isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
    except: pass

def get_bullish_news():
    load_cache()
    all_news = fetch_all()
    scored = score_all_news(all_news)
    important = [n for n in scored if n["final_score"] >= NOTIFY_THRESHOLD]
    save_cache(set(n["fingerprint"] for n in scored))
    logger.info(f"v3 result: {len(scored)} matched, {len(important)} important")
    return important, scored
