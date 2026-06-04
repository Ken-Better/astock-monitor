#!/usr/bin/env python
"""Dashboard v4 - Dynamic auto-refresh with JS polling + data.json"""
from datetime import datetime
from .config import DASHBOARD_PATH, DATA_PATH, logger

STYLE = r"""
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
.tag-space{background:#1a1a2a;color:#7fc8ff;border:1px solid rgba(127,200,255,.3)}
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
.ch{display:flex;align-items:center;gap:5px;margin-bottom:4px;flex-wrap:wrap}
.sb2{background:#ff4444;color:#fff;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700}
.ll2{font-size:10px;color:#7a8a8a}
.sl2{margin-left:auto;font-size:9px;color:#4a5a6a;background:rgba(255,255,255,.04);padding:1px 6px;border-radius:3px}
.stags{display:flex;gap:3px;flex-wrap:wrap;margin-bottom:3px}
.stag{font-size:9px;background:rgba(255,255,255,.06);padding:1px 5px;border-radius:3px;color:#5a7a9a}
.ct{font-size:12px;color:#b0bcc0;line-height:1.4;margin:3px 0}
.ck{font-size:9px;color:#5a7a5a;margin:2px 0}
.cf{font-size:9px;color:#4a5a6a;display:flex;gap:8px;align-items:center;margin-top:2px}
.cf a{color:#3b82f6;text-decoration:none;font-size:9px}
.nb{background:#101a28;border-radius:10px;padding:12px 14px;margin-bottom:8px;border-left:3px solid #60a5fa}
.nbt{font-size:12px;color:#60a5fa;font-weight:600;margin-bottom:6px}
.nbgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:6px}
.nbi{text-align:center;padding:6px;background:rgba(255,255,255,.03);border-radius:8px}
.nbv{font-size:16px;font-weight:700}
.nbv-inflow{color:#22c55e}
.nbv-outflow{color:#ef4444}
.nbv-neutral{color:#60a5fa}
.nbl{font-size:8px;color:#5a6a7a;margin-top:2px}
.nbs{font-size:9px;color:#5a7a9a;padding:2px 0}
.nb-bar-wrap{display:flex;align-items:center;gap:8px;margin:4px 0}
.nb-bar-bg{flex:1;height:6px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden}
.nb-bar-fill{height:100%;border-radius:3px;transition:width 1s}
.nb-bar-inflow{background:linear-gradient(90deg,#22c55e,#4ade80)}
.nb-bar-outflow{background:linear-gradient(90deg,#ef4444,#f87171)}
.nb-bar-label{font-size:9px;color:#7a8a9a;min-width:36px;text-align:right}
.sp{background:#101a28;border-radius:10px;padding:12px 14px;margin-bottom:8px}
.spt{font-size:11px;color:#6a7a8a;font-weight:600;margin-bottom:4px}
.spr{display:grid;grid-template-columns:repeat(2,1fr);gap:3px}
.spi{display:flex;align-items:center;gap:4px;padding:2px 0;font-size:10px;border-bottom:1px solid rgba(255,255,255,.03)}
.spn{color:#aab0b8;min-width:0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.spv{font-size:10px;font-weight:600;min-width:42px;text-align:right}
.spv-up{color:#22c55e}
.spv-down{color:#ef4444}
.spf{font-size:8px;color:#3a4a5a;min-width:28px;text-align:right}
.ft{text-align:center;font-size:9px;color:#3a4a5a;padding:16px 0 24px;line-height:1.6}
"""  # noqa

def _tag(name):
    cls = "tag-gen"
    for kw, c in [("航天","tag-space"),("军工","tag-space"),("AI","tag-ai"),("人工","tag-ai"),
                   ("芯片","tag-chip"),("半导体","tag-chip"),("新能源","tag-ev"),
                   ("汽车","tag-ev"),("医药","tag-med"),("医疗","tag-med"),
                   ("金融","tag-fin"),("政策","tag-fin")]:
        if kw in name: cls = c; break
    return f'<span class="tag {cls}">{name}</span>'

