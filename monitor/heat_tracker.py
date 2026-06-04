#!/usr/bin/env python
"""
v3 机构关注度追踪 + 多维度热点监测
"""
import json, urllib.request
from datetime import datetime
from collections import defaultdict
from .config import BASE_DIR, logger

TRACKER_PATH = BASE_DIR / "outputs" / "heat_tracker.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"}

class HeatTracker:
    def __init__(self):
        self.state = self._load()
        self.sector_clicks = defaultdict(int)
        self.concept_mentions = defaultdict(int)
        self.institution_keywords = defaultdict(int)

    def _load(self):
        if TRACKER_PATH.exists():
            try: return json.loads(TRACKER_PATH.read_text("utf-8"))
            except: pass
        return {"sector_history": {}, "hot_concepts": [], "institution_focus": [], "daily_topics": [], "last_update": None}

    def _save(self):
        self.state["last_update"] = datetime.now().isoformat()
        TRACKER_PATH.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def fetch_sector_hot(self):
        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=30&po=1&np=1&fields=f12,f14,f3,f62,f184,f66&fs=m:90+t:2"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            sectors = []
            for item in data.get("data", {}).get("diff", []):
                sectors.append({
                    "name": item.get("f14", ""), "code": item.get("f12", ""),
                    "change_pct": item.get("f3", 0), "turnover": item.get("f62", 0),
                    "main_flow": item.get("f184", 0),
                })
            if sectors:
                sorted_by_flow = sorted(sectors, key=lambda x: abs(x["main_flow"]), reverse=True)[:10]
                hot_sectors = [s["name"] for s in sorted_by_flow if s["change_pct"] > 0]
                self.state["hot_concepts"] = hot_sectors
                logger.info(f"Hot sectors: {hot_sectors[:5]}")
        except Exception as e:
            logger.warning(f"Sector hot fetch: {e}")
        self._save()
        return self.state["hot_concepts"]

    def fetch_institution_news(self):
        try:
            url = "https://data.eastmoney.com/report/reportlist.aspx"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
                try: html = raw.decode("utf-8")
                except: html = raw.decode("gbk", errors="replace")
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            texts = [a.get_text(strip=True) for a in soup.select("a") if len(a.get_text(strip=True)) > 10]
            inst_kws = ["推荐", "买入", "增持", "看好", "关注", "评级", "目标价",
                       "调研", "路演", "策略会", "配置", "超配", "重仓"]
            found = []
            for t in texts[:20]:
                for kw in inst_kws:
                    if kw in t:
                        found.append(t[:60])
                        break
            if found:
                self.state["institution_focus"] = found[:10]
                logger.info(f"Institution focus: {len(found)} items")
        except Exception as e:
            logger.warning(f"Institution news: {e}")
        self._save()

    def get_market_mood(self, scored_news: list) -> dict:
        if not scored_news:
            return {"mood": "neutral", "score": 50, "hot_sectors": [], "topics": []}
        total_score = sum(n["final_score"] for n in scored_news)
        avg_score = total_score / max(len(scored_news), 1)
        mood_score = min(100, max(0, avg_score * 5))
        if mood_score >= 70: mood = "very_positive"
        elif mood_score >= 55: mood = "positive"
        elif mood_score >= 40: mood = "neutral"
        elif mood_score >= 25: mood = "cautious"
        else: mood = "negative"
        sector_counts = defaultdict(int)
        for n in scored_news:
            for s in n.get("sectors", []):
                sector_counts[s] += 1
        hot_sectors = sorted(sector_counts.keys(), key=lambda s: sector_counts[s], reverse=True)[:5]
        from .keyword_learner import get_learner
        learner = get_learner()
        topics = learner.get_hot_topics(3)
        return {"mood": mood, "score": round(mood_score, 1), "hot_sectors": hot_sectors, "topics": [t["word"] for t in topics]}


_tracker = None
def get_tracker():
    global _tracker
    if _tracker is None:
        _tracker = HeatTracker()
    return _tracker
