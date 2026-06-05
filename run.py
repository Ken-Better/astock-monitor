#!/usr/bin/env python
import json
import os
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from monitor.auto_deploy import auto_deploy
from monitor.config import DATA_PATH, HISTORY_PATH, logger
from monitor.dashboard import write_dashboard
from monitor.engine import build_market_pulse, build_recommendations, build_summary, notification_fingerprint, score_news
from monitor.market_data import MarketDataEngine
from monitor.notifier import notify_all, should_notify
from monitor.scraper import fetch_all_news

CN_TZ = ZoneInfo("Asia/Shanghai")


def run_once(force: bool = False) -> dict:
    now = datetime.now(CN_TZ)
    logger.info("=" * 60)
    logger.info("A-stock monitor v5 scan starting at %s", now.isoformat(timespec="seconds"))

    if not force and not _should_scan_market_window(now):
        logger.info("Skipped outside market window; keep the published dashboard unchanged.")
        return {"skipped": True, "dashboard": False, "reason": "outside_market_window"}

    market_data = _fetch_market_data()
    news_items = fetch_all_news()
    important, scored, sector_impact = score_news(news_items)
    recommendations = build_recommendations(scored, market_data)
    summary = build_summary(important, scored, recommendations, sector_impact)
    market_pulse = build_market_pulse(market_data, scored, sector_impact)
    data = {
        "summary": summary,
        "important_news": important,
        "scored_news": scored[:80],
        "sector_impact": sector_impact,
        "recommendations": recommendations,
        "market_data": market_data,
        "market_pulse": market_pulse,
        "automation": _automation_status(summary),
        "status": "running",
    }

    write_dashboard(data)
    auto_deploy()
    _append_history(important, recommendations, summary)
    push_result = _maybe_push(important, recommendations)

    result = {
        "skipped": False,
        "total_news": len(news_items),
        "matched": len(scored),
        "important": len(important),
        "recommendations": len(recommendations),
        "pushed": any(push_result.values()) if push_result else False,
    }
    logger.info("A-stock monitor v5 scan done: %s", result)
    logger.info("=" * 60)
    return result


def _fetch_market_data() -> dict:
    try:
        engine = MarketDataEngine()
        data = engine.fetch_all()
        logger.info("Market data fetched: %d sectors, %d gainers", len(data.get("sectors", [])), len(data.get("gainers", [])))
        return data
    except Exception as exc:
        logger.warning("Market data error (non-fatal): %s", exc)
        return {}


def _maybe_push(important: list[dict], recommendations: list[dict]) -> dict | None:
    if not important:
        return None
    fingerprint = notification_fingerprint(important, recommendations)
    if not should_notify(fingerprint):
        return None
    top = important[0]
    title = f"{top['level']}: {top['event']}"
    lines = [f"检测到 {len(important)} 条重大利好信号", ""]
    for item in important[:5]:
        sectors = "、".join(item.get("sectors", [])[:4])
        stocks = "、".join(item.get("stocks", [])[:4])
        lines.append(f"[{item['score']}] {item['title'][:72]}")
        if sectors:
            lines.append(f"板块: {sectors}")
        if stocks:
            lines.append(f"人气股: {stocks}")
    if recommendations:
        rec = recommendations[0]
        lines.extend([
            "",
            f"首选观察: {rec['stock']} / {rec['action_label']} / {rec['score']}",
            f"仓位上限: {rec['position_pct']}%  止损: {rec['stop_loss']}  止盈: {rec['take_profit']}",
            f"入场: {rec['entry']}",
        ])
    return notify_all(title, "\n".join(lines))


def _append_history(important: list[dict], recommendations: list[dict], summary: dict) -> None:
    try:
        history = []
        if HISTORY_PATH.exists():
            history = json.loads(HISTORY_PATH.read_text("utf-8")).get("history", [])
        for item in important[:8]:
            history.insert(
                0,
                {
                    "time": summary["timestamp"],
                    "title": item["title"][:90],
                    "score": item["score"],
                    "event": item["event"],
                    "sectors": item.get("sectors", [])[:4],
                    "top_stock": recommendations[0]["stock"] if recommendations else "",
                },
            )
        HISTORY_PATH.write_text(json.dumps({"history": history[:300], "last_scan": summary["timestamp"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("History save error: %s", exc)


def _should_scan_market_window(now: datetime) -> bool:
    if now.weekday() >= 5:
        return False
    current = now.time()
    return time(9, 20) <= current <= time(15, 5)


def _load_existing_or_empty(now: datetime, message: str) -> dict:
    if DATA_PATH.exists():
        try:
            data = json.loads(DATA_PATH.read_text("utf-8"))
            data["summary"]["timestamp"] = now.isoformat(timespec="seconds")
            data["status"] = message
            return data
        except Exception:
            pass
    summary = {
        "timestamp": now.isoformat(timespec="seconds"),
        "important_count": 0,
        "matched_count": 0,
        "sector_count": 0,
        "mood": {"label": "中性", "score": 50, "class": "neutral"},
        "top_stock": "",
        "top_action": "",
        "version": "v5",
        "scan_interval": "1分钟",
    }
    return {
        "summary": summary,
        "important_news": [],
        "scored_news": [],
        "sector_impact": {"sectors": [], "updated_at": now.isoformat(timespec="seconds")},
        "recommendations": [],
        "market_data": {},
        "market_pulse": {},
        "automation": _automation_status(summary),
        "status": message,
    }


def _automation_status(summary: dict) -> dict:
    return {
        "runtime": "GitHub Actions",
        "hosting": "GitHub Pages",
        "computer_required": False,
        "schedule": "A股交易日 09:20-15:05，北京时间",
        "target_interval": summary.get("scan_interval", "1分钟"),
        "note": "GitHub 定时任务由云端触发，可能有分钟级延迟；非交易时段不会覆盖最近有效看板。",
    }


if __name__ == "__main__":
    result = run_once(force=os.environ.get("FORCE_SCAN", "0") == "1")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        Path(github_output).write_text(
            f"should_deploy={'false' if result.get('skipped') else 'true'}\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
