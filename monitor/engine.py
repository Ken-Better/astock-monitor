import hashlib
import math
import re
from collections import defaultdict
from datetime import datetime

from .config import (
    AUTHORITY_KEYWORDS,
    CONFIRM_KEYWORDS,
    EVENT_RULES,
    MAX_RECOMMENDATIONS,
    NEGATIVE_KEYWORDS,
    NOTIFY_THRESHOLD,
    POPULAR_STOCKS,
)

ACTION_LABELS = {
    "strong_buy": "强关注",
    "buy": "关注",
    "watch": "观察",
    "avoid": "回避",
}


def score_news(news_items: list[dict]) -> tuple[list[dict], list[dict], dict]:
    scored = []
    sector_scores = defaultdict(lambda: {"score": 0.0, "events": set(), "stocks": set(), "news": []})

    for position, item in enumerate(news_items):
        title = item["title"]
        best = None
        for rule in EVENT_RULES:
            hits = _keyword_hits(title, rule["keywords"])
            if not hits:
                continue

            negative_hits = _keyword_hits(title, NEGATIVE_KEYWORDS)
            score = rule["base"] + len(hits) * 8 + _specificity_bonus(title)
            score *= float(item.get("source_weight", 1.0))
            score *= max(0.76, 1.0 - position * 0.005)
            score -= len(negative_hits) * 18
            score = round(max(0, min(100, score)), 1)
            candidate = {"rule": rule, "hits": hits, "score": score, "negative_hits": negative_hits}
            if best is None or candidate["score"] > best["score"]:
                best = candidate

        if not best:
            continue

        rule = best["rule"]
        risk = "high" if best["negative_hits"] else ("medium" if best["score"] < 76 else "normal")
        row = {
            **item,
            "score": best["score"],
            "level": _level(best["score"], risk),
            "event": rule["event"],
            "matched_keywords": best["hits"],
            "negative_keywords": best["negative_hits"],
            "sectors": rule["sectors"],
            "stocks": rule["stocks"],
            "duration": rule["duration"],
            "risk": risk,
        }
        scored.append(row)

        for sector in rule["sectors"]:
            sector_scores[sector]["score"] += best["score"] / max(1, len(rule["sectors"]))
            sector_scores[sector]["events"].add(rule["event"])
            sector_scores[sector]["news"].append(title[:70])
            for stock in rule["stocks"]:
                sector_scores[sector]["stocks"].add(stock)

    scored.sort(key=lambda row: row["score"], reverse=True)
    important = [row for row in scored if row["score"] >= NOTIFY_THRESHOLD and row["risk"] != "high"]
    return important, scored, _format_sector_impact(sector_scores)


def build_recommendations(scored_news: list[dict], market_data: dict | None = None) -> list[dict]:
    stock_state = defaultdict(lambda: {"score": 0.0, "events": set(), "sectors": set(), "reasons": [], "risks": set()})
    for news in scored_news:
        if news.get("risk") == "high":
            continue
        for stock in news.get("stocks", []):
            state = stock_state[stock]
            state["score"] += news["score"] * 0.46
            state["events"].add(news["event"])
            state["sectors"].update(news.get("sectors", []))
            state["reasons"].append(news["title"][:62])
            if news.get("risk") not in ("normal", "medium"):
                state["risks"].add(news["risk"])

    sector_flow = _sector_flow_score(market_data or {})
    recommendations = []
    for stock, state in stock_state.items():
        breadth_bonus = min(14, len(state["events"]) * 4 + len(state["sectors"]) * 2)
        popularity_bonus = 5 if stock in POPULAR_STOCKS else 0
        sector_bonus = max([sector_flow.get(sector, 0) for sector in state["sectors"]] or [0])
        risk_penalty = 12 if state["risks"] else 0
        composite = round(min(100, state["score"] + breadth_bonus + popularity_bonus + sector_bonus - risk_penalty), 1)
        action, position, stop, take_profit = _trade_plan(composite, bool(state["risks"]))
        recommendations.append(
            {
                "stock": stock,
                "score": composite,
                "action": action,
                "action_label": ACTION_LABELS[action],
                "position_pct": position,
                "entry": _entry_rule(action),
                "stop_loss": stop,
                "take_profit": take_profit,
                "time_stop": "3个交易日无放量确认则降级观察",
                "sectors": sorted(state["sectors"])[:4],
                "events": sorted(state["events"])[:4],
                "reasons": state["reasons"][:3],
                "risk_flags": sorted(state["risks"]),
            }
        )

    recommendations = [row for row in recommendations if row["action"] != "avoid"]
    recommendations.sort(key=lambda row: row["score"], reverse=True)
    for index, row in enumerate(recommendations[:MAX_RECOMMENDATIONS], 1):
        row["rank"] = index
    return recommendations[:MAX_RECOMMENDATIONS]


