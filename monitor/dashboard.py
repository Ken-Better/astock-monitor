#!/usr/bin/env python
"""
A股利好监控 v3 — 增强版看板生成器
"""
from datetime import datetime
from .config import DASHBOARD_PATH, INTERVAL_MINUTES, logger

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>A股利好监控 v3</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#080c12;color:#e0e6ed;font-size:14px}
.c{max-width:860px;margin:0 auto;padding:12px}
.h{background:linear-gradient(135deg,#101a28,#0a1420);border-radius:14px;padding:20px;margin-bottom:10px;border:1px solid rgba(255,75,75,.15)}
.ht{font-size:20px;font-weight:700;color:#ff6b6b}
.hs{font-size:11px;color:#6a7a8a;margin-top:2px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:12px}
.gi{text-align:center;padding:6px;background:rgba(255,255,255,.03);border-radius:8px}
.gv{font-size:17px;font-weight:700;color:#ff6b6b}
.gl{font-size:9px;color:#5a6a7a;margin-top:1px}
.ls{font-size:9px;color:#3a4a5a;text-align:right;margin-top:6px}
.mb{display:inline-block;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:600}
.mb-positive{background:rgba(34,197,94,.15);color:#22c55e}
.mb-very-positive{background:rgba(34,197,94,.2);color:#4ade80}
.mb-neutral{background:rgba(59,130,246,.15);color:#60a5fa}
.mb-cautious{background:rgba(251,191,36,.15);color:#fbbf24}
.mb-negative{background:rgba(239,68,68,.15);color:#ef4444}
.tagbar{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0}
.tag{padding:2px 9px;border-radius:10px;font-size:10px;font-weight:500}
.tag-hot{background:#2a1520;color:#ff6b6b;border:1px solid rgba(255,107,107,.3)}
.tag-chip{background:#1a2a30;color:#4fc3f7;border:1px solid rgba(79,195,247,.3)}
.tag-ai{background:#1a1a30;color:#b388ff;border:1px solid rgba(179,136,255,.3)}
.tag-ev{background:#1a2a20;color:#69f0ae;border:1px solid rgba(105,240,174,.3)}
.tag-med{background:#2a1a28;color:#f48fb1;border:1px solid rgba(244,143,177,.3)}
.tag-fin{background:#1a2020;color:#ffd54f;border:1px solid rgba(255,213,79,.3)}
.tag-gen{background:#1a1a1a;color:#90a4ae;border:1px solid rgba(144,164,174,.3)}
.sb{background:#101a28;border-radius:8px;padding:8px 12px;margin-bottom:8px;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.sd{width:7px;height:7px;border-radius:50%;animation:pulse 2s infinite;flex-shrink:0}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.st{font-size:11px;color:#7a8a9a}
.hsect{background:#101a28;border-radius:10px;padding:12px 14px;margin-bottom:8px}
.hstitle{font-size:12px;color:#8a9aaa;font-weight:600;margin-bottom:6px}
.heat-row{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0}
.heat-item{background:rgba(255,255,255,.04);padding:3px 8px;border-radius:6px;font-size:11px;color:#b0b8c0}
.rc{background:#0f1a18;border-radius:10px;padding:12px 14px;margin-bottom:8px;border:1px solid rgba(52,211,153,.15)}
.rh{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.rt{font-size:12px;color:#34d399;font-weight:600}
.rg{display:grid;grid-template-columns:repeat(2,1fr);gap:6px}
.ri{background:rgba(255,255,255,.03);border-radius:8px;padding:8px 10px;border-left:3px solid #34d399}
.ri-strong_buy{border-left-color:#22c55e;background:linear-gradient(135deg,#0f1a18,#0a1a10)}
.ri-buy{border-left-color:#34d399}
.ri-watch{border-left-color:#fbbf24}
.ri-info{border-left-color:#3b82f6}
.rn{font-size:13px;font-weight:600;color:#e0e6ed;display:flex;align-items:center;gap:4px}
.rnk{font-size:9px;color:#5a7a6a;font-weight:400}
.ra{display:inline-block;padding:1px 6px;border-radius:4px;font-size:9px;font-weight:600}
.ra-strong_buy{background:rgba(34,197,94,.2);color:#22c55e}
.ra-buy{background:rgba(52,211,153,.15);color:#34d399}
.ra-watch{background:rgba(251,191,36,.15);color:#fbbf24}
.ra-info{background:rgba(59,130,246,.15);color:#60a5fa}
.rcf{display:flex;gap:4px;align-items:center;margin-top:4px;flex-wrap:wrap}
.rsec{font-size:9px;background:rgba(255,255,255,.06);padding:1px 5px;border-radius:3px;color:#5a8a7a}
.rconf-high{color:#22c55e;font-size:9px}
.rconf-medium{color:#fbbf24;font-size:9px}
.rconf-low{color:#60a5fa;font-size:9px}
.rconf-watch{color:#5a6a7a;font-size:9px}
.rrisk-low{color:#22c55e;font-size:9px}
.rrisk-medium{color:#fbbf24;font-size:9px}
.rrisk-high{color:#ef4444;font-size:9px}
.rrisk-very_high{color:#dc2626;font-size:9px}
.rpos{font-size:9px;color:#a78bfa}
.rrea{font-size:9px;color:#6a7a7a;margin-top:3px;line-height:1.3}
@media(min-width:600px){.rg{grid-template-columns:repeat(3,1fr)}}
.nc{background:#101a28;border-radius:8px;padding:10px 12px;margin-bottom:6px;border-left:3px solid #2a3a4a}
.level-high{border-left-color:#ff4444;background:linear-gradient(135deg,#101a28,#1a0e0e)}
.level-mid{border-left-color:#ff8c00;background:linear-gradient(135deg,#101a28,#1a1610)}
.level-low{border-left-color:#3b82f6}
.level-info{border-left-color:#2a3a4a}
.ch{display:flex;align-items:center;gap:5px;margin-bottom:4px;flex-wrap:wrap}
.sb2{background:#ff4444;color:#fff;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700}
.ll2{font-size:12px;font-weight:600;color:#e0e6ed}
.sl2{font-size:10px;color:#5a6a7a;margin-left:auto}
.ct{font-size:13px;color:#c0c8d0;margin:5px 0;line-height:1.4}
.ck{display:flex;flex-wrap:wrap;gap:3px;margin:3px 0}
.ck span{background:rgba(255,255,255,.05);padding:0 6px;border-radius:3px;font-size:10px;color:#5a7a8a}
.stags{display:flex;flex-wrap:wrap;gap:3px;margin:3px 0}
.stag{background:rgba(59,130,246,.1);padding:0 6px;border-radius:3px;font-size:10px;color:#60a5fa}
.cf{display:flex;gap:8px;margin-top:4px;font-size:10px;color:#3a4a5a;align-items:center}
.ft{font-size:10px;color:#2a3a3a;text-align:center;margin-top:12px;padding:10px;border-top:1px solid #0a121a}
.se{background:#101a28;border-radius:10px;padding:12px 14px;margin-bottom:8px;overflow-x:auto}
.set{font-size:12px;color:#8a9aaa;font-weight:600;margin-bottom:6px}
.ser{display:flex;gap:0;min-width:500px}
.sec{flex:1;text-align:center;padding:6px 2px;font-size:10px}
.sec-h{color:#22c55e;font-weight:600}
.sec-m{color:#fbbf24}
.sec-l{color:#ef4444}
.sev{font-size:11px;font-weight:700}
.sel{font-size:8px;color:#4a5a5a;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nb{background:#101a28;border-radius:10px;padding:12px 14px;margin-bottom:8px}
.nbt{font-size:12px;color:#8a9aaa;font-weight:600;margin-bottom:6px}
.nbgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0}
.nbi{text-align:center;background:rgba(255,255,255,.02);padding:6px;border-radius:6px}
.nbv{font-size:16px;font-weight:700}
.nbv-inflow{color:#22c55e}
.nbv-outflow{color:#ef4444}
.nbv-neutral{color:#60a5fa}
.nbl{font-size:9px;color:#4a5a5a;margin-top:2px}
.nb-bar-wrap{display:flex;align-items:center;gap:8px;margin:8px 0}
.nb-bar-bg{flex:1;height:6px;background:#1a2a2a;border-radius:3px;overflow:hidden}
.nb-bar-fill{height:100%;border-radius:3px;transition:width 0.5s}
.nb-bar-fill.inflow{background:linear-gradient(90deg,#22c55e,#4ade80)}
.nb-bar-fill.outflow{background:linear-gradient(90deg,#ef4444,#dc2626)}
.nbs{font-size:10px;color:#3a4a5a;text-align:center;margin-top:4px}
.rf{display:flex;gap:8px;margin-top:4px;flex-wrap:wrap}
.rf-item{display:flex;align-items:center;gap:3px;font-size:9px;color:#5a6a7a}
.rf-dot{width:5px;height:5px;border-radius:50%}
.rpos-tag{font-size:9px;color:#a78bfa}
</style>
</head>
<body>
<div class="c">
<div class="h">
<div class="ht">A股利好监控 v3</div>
<div class="hs">{now} · 云扫描 · {src}</div>
<div class="grid">
<div class="gi"><div class="gv">{imp}</div><div class="gl">利好信号</div></div>
<div class="gi"><div class="gv">{total}</div><div class="gl">总扫描</div></div>
<div class="gi"><div class="gv">{sc}</div><div class="gl">涉及行业</div></div>
<div class="gi"><div class="gv">{ms}</div><div class="gl">情绪评分</div></div>
</div>
</div>
{sb}
{sector_tags}
{heat_section}
{sector_section}
{northbound_section}
{recommendation_section}
{news_feed}
<div class="ft">GitHub Actions · 5min/次 · 东方财富 · 财联社 · 新浪财经<br>自发现新关键词 · 多维度热度评分 · 行业板块追踪 · 智能推荐</div>
</div>
</body>
</html>
"""


def _tag(sector):
    tmap = {
        "航天军工": "tag-hot", "芯片半导体": "tag-chip", "AI人工智能": "tag-ai",
        "新能源汽车": "tag-ev", "医药医疗": "tag-med", "金融政策": "tag-fin",
        "新能源/储能": "tag-ev", "信创/国产替代": "tag-chip",
    }
    cls = tmap.get(sector, "tag-gen")
    return '<span class="tag %s">%s</span>' % (cls, sector)


def _render_news(news_list):
    cards = ""
    for n in news_list:
        lvl = n.get("level_class", "level-info")
        score = n.get("final_score", 0)
        source = n.get("source", "?")
        title = n.get("title", "")
        url = n.get("url", "")
        sectors = n.get("sectors", [])
        stocks = n.get("stocks", [])
        kws = [k["keyword"] for k in n.get("matched_keywords", [])[:4]]
        ts = n.get("timestamp", "")[11:16]
        tags = "".join(_tag(s) for s in sectors)
        stks = "".join('<span class="stag">%s</span>' % s["name"] for s in stocks[:4])
        kws_html = '<div class="ck">%s</div>' % "".join('<span>%s</span>' % k for k in kws) if kws else ""
        cards += (
            '<div class="nc %s">'
            '<div class="ch">'
            '<span class="sb2">%.1f</span>'
            '<span class="ll2">%s</span>'
            '<span class="sl2">%s</span>'
            '</div>'
            '%s'
            '<div class="ct">%s</div>'
            '%s'
            '<div class="stags">%s</div>'
            '<div class="cf"><span>%s</span>%s</div>'
            '</div>\n'
        ) % (lvl, score, n.get("level", ""), source,
             tags, title, kws_html, stks,
             ts,
             '<a href="%s" target="_blank" style="color:#3b82f6">原文</a>' % url if url else "")
    return cards


def _render_sector_section(sectors):
    if not sectors:
        return ""
    rows = ""
    for s in sectors[:10]:
        pct = s.get("change_pct", 0) or 0
        cls = "sec-h" if pct > 2 else ("sec-m" if pct > 0 else "sec-l")
        rows += '<div class="sec"><div class="sev %s">%+.2f%%</div><div class="sel">%s</div></div>' % (
            cls, pct, s.get("name", ""))
    return (
        '<div class="se">'
        '<div class="set">板块涨幅排行</div>'
        '<div class="ser">%s</div>'
        '</div>'
    ) % rows


def _render_northbound_section(nb_data):
    if not nb_data:
        return ""
    total_net = nb_data.get("total_net", 0) or 0
    total_accum = nb_data.get("total_accum", 0) or 0
    sh = nb_data.get("sh_net", 0) or 0
    sz = nb_data.get("sz_net", 0) or 0
    status = nb_data.get("status", "neutral")
    cls = "nbv-inflow" if status == "inflow" else ("nbv-outflow" if status == "outflow" else "nbv-neutral")
    bar_cls = "inflow" if status == "inflow" else "outflow"
    bar_pct = min(100, max(5, abs(total_net) * 8 + 50))
    status_text = {"inflow": "资金净流入", "outflow": "资金净流出", "neutral": "资金平稳"}.get(status, "资金平稳")
    total_str = f"{total_net:+.2f}亿" if abs(total_net) > 0 else "暂无数据"
    return (
        '<div class="nb">'
        '<div class="nbt">北向资金</div>'
        '<div class="nbgrid">'
        '<div class="nbi"><div class="nbv %s">%s</div><div class="nbl">当日净流入</div></div>'
        '<div class="nbi"><div class="nbv %s">%+.2f亿</div><div class="nbl">沪股通</div></div>'
        '<div class="nbi"><div class="nbv %s">%+.2f亿</div><div class="nbl">深股通</div></div>'
        '</div>'
        '<div class="nb-bar-wrap">'
        '<span style="font-size:10px;color:#4a5a5a">流出</span>'
        '<div class="nb-bar-bg"><div class="nb-bar-fill %s" style="width:%s%%"></div></div>'
        '<span style="font-size:10px;color:#4a5a5a">流入</span>'
        '</div>'
        '<div class="nbs">%s: 当日%s</div>'
        '</div>'
    ) % (cls, total_str, cls, sh, cls, sz, bar_cls, bar_pct, status_text, total_str)


def _render_recommendations_v2(recommendations):
    if not recommendations:
        return ""
    cards = ""
    for r in recommendations[:6]:
        rank = r.get("rank", 0)
        stock = r.get("stock", "")
        action = r.get("action", "watch")
        comp = r.get("composite_score", 0)
        sectors = r.get("sectors", [])
        confidence = r.get("confidence", "low")
        risk = r.get("risk_rating", "medium")
        pos = r.get("suggested_position_pct", 0)
        f1 = r.get("factor1_news_score", 0)
        f2 = r.get("factor2_sector_score", 0)
        f3 = r.get("factor3_capital_score", 0)
        reasons = r.get("reasons", [])
        action_label = {"strong_buy": "强买", "buy": "买入", "watch": "关注", "info": "参考"}.get(action, action)
        sector_tags = "".join('<span class="rsec">%s</span>' % s for s in sectors[:2])
        cards += (
            '<div class="ri ri-%s">'
            '<div class="rn"><span class="rnk">#%d</span>%s <span class="ra ra-%s">%s</span></div>'
            '<div class="rcf">%s<span class="rconf-%s">%s</span><span class="rrisk-%s">%s</span><span class="rpos-tag">%s%%</span>'
            '<span style="color:#5a6a7a;font-size:9px">| %s分</span></div>'
            '<div class="rrea">%s</div>'
            '<div class="rf">'
            '<span class="rf-item"><span class="rf-dot" style="background:#ff6b6b"></span>消息:%s</span>'
            '<span class="rf-item"><span class="rf-dot" style="background:#fbbf24"></span>板块:%s</span>'
            '<span class="rf-item"><span class="rf-dot" style="background:#60a5fa"></span>资金:%s</span>'
            '</div>'
            '</div>'
        ) % (action, rank, stock, action, action_label,
             sector_tags, confidence, confidence, risk, risk, pos, comp,
             reasons[0][:30] if reasons else "",
             f1, f2, f3)
    return (
        '<div class="rc">'
        '<div class="rh"><div class="rt">多因子推荐</div></div>'
        '<div class="rg">%s</div>'
        '</div>'
    ) % cards


def generate_dashboard(bullish_news, all_news=None, mood=None, hot_sectors=None,
                       auto_keywords=None, hot_topics=None, recommendations=None,
                       market_data=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    imp = len(bullish_news)
    total = len(all_news) if all_news else 0

    all_secs = set()
    for n in (bullish_news or []):
        for s in n.get("sectors", []):
            all_secs.add(s)
    sc = len(all_secs)

    mood = mood or {}
    mc = mood.get("mood", "neutral")
    mlbl = {"very_positive": "非常乐观", "positive": "偏乐观", "neutral": "中性",
            "cautious": "偏谨慎", "negative": "偏悲观"}.get(mc, "中性")
    ms = int(mood.get("score", 50))

    stags = ""
    if all_secs:
        stags = '<div class="tagbar">%s</div>' % "".join(_tag(s) for s in sorted(all_secs))

    hs = ""
    if hot_sectors:
        secs = "".join('<span class="heat-item">%s</span>' % s for s in hot_sectors[:8])
        hs = '<div class="hsect"><div class="hstitle">热点板块</div><div class="heat-row">%s</div></div>' % secs

    akw = ""
    if auto_keywords:
        kws = " ".join('<span class="heat-item">%s</span>' % k for k in auto_keywords[:5])
        akw = '<span style="color:#5a6a7a;font-size:10px"> | 热点词: %s</span>' % kws

    ht = ""
    if hot_topics:
        topics = " ".join('<span class="heat-item" style="color:#ff8c00">%s</span>' % t for t in hot_topics[:3])
        ht = '<div class="hstitle">热门话题</div><div class="heat-row">%s</div>' % topics

    heat = hs
    if ht:
        heat += '<div class="hsect">%s</div>' % ht

    sectors = []
    if market_data:
        sectors = market_data.get("sectors", [])
    sector_section = _render_sector_section(sectors)

    nb_data = None
    if market_data:
        nb_data = market_data.get("northbound", None)
    nb_section = _render_northbound_section(nb_data)

    rec_html = _render_recommendations_v2(recommendations)

    dc = "#22c55e" if bullish_news else "#3b82f6"
    st = ("<div class='sb'>"
          "<div class='sd' style='background:%s'></div>"
          "<span class='st'>%s</span>%s"
          "</div>") % (dc, "检测到 %s 条利好 · %s 个行业" % (imp, sc) if bullish_news else "监控运行中", akw)
    cards = _render_news(bullish_news)
    sr = "东方财富 · 财联社 · 新浪财经"

    html = TEMPLATE.replace("{imp}", str(imp)).replace("{total}", str(total))
    html = html.replace("{sc}", str(sc)).replace("{now}", now)
    html = html.replace("{ms}", str(ms))
    html = html.replace("{sb}", st)
    html = html.replace("{sector_tags}", stags)
    html = html.replace("{heat_section}", heat)
    html = html.replace("{sector_section}", sector_section)
    html = html.replace("{northbound_section}", nb_section)
    html = html.replace("{recommendation_section}", rec_html)
    html = html.replace("{news_feed}", cards)
    html = html.replace("{src}", sr)

    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    logger.info("Dashboard v3 generated: %s" % DASHBOARD_PATH)
    return str(DASHBOARD_PATH)