def _render_news(news_list):
    cards = []
    for n in (news_list or []):
        secs = " ".join(_tag(s) for s in n.get("sectors",[]))
        stks = " ".join(f'<span class="stag">{s["name"]}</span>' for s in n.get("stocks",[])[:4])
        src_lbl = {"东方财富":"东方财富","财联社":"财联社","新浪财经":"新浪财经"}.get(n.get("source",""),n.get("source",""))
        cards.append(
            f'<div class="nc {n.get("level_class","level-low")}">'
            f'<div class="ch"><span class="sb2">{n["final_score"]}</span>'
            f'<span class="ll2">{n.get("level","利好")}</span>'
            f'<span class="sl2">{src_lbl}</span></div>'
            f'{secs}'
            f'<div class="ct">{n["title"]}</div>'
            f'<div class="ck">关键词: {" ".join(k["keyword"] for k in n.get("matched_keywords",[])[:4])}</div>'
            f'<div class="stags">{stks}</div>'
            f'<div class="cf"><span>{n["timestamp"][:19]}</span>'
            f'<a href="{n["url"]}" target="_blank">原文</a></div>'
            f'</div>'
        )
    if not cards:
        cards.append('<div class="nc level-low"><div class="ct" style="color:#5a6a7a">暂无利好信号</div></div>')
    return "".join(cards)

def _render_sectors(sectors):
    if not sectors: return ""
    html = '<div class="sp"><div class="spt">板块涨幅排行</div><div class="spr">'
    for s in sectors[:20]:
        name = s.get("name","")
        cp = s.get("change_pct",0) or 0
        vol = s.get("turnover_yuan",0) or 0
        vol_s = f'{vol/1e8:.0f}亿' if vol > 1e8 else f'{vol/1e4:.0f}万'
        cls = "spv-up" if cp > 0 else "spv-down"
        html += f'<div class="spi"><span class="spn">{name}</span><span class="spv {cls}">{cp:+.2f}%</span><span class="spf">{vol_s}</span></div>'
    return html + '</div></div>'

def _render_northbound(data):
    if not data: return ""
    net = data.get("total_net",0) or 0
    status = data.get("status","neutral")
    sh = data.get("sh_net",0) or 0
    sz = data.get("sz_net",0) or 0
    nb_cls = "nbv-inflow" if net > 1 else ("nbv-outflow" if net < -1 else "nbv-neutral")
    pct = min(100, max(0, (net/50)*100 + 50))
    fill_cls = "nb-bar-inflow" if net >= 0 else "nb-bar-outflow"
    label = "净流入" if net >= 0 else "净流出"
    return (
        f'<div class="nb">'
        f'<div class="nbt">🏦 北向资金</div>'
        f'<div class="nbgrid">'
        f'<div class="nbi"><div class="nbv {nb_cls}">{net:+.2f}亿</div><div class="nbl">合计{label}</div></div>'
        f'<div class="nbi"><div class="nbv" style="color:#60a5fa">{sh:+.2f}亿</div><div class="nbl">沪股通</div></div>'
        f'<div class="nbi"><div class="nbv" style="color:#60a5fa">{sz:+.2f}亿</div><div class="nbl">深股通</div></div>'
        f'</div>'
        f'<div class="nb-bar-wrap">'
        f'<div class="nb-bar-label">{label}</div>'
        f'<div class="nb-bar-bg"><div class="nb-bar-fill {fill_cls}" style="width:{pct:.0f}%"></div></div>'
        f'</div>'
        f'<div class="nbs">状态: {"外资流入" if net>1 else ("外资流出" if net<-1 else "中性")} | 更新时间: {data.get("updated","")[:19]}</div>'
        f'</div>'
    )

def _render_recommendations(recs):
    if not recs: return ""
    cards = []
    for i, r in enumerate(recs[:9], 1):
        action = r.get("action","watch")
        stock = r.get("stock","")
        sectors = r.get("sectors",[])
        confidence = r.get("confidence","low")
        risk = r.get("risk_rating","medium")
        pos = r.get("suggested_position_pct",0)
        f1 = r.get("factor1_news_score",0)
        f2 = r.get("factor2_sector_score",0)
        f3 = r.get("factor3_capital_score",0)
        reasons = r.get("reasons",[])
        comp = r.get("composite_score",0)
        action_label = {"strong_buy":"强买","buy":"买入","watch":"关注","info":"参考"}.get(action,action)
        sector_tags = "".join(f'<span class="rsec">{s}</span>' for s in sectors[:2])
        cards.append(
            f'<div class="ri ri-{action}">'
            f'<div class="rn"><span class="rnk">#{i}</span>{stock} <span class="ra ra-{action}">{action_label}</span></div>'
            f'<div class="rcf">{sector_tags}<span class="rconf-{confidence}">{confidence}</span><span class="rrisk-{risk}">{"较低风险" if risk=="low" else ("中等风险" if risk=="medium" else "较高风险")}</span><span class="rpos-tag">{pos}%</span>'
            f'<span style="color:#5a7a6a;font-size:9px">| {comp}分</span></div>'
            f'<div class="rrea">{reasons[0][:30] if reasons else ""}</div>'
            f'<div class="rf">'
            f'<span class="rf-item"><span class="rf-dot" style="background:#ff6b6b"></span>消息:{f1}</span>'
            f'<span class="rf-item"><span class="rf-dot" style="background:#fbbf24"></span>板块:{f2}</span>'
            f'<span class="rf-item"><span class="rf-dot" style="background:#60a5fa"></span>资金:{f3}</span>'
            f'</div></div>'
        )
    return (
        '<div class="rc">'
        '<div class="rh"><div class="rt">多因子推荐</div></div>'
        f'<div class="rg">{"".join(cards)}</div></div>'
    )

