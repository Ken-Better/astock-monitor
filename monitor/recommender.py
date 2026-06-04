"""
A股多因子推荐引擎 v2 (正式版)
基于三维度因子分析 + 凯利公式仓位管理
"""
import json, math
from datetime import datetime
from collections import defaultdict
from .config import BASE_DIR, logger

RECOMMENDER_STATE_PATH = BASE_DIR / "outputs" / "recommendations.json"


class MultiFactorEngine:
    """多因子分析引擎"""

    WEIGHTS = {
        "news_sentiment": 0.40,
        "sector_momentum": 0.30,
        "capital_flow": 0.30,
    }

    def __init__(self):
        self.state = self._load()

    def _load(self):
        if RECOMMENDER_STATE_PATH.exists():
            try:
                return json.loads(RECOMMENDER_STATE_PATH.read_text("utf-8"))
            except Exception:
                pass
        return {
            "recommendations": [],
            "factors": {},
            "history": [],
            "last_update": None,
        }

    def _save(self):
        self.state["last_update"] = datetime.now().isoformat()
        RECOMMENDER_STATE_PATH.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def compute_factor1_news(self, scored_news) -> dict:
        stock_signals = defaultdict(lambda: {
            "total_score": 0, "count": 0, "reasons": [],
            "sectors": set(), "sources": set(), "title_snippets": [],
        })
        for news in scored_news:
            stocks = news.get("stocks", [])
            score = news.get("final_score", 0)
            for s in stocks:
                name = s["name"]
                stock_signals[name]["total_score"] += score
                stock_signals[name]["count"] += 1
                stock_signals[name]["reasons"].append(news.get("title", "")[:50])
                stock_signals[name]["sectors"].update(news.get("sectors", []))
                stock_signals[name]["sources"].add(news.get("source", ""))
                stock_signals[name]["title_snippets"].append(news.get("title", "")[:80])
        result = {}
        for name, data in stock_signals.items():
            avg_score = data["total_score"] / max(data["count"], 1)
            source_diversity = min(len(data["sources"]), 3) / 3.0
            base = min(100, avg_score * 5)
            diversity_bonus = source_diversity * 15
            freq_bonus = min(10, data["count"] * 2)
            news_score = min(100, base + diversity_bonus + freq_bonus)
            result[name] = {
                "stock": name, "raw_score": round(news_score, 1),
                "avg_signal_strength": round(avg_score, 1),
                "signal_count": data["count"],
                "source_diversity": round(source_diversity, 2),
                "sectors": list(data["sectors"]), "reasons": data["reasons"][:3],
                "sources": list(data["sources"]),
                "factor_weight": self.WEIGHTS["news_sentiment"],
            }
        return result

    def compute_factor2_sector(self, scored_news, sector_momentum: dict) -> dict:
        if not sector_momentum:
            return {}
        result = {}
        stock_sectors = defaultdict(set)
        sector_scores = {}
        for news in scored_news:
            for s in news.get("stocks", []):
                for sec in news.get("sectors", []):
                    stock_sectors[s["name"]].add(sec)
        for sec_name, sec_data in sector_momentum.items():
            mom_score = sec_data.get("momentum_score", 0)
            normalized = min(100, max(0, (mom_score + 20) * 2.5))
            sector_scores[sec_name] = normalized
        for stock_name, sectors in stock_sectors.items():
            best_sector = max(sectors, key=lambda s: sector_scores.get(s, 0))
            best_score = sector_scores.get(best_sector, 50)
            result[stock_name] = {
                "stock": stock_name,
                "best_sector": best_sector,
                "best_sector_score": round(best_score, 1),
                "related_sectors": list(sectors),
                "sector_count": len(sectors),
                "factor_weight": self.WEIGHTS["sector_momentum"],
            }
        return result

    def compute_factor3_capital(self, scored_news, capital_signal: dict) -> dict:
        if not capital_signal:
            return {}
        result = {}
        nb_signal = capital_signal.get("northbound_signal", 0) or 0
        nb_status = capital_signal.get("northbound_status", "unknown")
        inflow_secs = capital_signal.get("main_force_inflow_sectors", []) or []
        outflow_secs = capital_signal.get("main_force_outflow_sectors", []) or []
        # Map news stocks to capital flow sectors
        stock_secs = defaultdict(set)
        for news in scored_news:
            for s in news.get("stocks", []):
                stock_secs[s["name"]].update(news.get("sectors", []))
        for stock_name, sectors in stock_secs.items():
            matching_inflow = [s for s in sectors if s in inflow_secs]
            matching_outflow = [s for s in sectors if s in outflow_secs]
            flow_bonus = 0
            if matching_inflow:
                flow_bonus = len(matching_inflow) * 8
            if matching_outflow:
                flow_bonus -= len(matching_outflow) * 5
            nb_score = min(30, max(-10, nb_signal * 2))
            capital_score = min(100, max(0, 50 + flow_bonus + nb_score))
            result[stock_name] = {
                "stock": stock_name,
                "capital_score": round(capital_score, 1),
                "northbound_signal_used": round(nb_signal, 1),
                "northbound_status": nb_status,
                "matching_inflow_sectors": matching_inflow,
                "matching_outflow_sectors": matching_outflow,
                "factor_weight": self.WEIGHTS["capital_flow"],
            }
        return result

    def compute_composite(self, scored_news, sector_momentum=None, capital_signal=None):
        f1 = self.compute_factor1_news(scored_news)
        f2 = self.compute_factor2_sector(scored_news, sector_momentum)
        f3 = self.compute_factor3_capital(scored_news, capital_signal)
        all_stocks = set(f1.keys()) | set(f2.keys()) | set(f3.keys())
        if not all_stocks:
            return []
        recommendations = []
        for stock in all_stocks:
            f1_score = f1.get(stock, {}).get("raw_score", 0) or 0
            f2_score = f2.get(stock, {}).get("best_sector_score", 50) or 50
            f3_score = f3.get(stock, {}).get("capital_score", 50) or 50
            composite = (
                f1_score * self.WEIGHTS["news_sentiment"]
                + f2_score * self.WEIGHTS["sector_momentum"]
                + f3_score * self.WEIGHTS["capital_flow"]
            )
            composite = round(composite, 1)
            action, confidence, risk_rating = self._classify(composite)
            suggested_position = self._calc_position_sizing(composite, confidence)
            rec = {
                "rank": 0, "stock": stock, "composite_score": composite,
                "risk_rating": risk_rating, "action": action, "confidence": confidence,
                "suggested_position_pct": suggested_position,
                "suggested_position_label": self._position_label(suggested_position),
                "factor1_news_score": round(f1_score, 1),
                "factor1_details": {
                    "signal_count": f1.get(stock, {}).get("signal_count", 0),
                    "source_diversity": f1.get(stock, {}).get("source_diversity", 0),
                    "reasons": f1.get(stock, {}).get("reasons", [])[:2],
                },
                "factor2_sector_score": round(f2_score, 1),
                "factor2_details": {
                    "best_sector": f2.get(stock, {}).get("best_sector", "N/A"),
                    "sectors": f2.get(stock, {}).get("related_sectors", []),
                },
                "factor3_capital_score": round(f3_score, 1),
                "factor3_details": {
                    "inflow_sectors": f3.get(stock, {}).get("matching_inflow_sectors", []),
                    "outflow_sectors": f3.get(stock, {}).get("matching_outflow_sectors", []),
                },
                "sectors": f1.get(stock, {}).get("sectors", f2.get(stock, {}).get("related_sectors", [])),
                "reasons": f1.get(stock, {}).get("reasons", [])[:2],
                "generated_at": datetime.now().isoformat(),
            }
            recommendations.append(rec)
        recommendations.sort(key=lambda r: r["composite_score"], reverse=True)
        for i, rec in enumerate(recommendations, 1):
            rec["rank"] = i
        self.state["recommendations"] = recommendations[:15]
        self._save()
        return recommendations[:15]

    def _classify(self, score):
        if score >= 80:
            return ("strong_buy", "high", "low")
        elif score >= 65:
            return ("buy", "high", "low")
        elif score >= 55:
            return ("buy", "medium", "medium")
        elif score >= 45:
            return ("watch", "medium", "medium")
        elif score >= 35:
            return ("watch", "low", "high")
        elif score >= 25:
            return ("info", "low", "high")
        else:
            return ("info", "watch", "very_high")

    def _calc_position_sizing(self, score, confidence):
        if confidence == "high":
            if score >= 75:
                return min(30, max(5, round(score * 0.35)))
            return min(20, max(3, round(score * 0.3)))
        elif confidence == "medium":
            return min(15, max(1, round(score * 0.2)))
        elif confidence == "low":
            return min(8, max(0, round(score * 0.1)))
        else:
            return 0

    def _position_label(self, pct):
        if pct >= 20:
            return "重仓"
        elif pct >= 10:
            return "中仓"
        elif pct >= 5:
            return "轻仓"
        elif pct > 0:
            return "观察仓"
        return "观望"

    def get_top_picks(self, n=5):
        return self.state.get("recommendations", [])[:n]


class AStockRecommender:
    """兼容旧接口的包装类"""
    def __init__(self):
        self.engine = MultiFactorEngine()
        self.state = self.engine.state

    def process_news(self, scored_news, sector_momentum=None, capital_signal=None):
        recs = self.engine.compute_composite(scored_news, sector_momentum, capital_signal)
        logger.info(f"MultiFactor recs: {len(recs)} generated")
        if recs:
            for r in recs[:3]:
                logger.info(f"  #{r['rank']} {r['stock']}: composite={r['composite_score']} action={r['action']} pos={r['suggested_position_pct']}%")
        return recs

    def get_top_picks(self, n=5):
        return self.engine.get_top_picks(n)
