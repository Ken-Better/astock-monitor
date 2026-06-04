#!/usr/bin/env python
"""A股利好监控 v3 — GitHub Actions 版本"""
import sys, json
from datetime import datetime
from monitor.scraper import get_bullish_news
from monitor.dashboard import generate_dashboard
from monitor.notifier import notify_all
from monitor.auto_deploy import auto_deploy
from monitor.keyword_learner import get_learner
from monitor.heat_tracker import get_tracker
from monitor.config import HISTORY_PATH, logger
from monitor.recommender import AStockRecommender
from monitor.market_data import MarketDataEngine


def run_once():
    logger.info("=" * 55)
    logger.info("v3 cloud scan starting...")

    # 0. 获取市场数据
    market_engine = MarketDataEngine()
    try:
        market_data = market_engine.fetch_all()
        logger.info("Market data fetched: %d sectors, %d gainers" % (
            len(market_data.get("sectors", [])),
            len(market_data.get("gainers", [])),
        ))
        sector_momentum = market_engine.get_sector_momentum()
        capital_signal = market_engine.get_capital_flow_signal()
        logger.info("Capital signal: northbound=%s overall=%s" % (
            capital_signal.get("northbound_status", "?"),
            capital_signal.get("overall_signal", 0),
        ))
    except Exception as e:
        logger.warning("Market data error (non-fatal): %s" % e)
        market_data = None
        sector_momentum = None
        capital_signal = None

    # 1. 扫描新闻 + 评分
    important, all_scored = get_bullish_news()

    # 2. 自学习
    learner = get_learner()
    titles = [n["title"] for n in all_scored]
    learner.extract_words(titles)
    new_kws = learner.discover_new_keywords()
    hot_topics = learner.get_hot_topics(3)
    sector_heat = learner.get_sector_heat(all_scored)

    # 3. 机构热点追踪
    tracker = get_tracker()
    hot_sectors = tracker.fetch_sector_hot()
    tracker.fetch_institution_news()
    mood = tracker.get_market_mood(all_scored)

    # 4. 保存历史
    try:
        history = []
        if HISTORY_PATH.exists():
            history = json.loads(HISTORY_PATH.read_text("utf-8")).get("history", [])
        for n in important:
            secs = ",".join(n.get("sectors", []))
            stks = ",".join(s["name"] for s in n.get("stocks", [])[:3])
            history.insert(0, {
                "title": n["title"][:60], "score": n["final_score"],
                "source": n["source"], "sectors": secs, "stocks": stks,
                "time": n["timestamp"][:16],
            })
        history = history[:200]
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump({"history": history, "last_scan": datetime.now().isoformat(),
                       "v3": True}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("History: %s" % e)

    # 5. 多因子推荐
    recs = None
    try:
        recommender = AStockRecommender()
        recs = recommender.process_news(all_scored, sector_momentum, capital_signal)
        if recs:
            logger.info("Top recommendations: %s" % [(r["stock"], r["action"],
                        r["confidence"], r["suggested_position_pct"]) for r in recs[:3]])
    except Exception as e:
        logger.warning("Recommender error: %s" % e)

    # 6. 生成看板 + 部署
    auto_keywords = [k["word"] for k in new_kws[:10]]
    hot_topic_words = [t["word"] for t in hot_topics]
    dp = generate_dashboard(important, all_scored, mood, hot_sectors,
                            auto_keywords, hot_topic_words, recs,
                            market_data=market_data)
    try:
        auto_deploy()
    except Exception as e:
        logger.warning("auto-deploy skip: %s" % e)

    # 7. 推送通知
    notified = False
    if important:
        top = important[0]
        title = "A股利好v3: %s" % top["title"][:35]
        lines = ["检测到 %s 条利好信号" % len(important)]
        if capital_signal:
            nb = capital_signal.get("northbound_net", 0)
            nb_status = capital_signal.get("northbound_status", "?")
            lines.append("北向资金: %s (%+.2f亿)" % (nb_status, nb))
        for n in important[:5]:
            secs = " ".join(n.get("sectors", []))
            stks = " ".join(s["name"] for s in n.get("stocks", [])[:3])
            lines.append("[%s分] %s" % (n["final_score"], n["title"][:50]))
            if secs: lines.append("  行业: %s" % secs)
            if stks: lines.append("  股票: %s" % stks)
        if recs and recs[0]:
            r = recs[0]
            lines.append("\n推荐: %s [%s] 仓%s%% 风险%s" % (
                r["stock"], r["action"], r["suggested_position_pct"],
                r.get("risk_rating", "?"),
            ))
        if auto_keywords:
            lines.append("\n热点新词: %s" % " ".join(auto_keywords[:5]))
        r = notify_all(title, "\n".join(lines))
        notified = any(r.values())

    s = {"total": len(all_scored), "important": len(important),
         "sectors": len(sector_heat), "mood": mood.get("mood"),
         "new_kws": len(new_kws), "notified": notified, "dashboard": dp}
    logger.info("v3 cloud scan done: %s" % s)
    logger.info("=" * 55)
    return s


if __name__ == "__main__":
    r = run_once()
    print("\nv3 结果: %s条匹配, %s条重要" % (r["total"], r["important"]))
    print("  行业热度: %s个行业, 情绪: %s" % (r["sectors"], r["mood"]))
    print("  新发现关键词: %s个" % r["new_kws"])
    print("  推送: %s" % r["notified"])
    print("  看板: %s" % r["dashboard"])