def _build_data_json(bullish_news, all_news, mood, hot_sectors, auto_keywords, hot_topics, recs, market_data):
    """Build JSON data for JS auto-polling"""
    now = datetime.now().isoformat()
    imp = len(bullish_news)
    total = len(all_news) if all_news else 0
    all_secs = set()
    for n in (bullish_news or []):
        for s in n.get("sectors",[]):
            all_secs.add(s)
    sc = len(all_secs)
    mc = mood.get("mood","neutral") if mood else "neutral"
    ms = int(mood.get("score",50)) if mood else 50
    mood_label = {"very_positive":"非常乐观","positive":"偏乐观","neutral":"中性",
                  "cautious":"偏谨慎","negative":"偏悲观"}.get(mc,"中性")

    data = {
        "timestamp": now,
        "imp": imp, "total": total, "sectors_count": sc,
        "mood": mc, "mood_score": ms, "mood_label": mood_label,
        "bullish_news": [],
        "sectors": [s.get("name","") for s in (market_data.get("sectors",[]) if market_data else [])[:15]],
        "sector_perf": [{"n": s.get("name",""),"c": s.get("change_pct",0) or 0}
                       for s in (market_data.get("sectors",[]) if market_data else [])[:20]],
        "hot_sectors": (hot_sectors or [])[:8],
        "auto_keywords": (auto_keywords or [])[:8],
        "hot_topics": (hot_topics or [])[:3],
        "recommendations": [],
        "northbound": None,
        "news_sectors": sorted(all_secs),
        "source": "东方财富 财联社 新浪财经",
    }

    if market_data:
        data["northbound"] = market_data.get("northbound")

    for n in (bullish_news or []):
        data["bullish_news"].append({
            "title": n["title"], "url": n["url"], "source": n.get("source",""),
            "score": n["final_score"], "level": n.get("level","利好"),
            "level_class": n.get("level_class","level-low"),
            "sectors": n.get("sectors",[]),
            "stocks": [s["name"] for s in n.get("stocks",[])[:4]],
            "keywords": [k["keyword"] for k in n.get("matched_keywords",[])[:4]],
            "timestamp": n["timestamp"][:19],
        })

    for r in (recs or []):
        data["recommendations"].append({
            "rank": r.get("rank",0), "stock": r.get("stock",""),
            "action": r.get("action",""), "composite": r.get("composite_score",0),
            "confidence": r.get("confidence",""), "risk": r.get("risk_rating",""),
            "pos_pct": r.get("suggested_position_pct",0),
            "sectors": r.get("sectors",[])[:2],
            "f1": r.get("factor1_news_score",0),
            "f2": r.get("factor2_sector_score",0),
            "f3": r.get("factor3_capital_score",0),
            "reasons": r.get("reasons",[])[:1],
        })

    return data

