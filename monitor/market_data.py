"""A股市场实时数据模块 - 使用多源API + 回退策略"""
import json, urllib.request, re
from datetime import datetime
from collections import defaultdict
from .config import BASE_DIR, logger

MARKET_DATA_PATH = BASE_DIR / "outputs" / "market_data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
}


def _fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return raw
    except Exception as e:
        logger.warning("Fetch fail [%s]: %s" % (url[:70], e))
        return None


def _fetch_json(url, timeout=10):
    raw = _fetch_url(url, timeout)
    if not raw:
        return None
    if raw.startswith("(") or raw.startswith("jQuery"):
        m = re.search(r"\((\{.*\})\)", raw, re.DOTALL)
        if m:
            raw = m.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def fetch_sector_performance():
    url = ("https://push2.eastmoney.com/api/qt/clist/get"
           "?cb=&pn=1&pz=56&po=1&np=1"
           "&fields=f12,f14,f3,f62,f184,f20,f104,f8,f15,f16"
           "&fs=m:90+t:2")
    data = _fetch_json(url)
    if data and data.get("data", {}).get("diff"):
        sectors = []
        for item in data["data"]["diff"]:
            sectors.append({
                "name": item.get("f14", ""), "code": item.get("f12", ""),
                "change_pct": item.get("f3", 0), "turnover_yuan": item.get("f62", 0),
                "main_flow_yuan": item.get("f184", 0), "market_cap_yuan": item.get("f20", 0),
                "pe_ratio": item.get("f104", 0), "up_count": item.get("f8", 0),
                "down_count": item.get("f15", 0),
            })
        sectors.sort(key=lambda s: (s["change_pct"] or 0), reverse=True)
        logger.info("Sector perf: %d sectors" % len(sectors))
        return sectors
    logger.warning("Sector perf: API returned no data")
    return []


def fetch_top_gainers(top_n=20):
    url = ("https://push2.eastmoney.com/api/qt/clist/get"
           "?cb=&pn=1&pz=%d&po=1&np=1"
           "&fields=f12,f14,f2,f3,f4,f5,f6,f15,f16,f17,f62,f184,f8"
           "&fs=m:0+t:6+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2"
           "&fltt=2" % top_n)
    data = _fetch_json(url)
    if not data:
        return []
    gainers = []
    for item in data.get("data", {}).get("diff", []):
        change_pct = item.get("f3", 0)
        if change_pct and change_pct > 0:
            gainers.append({
                "code": item.get("f12", ""), "name": item.get("f14", ""),
                "price": item.get("f2", 0), "change_pct": change_pct,
                "volume": item.get("f5", 0), "turnover_yuan": item.get("f62", 0),
                "main_flow_yuan": item.get("f184", 0),
            })
    gainers = [g for g in gainers if g["change_pct"] > 0]
    gainers.sort(key=lambda g: g["change_pct"], reverse=True)
    return gainers[:top_n]


def fetch_northbound_flow():
    result = {
        "sh_net": 0, "sz_net": 0, "total_net": 0,
        "sh_accum": 0, "sz_accum": 0, "total_accum": 0,
        "status": "unknown", "updated": None,
    }
    try:
        url = ("https://push2.eastmoney.com/api/qt/ulist.np/get"
               "?fltt=2&fields=f2,f3,f4,f12,f14&secids=1.000001,0.159901")
        data = _fetch_json(url)
        if data and data.get("data"):
            for item in data["data"].get("diff", []):
                code = str(item.get("f12", ""))
                net = item.get("f4", 0) or 0
                if "000001" in code:
                    result["sh_net"] = net
                elif "159901" in code:
                    result["sz_net"] = net
        result["total_net"] = round(result["sh_net"] + result["sz_net"], 2)
        result["total_accum"] = round(result["total_net"], 2)
        result["updated"] = datetime.now().isoformat()
        result["status"] = "inflow" if result["total_net"] > 1 else (
            "outflow" if result["total_net"] < -1 else "neutral")
        logger.info("Northbound: total=%.2f (SH=%.2f SZ=%.2f)" % (
            result["total_net"], result["sh_net"], result["sz_net"]))
    except Exception as e:
        logger.warning("Northbound fetch error: %s" % e)
    return result


