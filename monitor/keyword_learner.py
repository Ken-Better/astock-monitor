#!/usr/bin/env python
"""
v3 关键词自学习引擎
"""
import json, re
from collections import Counter, defaultdict
from datetime import datetime
from .config import BASE_DIR, BULLISH_KEYWORDS, logger

LEARNER_STATE_PATH = BASE_DIR / "outputs" / "learner_state.json"

STOP_WORDS = set("我们他们可以这个那个什么一个没有不是就是还是只是但是而且因为所以如果虽然已经"
                 "可能应该需要知道成为进行通过之后以及这些那些这样那样一种其中目前同时此外"
                 "今年昨日今日明日本周本月公司企业行业市场中国全球昨日今日明日上午下午"
                 "记者报道来源编辑作者发布公告提示风险影响推动提升扩大同比增长环比".split())

MIN_FREQ = {2: 5, 3: 3, 4: 2}


class KeywordLearner:
    def __init__(self):
        self.state = self._load_state()
        self.word_freq = Counter()
        self.daily_words = Counter()
        self.sector_words = defaultdict(Counter)
        self.scan_count = 0

    def _load_state(self):
        if LEARNER_STATE_PATH.exists():
            try: return json.loads(LEARNER_STATE_PATH.read_text("utf-8"))
            except: pass
        return {
            "known_keywords": {}, "keyword_history": [],
            "auto_discovered": [], "sector_trends": {},
            "hot_topics": [], "last_scan": None, "total_scans": 0,
        }

    def _save_state(self):
        self.state["last_scan"] = datetime.now().isoformat()
        self.state["total_scans"] = self.scan_count
        LEARNER_STATE_PATH.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def extract_words(self, titles: list):
        for t in titles:
            for i in range(len(t)-1):
                for l in [2, 3, 4]:
                    if i+l <= len(t):
                        w = t[i:i+l]
                        if all("\u4e00" <= c <= "\u9fff" for c in w):
                            if w not in STOP_WORDS:
                                self.word_freq[w] += 1
                                self.daily_words[w] += 1
        self.scan_count += 1

    def discover_new_keywords(self) -> list:
        existing = set(BULLISH_KEYWORDS)
        new_candidates = []
        for word, count in self.daily_words.most_common(100):
            if word not in existing and count >= MIN_FREQ.get(len(word), 2):
                if word not in [k["word"] for k in self.state["auto_discovered"]]:
                    new_candidates.append({
                        "word": word, "count": count,
                        "discovered_at": datetime.now().isoformat(),
                        "status": "candidate",
                    })
                    existing.add(word)
        if new_candidates:
            self.state["auto_discovered"].extend(new_candidates)
            logger.info(f"Auto-discovered {len(new_candidates)} new keyword candidates")
            for c in new_candidates[:10]:
                logger.info(f"  -> {c['word']} (freq: {c['count']})")
        self.daily_words = Counter()
        self._save_state()
        return new_candidates

    def get_hot_topics(self, top_n=5) -> list:
        topics = []
        for item in self.state["auto_discovered"]:
            if item["status"] == "candidate":
                topics.append(item)
        merged = {}
        for t in topics:
            word = t["word"]
            key = word
            for existing in list(merged.keys()):
                if word in existing or existing in word:
                    key = existing if len(existing) >= len(word) else word
                    break
            if key not in merged:
                merged[key] = {"word": key, "count": 0, "sources": []}
            merged[key]["count"] += t["count"]
        result = sorted(merged.values(), key=lambda x: x["count"], reverse=True)[:top_n]
        self.state["hot_topics"] = result
        return result

    def get_sector_heat(self, scored_news: list) -> dict:
        sector_heat = defaultdict(lambda: {"count": 0, "total_score": 0, "stocks": set()})
        for n in scored_news:
            for sec in n.get("sectors", []):
                sector_heat[sec]["count"] += 1
                sector_heat[sec]["total_score"] += n["final_score"]
                for s in n.get("stocks", []):
                    sector_heat[sec]["stocks"].add(s["name"])
        result = {}
        for sec, data in sector_heat.items():
            result[sec] = {
                "count": data["count"],
                "total_score": round(data["total_score"], 1),
                "avg_score": round(data["total_score"] / max(data["count"], 1), 1),
                "stocks": list(data["stocks"])[:5],
                "heat": round(data["count"] * data["total_score"] / max(sum(d["total_score"] for d in sector_heat.values()), 1) * 100, 1),
            }
        self.state["sector_trends"] = result
        self._save_state()
        return result


_learner = None
def get_learner():
    global _learner
    if _learner is None:
        _learner = KeywordLearner()
    return _learner