def build_summary(important: list[dict], scored: list[dict], recommendations: list[dict], sector_impact: dict) -> dict:
    top = recommendations[0] if recommendations else None
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "important_count": len(important),
        "matched_count": len(scored),
        "sector_count": len(sector_impact["sectors"]),
        "mood": _market_mood(scored),
        "top_stock": top["stock"] if top else "",
        "top_action": top["action_label"] if top else "",
        "version": "v5",
        "scan_interval": "1分钟",
    }


def notification_fingerprint(important: list[dict], recommendations: list[dict]) -> str:
    payload = "|".join([row["title"][:60] for row in important[:4]])
    payload += "|" + "|".join([row["stock"] + str(row["score"]) for row in recommendations[:4]])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _keyword_hits(title: str, words: list[str]) -> list[str]:
    title_lower = title.lower()
    return [word for word in words if word.lower() in title_lower]


def _specificity_bonus(title: str) -> int:
    bonus = 0
    if re.search(r"\d+(\.\d+)?\s*(%|亿元|万亿元|万台|万套|颗|枚)", title):
        bonus += 7
    if any(word in title for word in CONFIRM_KEYWORDS):
        bonus += 7
    if any(word in title for word in AUTHORITY_KEYWORDS):
        bonus += 8
    if any(word in title for word in ["盘中", "午后", "直线拉升", "涨停", "大涨"]):
        bonus += 5
    return min(bonus, 22)


def _level(score: float, risk: str) -> str:
    if risk == "high":
        return "风险信号"
    if score >= 88:
        return "重大利好"
    if score >= 76:
        return "强利好"
    if score >= 62:
        return "关注"
    return "普通"


def _format_sector_impact(raw: dict) -> dict:
    sectors = []
    for sector, data in raw.items():
        sectors.append(
            {
                "sector": sector,
                "score": round(data["score"], 1),
                "events": sorted(data["events"]),
                "stocks": sorted(data["stocks"])[:6],
                "news": data["news"][:3],
            }
        )
    sectors.sort(key=lambda row: row["score"], reverse=True)
    return {"sectors": sectors[:12], "updated_at": datetime.now().isoformat(timespec="seconds")}


def _sector_flow_score(market_data: dict) -> dict[str, float]:
    result = {}
    for row in market_data.get("sectors", [])[:40]:
        name = row.get("name", "")
        change = _to_float(row.get("change_pct"))
        flow = _to_float(row.get("main_flow_yuan") or row.get("turnover_yuan"))
        if not name:
            continue
        result[name] = min(12, max(-8, change * 1.35 + (math.copysign(2, flow) if flow else 0)))
    return result


def _trade_plan(score: float, has_risk: bool) -> tuple[str, int, str, str]:
    if has_risk:
        return "avoid", 0, "-", "-"
    if score >= 86:
        return "strong_buy", 12, "-6%", "+12%至+18%分批"
    if score >= 74:
        return "buy", 8, "-5%", "+8%至+12%分批"
    if score >= 58:
        return "watch", 3, "-4%", "+6%先观察"
    return "watch", 0, "-", "-"


def _entry_rule(action: str) -> str:
    if action == "strong_buy":
        return "开盘后量能确认且高开不超过6%再考虑"
    if action == "buy":
        return "回踩5日线或分时放量突破时小仓试探"
    if action == "watch":
        return "等待板块持续性和成交量确认"
    return "不参与"


def _market_mood(scored: list[dict]) -> dict:
    if not scored:
        return {"label": "中性", "score": 50, "class": "neutral"}
    avg = sum(row["score"] for row in scored[:12]) / min(len(scored), 12)
    if avg >= 82:
        return {"label": "进攻", "score": round(avg, 1), "class": "positive"}
    if avg >= 68:
        return {"label": "偏暖", "score": round(avg, 1), "class": "warm"}
    if avg >= 52:
        return {"label": "中性", "score": round(avg, 1), "class": "neutral"}
    return {"label": "谨慎", "score": round(avg, 1), "class": "cautious"}


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