def fetch_main_force_flow(top_sectors=10):
    url = ("https://push2.eastmoney.com/api/qt/clist/get"
           "?cb=&pn=1&pz=%d&po=1&np=1"
           "&fields=f12,f14,f3,f62,f184,f20,f8,f15"
           "&fs=m:90+t:2" % top_sectors)
    data = _fetch_json(url)
    sectors = []
    if data and data.get("data"):
        for item in data["data"].get("diff", []):
            flow = item.get("f184", 0) or 0
            sectors.append({
                "name": item.get("f14", ""), "code": item.get("f12", ""),
                "main_flow_yuan": flow, "change_pct": item.get("f3", 0),
                "turnover_yuan": item.get("f62", 0),
            })
        sectors.sort(key=lambda s: (s["main_flow_yuan"] or 0), reverse=True)
    inflow = [s for s in sectors if (s["main_flow_yuan"] or 0) > 0]
    outflow = [s for s in sectors if (s["main_flow_yuan"] or 0) < 0]
    return {
        "inflow_sectors": inflow[:5], "outflow_sectors": outflow[:5],
        "top_flow": sectors[:10], "updated": datetime.now().isoformat(),
    }


class MarketDataEngine:
    def __init__(self):
        self.cache = self._load_cache()
        self.last_fetch = None

    def fetch_all(self):
        now = datetime.now()
        result = {
            "timestamp": now.isoformat(),
            "market_open": self._is_market_open(now),
            "sectors": fetch_sector_performance(),
            "gainers": fetch_top_gainers(15),
            "northbound": fetch_northbound_flow(),
            "main_force": fetch_main_force_flow(10),
        }
        if not result["sectors"] and self.cache and self.cache.get("sectors"):
            result["sectors"] = self.cache["sectors"]
        if not result["gainers"] and self.cache and self.cache.get("gainers"):
            result["gainers"] = self.cache["gainers"]
        if not result["northbound"]["total_net"] and self.cache and self.cache.get("northbound"):
            result["northbound"] = self.cache["northbound"]
        self.cache = result
        self.last_fetch = now
        self._save(result)
        return result

    def _load_cache(self):
        if MARKET_DATA_PATH.exists():
            try: return json.loads(MARKET_DATA_PATH.read_text("utf-8"))
            except: pass
        return None

    def _save(self, data):
        try:
            MARKET_DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Market data save: %s" % e)

    def _is_market_open(self, dt):
        if dt.weekday() >= 5:
            return False
        h, m = dt.hour, dt.minute
        if h < 9 or (h == 9 and m < 30) or h >= 15:
            return False
        if (h == 11 and m >= 30) or h in (12,):
            return False
        return True

    def get_sector_momentum(self):
        sectors = self.cache.get("sectors", []) if self.cache else []
        momentum = {}
        for s in sectors:
            name = s.get("name", "")
            change = s.get("change_pct", 0) or 0
            flow = s.get("main_flow_yuan", 0) or 0
            momentum[name] = {
                "sector": name, "change_pct": change, "main_flow_yuan": flow,
                "momentum_score": round(change * 0.6 + (1 if flow > 0 else -1) * 2, 1),
            }
        return momentum

    def get_capital_flow_signal(self):
        nb = (self.cache or {}).get("northbound", {})
        mf = (self.cache or {}).get("main_force", {})
        total_net = nb.get("total_net", 0) or 0
        nb_sig = min(10, max(-10, total_net / 5))
        inflow_names = [s["name"] for s in (mf.get("inflow_sectors", []) or [])[:3] if s.get("name")]
        outflow_names = [s["name"] for s in (mf.get("outflow_sectors", []) or [])[:3] if s.get("name")]
        return {
            "northbound_net": total_net,
            "northbound_status": nb.get("status", "unknown"),
            "northbound_signal": round(nb_sig, 1),
            "main_force_inflow_sectors": inflow_names,
            "main_force_outflow_sectors": outflow_names,
            "overall_signal": round(min(10, max(-10, nb_sig * 0.5 + (len(inflow_names) - len(outflow_names)) * 1.5)), 1),
        }


_market_engine = None
def get_market_engine():
    global _market_engine
    if _market_engine is None:
        _market_engine = MarketDataEngine()
    return _market_engine
