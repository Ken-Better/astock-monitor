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
    "strong_buy": "\u5f3a\u5173\u6ce8",
    "buy": "\u5173\u6ce8",
    "watch": "\u89c2\u5bdf",
    "avoid": "\u56de\u907f",
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
        factors = {
            "news_heat": round(min(40, state["score"] * 0.45), 1),
            "event_breadth": round(breadth_bonus, 1),
            "stock_attention": popularity_bonus,
            "sector_flow": round(sector_bonus, 1),
            "risk_penalty": risk_penalty,
        }
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
                "time_stop": "3\u4e2a\u4ea4\u6613\u65e5\u65e0\u653e\u91cf\u786e\u8ba4\u5219\u964d\u7ea7\u89c2\u5bdf",
                "sectors": sorted(state["sectors"])[:4],
                "events": sorted(state["events"])[:4],
                "reasons": state["reasons"][:3],
                "risk_flags": sorted(state["risks"]),
                "factors": factors,
                "decision": _decision_note(action, composite, factors),
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
        "scan_interval": "1\u5206\u949f",
    }


def build_market_pulse(market_data: dict | None, scored: list[dict], sector_impact: dict) -> dict:
    market_data = market_data or {}
    sectors = market_data.get("sectors", []) or []
    gainers = market_data.get("gainers", []) or []
    northbound = market_data.get("northbound", {}) or {}
    main_force = market_data.get("main_force", {}) or {}

    top_event_sectors = sector_impact.get("sectors", [])[:6]
    hot_keywords = _hot_keywords(scored)
    return {
        "market_open": bool(market_data.get("market_open")),
        "northbound": {
            "net": northbound.get("total_net", 0),
            "status": northbound.get("status", "unknown"),
        },
        "top_sectors": [
            {
                "name": row.get("name", ""),
                "change_pct": _to_float(row.get("change_pct")),
                "main_flow_yuan": _to_float(row.get("main_flow_yuan")),
            }
            for row in sectors[:10]
        ],
        "top_gainers": [
            {
                "code": row.get("code", ""),
                "name": row.get("name", ""),
                "change_pct": _to_float(row.get("change_pct")),
                "price": row.get("price", ""),
            }
            for row in gainers[:10]
        ],
        "main_force_inflow": main_force.get("inflow_sectors", [])[:5],
        "event_sectors": top_event_sectors,
        "hot_keywords": hot_keywords,
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
        return "\u98ce\u9669\u4fe1\u53f7"
    if score >= 88:
        return "\u91cd\u5927\u5229\u597d"
    if score >= 76:
        return "\u5f3a\u5229\u597d"
    if score >= 62:
        return "\u5173\u6ce8"
    return "\u666e\u901a"


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
        return "strong_buy", 12, "-6%", "+12%\u81f3+18%\u5206\u6279"
    if score >= 74:
        return "buy", 8, "-5%", "+8%\u81f3+12%\u5206\u6279"
    if score >= 58:
        return "watch", 3, "-4%", "+6%\u5148\u89c2\u5bdf"
    return "watch", 0, "-", "-"


def _decision_note(action: str, score: float, factors: dict) -> str:
    if action == "strong_buy":
        return "新闻热度、题材宽度和人气股属性同时满足，适合只在量能确认后强关注。"
    if action == "buy":
        return "事件分数达标但需要盘面确认，适合小仓观察而不是追高。"
    if action == "watch":
        return "有题材映射但强度不足，优先等板块持续性和成交量。"
    return "风险或负面词较多，不进入买入观察池。"


def _hot_keywords(scored: list[dict]) -> list[dict]:
    counts = defaultdict(lambda: {"count": 0, "score": 0.0})
    for row in scored[:80]:
        for word in row.get("matched_keywords", []):
            counts[word]["count"] += 1
            counts[word]["score"] += row.get("score", 0)
    hot = [
        {"word": word, "count": data["count"], "score": round(data["score"], 1)}
        for word, data in counts.items()
    ]
    hot.sort(key=lambda item: (item["score"], item["count"]), reverse=True)
    return hot[:12]


def _entry_rule(action: str) -> str:
    if action == "strong_buy":
        return "\u5f00\u76d8\u540e\u91cf\u80fd\u786e\u8ba4\u4e14\u9ad8\u5f00\u4e0d\u8d85\u8fc76%\u518d\u8003\u8651"
    if action == "buy":
        return "\u56de\u8e295\u65e5\u7ebf\u6216\u5206\u65f6\u653e\u91cf\u7a81\u7834\u65f6\u5c0f\u4ed3\u8bd5\u63a2"
    if action == "watch":
        return "\u7b49\u5f85\u677f\u5757\u6301\u7eed\u6027\u548c\u6210\u4ea4\u91cf\u786e\u8ba4"
    return "\u4e0d\u53c2\u4e0e"


def _market_mood(scored: list[dict]) -> dict:
    if not scored:
        return {"label": "\u4e2d\u6027", "score": 50, "class": "neutral"}
    avg = sum(row["score"] for row in scored[:12]) / min(len(scored), 12)
    if avg >= 82:
        return {"label": "\u8fdb\u653b", "score": round(avg, 1), "class": "positive"}
    if avg >= 68:
        return {"label": "\u504f\u6696", "score": round(avg, 1), "class": "warm"}
    if avg >= 52:
        return {"label": "\u4e2d\u6027", "score": round(avg, 1), "class": "neutral"}
    return {"label": "\u8c28\u614e", "score": round(avg, 1), "class": "cautious"}


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