def generate_dashboard(bullish_news, all_news=None, mood=None, hot_sectors=None,
                       auto_keywords=None, hot_topics=None, recommendations=None,
                       market_data=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    imp = len(bullish_news)
    total = len(all_news) if all_news else 0

    all_secs = set()
    for n in (bullish_news or []):
        for s in n.get("sectors",[]):
            all_secs.add(s)
    sc = len(all_secs)

    mood = mood or {}
    mc = mood.get("mood","neutral")
    mlbl = {"very_positive":"非常乐观","positive":"偏乐观","neutral":"中性",
            "cautious":"偏谨慎","negative":"偏悲观"}.get(mc,"中性")
    ms = int(mood.get("score",50))

    stags = ""
    if all_secs:
        stags = f'<div class="tagbar">{"".join(_tag(s) for s in sorted(all_secs))}</div>'

    hs = ""
    if hot_sectors:
        secs = "".join(f'<span class="heat-item">{s}</span>' for s in hot_sectors[:8])
        hs = f'<div class="hsect"><div class="hstitle">热点板块</div><div class="heat-row">{secs}</div></div>'

    akw = ""
    if auto_keywords:
        kws = " ".join(f'<span class="heat-item">{k}</span>' for k in auto_keywords[:5])
        akw = f'<span style="color:#5a6a7a;font-size:10px"> | 热点词 {kws}</span>'

    ht = ""
    if hot_topics:
        topics = " ".join(f'<span class="heat-item" style="color:#ff8c00">{t}</span>' for t in hot_topics[:3])
        ht = f'<div class="hstitle">热门话题</div><div class="heat-row">{topics}</div>'

    heat = hs
    if ht:
        heat += f'<div class="hsect">{ht}</div>'

    sector_section = _render_sectors(market_data.get("sectors",[]) if market_data else [])
    nb_section = _render_northbound(market_data.get("northbound") if market_data else None)
    rec_html = _render_recommendations(recommendations)

    dc = "#22c55e" if bullish_news else "#3b82f6"
    st = (f"<div class='sb'>"
          f"<div class='sd' style='background:{dc}'></div>"
          f"<span class='st'>"
          + (f"检测到 {imp} 条利好 · {sc} 个行业" if bullish_news else "监控运行中")
          + f"</span>{akw}</div>")

    cards = _render_news(bullish_news)

    # Build JS auto-refresh script
    js_code = r"""
<script>
// Dynamic auto-refresh: poll data.json every 10 seconds
(function(){
  var lastData = null;
  var pollInterval = 10000; // 10 seconds

  function updateDisplay(data) {
    // Update timestamp
    var els = document.querySelectorAll('.ls');
    if (els.length) {
      els[0].innerHTML = data.timestamp ? '更新: ' + data.timestamp.slice(0,19).replace('T',' ') + ' \u00b7 实时刷新' : els[0].innerHTML;
    }
  }

  function fetchData() {
    var t = new Date().getTime();
    fetch('/data.json?t=' + t, {cache: 'no-store'})
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (JSON.stringify(d) !== JSON.stringify(lastData)) {
          lastData = d;
          updateDisplay(d);
          // Full page reload if the data is significantly different (new scan deployed)
          var oldTime = document.querySelector('.ls');
          if (oldTime) {
            var oldText = oldTime.innerHTML;
            var newTime = d.timestamp ? d.timestamp.slice(0,19).replace('T',' ') : '';
            if (newTime && oldText.indexOf(newTime) === -1) {
              // Content changed - reload to show latest
              setTimeout(function(){ location.reload(); }, 3000);
            }
          }
        }
      })
      .catch(function(e){ /* silently retry */ });
  }

  // Poll on interval
  setInterval(fetchData, pollInterval);
  // Also check for meta refresh
  setTimeout(function(){
    // Try to detect if data.json is newer than current page
    fetchData();
  }, 5000);

  // Also do a full page refresh every 5 minutes as fallback
  setTimeout(function(){ location.reload(); }, 300000);
})();
</script>
"""

    html = (
        '<!DOCTYPE html><html lang="zh-CN"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">'
        '<title>A股利好监控 v4</title><style>' + STYLE + '</style>'
        '</head><body><div class="c">'
        '<div class="h">'
        '<div style="display:flex;justify-content:space-between;align-items:center">'
        '<div><div class="ht">A股利好监控<span style="font-size:10px;color:#5a6a7a">v4</span></div>'
        '<div class="hs">自学习引擎 · 热点追踪 · 机构动向</div></div>'
        f'<span class="mb mb-{mc}">{mlbl}</span>'
        '</div>'
        f'<div class="grid">'
        f'<div class="gi"><div class="gv">{imp}</div><div class="gl">利好</div></div>'
        f'<div class="gi"><div class="gv">{total}</div><div class="gl">匹配</div></div>'
        f'<div class="gi"><div class="gv">{sc}</div><div class="gl">行业</div></div>'
        f'<div class="gi"><div class="gv">{ms}</div><div class="gl">情绪</div></div>'
        '</div>'
        f'<div class="ls">更新: {now} · 实时刷新</div>'
        '</div>'
        + heat + sector_section + nb_section + rec_html + st + stags + cards +
        '<div class="ft">'
        'Codex v4 自进化 · 1min/次 · 东方财富 · 财联社 · 新浪财经<br>'
        '自动发现新关键词 · 多维度热度评分 · 行业板块追踪 · 智能推荐'
        '</div></div>'
        + js_code + '</body></html>'
    )

    DASHBOARD_PATH.write_text(html, encoding="utf-8")

    # Also save data.json for auto-polling
    data = _build_data_json(bullish_news, all_news or [], mood, hot_sectors, auto_keywords, hot_topics, recommendations, market_data)
    DATA_PATH.write_text(__import__("json").dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(f"Dashboard v4 generated: {DASHBOARD_PATH} + {DATA_PATH}")
    return str(DASHBOARD_PATH)
