import json
from html import escape

from .config import DASHBOARD_PATH, DATA_PATH, logger


def write_dashboard(data: dict) -> str:
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    DASHBOARD_PATH.write_text(_html(data), encoding="utf-8")
    logger.info("Dashboard generated: %s", DASHBOARD_PATH)
    return str(DASHBOARD_PATH)


def _html(data: dict) -> str:
    generated = escape(data["summary"]["timestamp"].replace("T", " "))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A股重大利好监控 v5</title>
<style>
:root {{
  --bg:#0b0f14; --panel:#111923; --panel2:#0f1720; --line:#223044;
  --text:#e7edf5; --muted:#7f8da3; --red:#ff5a66; --green:#27d17f;
  --amber:#ffc857; --blue:#58a6ff; --cyan:#56d4dd;
}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,#182238,#0b0f14 38%,#080b10);color:var(--text);font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif;font-size:14px;letter-spacing:0}}
.wrap{{max-width:1120px;margin:0 auto;padding:14px}} .top{{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:14px 0 12px;border-bottom:1px solid var(--line)}}
.brand{{font-size:22px;font-weight:800;color:var(--red)}} .sub{{color:var(--muted);font-size:12px;margin-top:4px;line-height:1.5}} .stamp{{text-align:right;color:var(--muted);font-size:11px;line-height:1.5}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}} .metric{{background:linear-gradient(180deg,var(--panel),#0d141c);border:1px solid var(--line);border-radius:8px;padding:10px;min-height:72px}}
.metric b{{display:block;font-size:22px;color:var(--red)}} .metric span{{font-size:11px;color:var(--muted)}} .band{{background:rgba(88,166,255,.08);border:1px solid rgba(88,166,255,.2);border-radius:8px;padding:10px 12px;margin-bottom:10px;color:#b8d7ff;line-height:1.45}}
.section{{margin:12px 0}} .title{{font-weight:700;color:#b9c7d8;margin:0 0 8px;font-size:13px}} .cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}} .card{{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:8px;padding:10px;min-width:0}}
.score{{display:inline-block;background:var(--red);color:white;font-weight:800;border-radius:5px;padding:1px 7px;font-size:11px;margin-right:6px}} .pill{{display:inline-block;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);border-radius:999px;padding:2px 7px;margin:2px 3px 2px 0;color:#aab7c8;font-size:10px;line-height:1.6}}
.headline{{line-height:1.45;margin:7px 0;color:#d9e4ef;word-break:break-word}} .meta{{color:var(--muted);font-size:11px;display:flex;gap:8px;flex-wrap:wrap}} a{{color:var(--blue);text-decoration:none}}
.rec{{border-left-color:var(--green)}} .rec.buy{{border-left-color:var(--amber)}} .rec.watch{{border-left-color:var(--blue)}} .rec.avoid{{border-left-color:#777}}
.row{{display:flex;justify-content:space-between;gap:8px;align-items:center}} .stock{{font-size:16px;font-weight:800}} .action{{font-size:12px;color:var(--green);font-weight:700;white-space:nowrap}} .plan{{font-size:11px;color:#9eacbd;line-height:1.55;margin-top:6px}}
.impact{{display:flex;gap:6px;flex-wrap:wrap}} .impact .pill{{color:#ffd78a;border-color:rgba(255,200,87,.25)}} .empty{{color:var(--muted);background:var(--panel);border:1px dashed var(--line);border-radius:8px;padding:14px;text-align:center}}
.foot{{color:#536176;text-align:center;font-size:11px;padding:18px 0;line-height:1.6}} @media(max-width:760px){{.grid{{grid-template-columns:repeat(2,1fr)}}.cards{{grid-template-columns:1fr}}.top{{display:block}}.stamp{{text-align:left;margin-top:8px}}}}
</style>
</head>
<body>
<main class="wrap">
  <header class="top">
    <div>
      <div class="brand">A股重大利好监控 <span style="font-size:12px;color:var(--muted)">v5</span></div>
      <div class="sub">新闻事件评分 / 板块影响 / 人气股交易计划 / 风险约束 / 手机推送</div>
    </div>
    <div class="stamp">当前页面生成 {generated}<br>GitHub Pages 自动发布</div>
  </header>
  <div id="app">{_render_body(data)}</div>
  <div class="foot">风险提示：本页是事件监控和交易计划辅助，不构成投资建议。默认单股仓位不超过12%，同一板块集中度需要自行控制。</div>
</main>
<script>
async function refreshData() {{
  try {{
    const res = await fetch('data.json?ts=' + Date.now());
    if (!res.ok) return;
    const data = await res.json();
    window.__DATA__ = data;
    render(data);
  }} catch (e) {{}}
}}
function esc(s) {{ return String(s ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function pills(items) {{ return (items || []).map(x => `<span class="pill">${{esc(x)}}</span>`).join(''); }}
function section(title, cards) {{ return `<section class="section"><h2 class="title">${{esc(title)}}</h2>${{cards.length ? `<div class="cards">${{cards.join('')}}</div>` : '<div class="empty">暂无达到阈值的信号</div>'}}</section>`; }}
function render(data) {{
  const s = data.summary || {{}};
  const topText = s.top_stock ? `当前首选观察：${{esc(s.top_stock)}} / ${{esc(s.top_action)}}` : '当前没有达到阈值的重大信号，系统保持观察。';
  const recs = (data.recommendations || []).slice(0, 10).map(r => `<article class="card rec ${{esc(r.action)}}">
    <div class="row"><div class="stock">#${{esc(r.rank)}} ${{esc(r.stock)}}</div><div class="action">${{esc(r.action_label)}} / ${{esc(r.score)}}</div></div>
    <div>${{pills(r.sectors)}}</div><div class="plan">仓位上限：${{esc(r.position_pct)}}% / 入场：${{esc(r.entry)}}<br>止损：${{esc(r.stop_loss)}} / 止盈：${{esc(r.take_profit)}} / 时间止损：${{esc(r.time_stop)}}</div>
    <div class="plan">${{pills((r.reasons || []).slice(0, 2))}}</div></article>`);
  const sectors = (((data.sector_impact || {{}}).sectors) || []).slice(0, 8).map(x => `<article class="card">
    <div class="row"><div class="stock">${{esc(x.sector)}}</div><div class="action">${{esc(x.score)}}</div></div>
    <div class="impact">${{pills(x.events)}}</div><div class="plan">关联股票：${{pills(x.stocks)}}</div></article>`);
  const news = (data.important_news || []).slice(0, 12).map(n => `<article class="card">
    <div><span class="score">${{esc(n.score)}}</span><span class="pill">${{esc(n.level)}}</span><span class="pill">${{esc(n.source)}}</span><span class="pill">${{esc(n.event)}}</span></div>
    <div class="headline">${{esc(n.title)}}</div><div>${{pills((n.sectors || []).slice(0, 4))}}</div><div>${{pills((n.matched_keywords || []).slice(0, 5))}}</div>
    <div class="meta"><span>${{esc(n.duration)}}</span><a href="${{esc(n.url)}}" target="_blank">原文</a></div></article>`);
  document.getElementById('app').innerHTML = `<section class="grid">
    <div class="metric"><b>${{esc(s.important_count || 0)}}</b><span>重大利好</span></div>
    <div class="metric"><b>${{esc(s.matched_count || 0)}}</b><span>匹配信号</span></div>
    <div class="metric"><b>${{esc(s.sector_count || 0)}}</b><span>影响板块</span></div>
    <div class="metric"><b>${{esc((s.mood || {{}}).score || 50)}}</b><span>情绪：${{esc((s.mood || {{}}).label || '中性')}}</span></div>
  </section><div class="band">${{topText}}<br>更新时间：${{esc((s.timestamp || '').replace('T', ' '))}} / 扫描频率：${{esc(s.scan_interval || '1分钟')}}</div>
  ${{section('人气股交易计划', recs)}}${{section('事件影响板块', sectors)}}${{section('重大利好新闻', news)}}`;
}}
refreshData();
setInterval(refreshData, 60000);
</script>
</body>
</html>"""


def _render_body(data: dict) -> str:
    summary = data["summary"]
    hero = f"当前首选观察：{summary['top_stock']} / {summary['top_action']}" if summary["top_stock"] else "当前没有达到阈值的重大信号，系统保持观察。"
    return f"""
  <section class="grid">
    <div class="metric"><b>{summary["important_count"]}</b><span>重大利好</span></div>
    <div class="metric"><b>{summary["matched_count"]}</b><span>匹配信号</span></div>
    <div class="metric"><b>{summary["sector_count"]}</b><span>影响板块</span></div>
    <div class="metric"><b>{summary["mood"]["score"]}</b><span>情绪：{escape(summary["mood"]["label"])}</span></div>
  </section>
  <div class="band">{escape(hero)}<br>更新时间：{escape(summary["timestamp"].replace("T", " "))} / 扫描频率：1分钟</div>
  {_recommendations(data)}
  {_sector_impacts(data)}
  {_news(data)}
"""


def _recommendations(data: dict) -> str:
    cards = []
    for row in data["recommendations"][:10]:
        cards.append(
            f'''<article class="card rec {escape(row["action"])}">
  <div class="row"><div class="stock">#{row["rank"]} {escape(row["stock"])}</div><div class="action">{escape(row["action_label"])} / {row["score"]}</div></div>
  <div>{_pills(row["sectors"])}</div>
  <div class="plan">仓位上限：{row["position_pct"]}% / 入场：{escape(row["entry"])}<br>止损：{escape(row["stop_loss"])} / 止盈：{escape(row["take_profit"])} / 时间止损：{escape(row["time_stop"])}</div>
  <div class="plan">{_pills(row["reasons"][:2])}</div>
</article>'''
        )
    return _section("人气股交易计划", cards)


def _sector_impacts(data: dict) -> str:
    cards = []
    for row in data["sector_impact"]["sectors"][:8]:
        cards.append(
            f'''<article class="card">
  <div class="row"><div class="stock">{escape(row["sector"])}</div><div class="action">{row["score"]}</div></div>
  <div class="impact">{_pills(row["events"])}</div>
  <div class="plan">关联股票：{_pills(row["stocks"])}</div>
</article>'''
        )
    return _section("事件影响板块", cards)


def _news(data: dict) -> str:
    cards = []
    for row in data["important_news"][:12]:
        cards.append(
            f'''<article class="card">
  <div><span class="score">{row["score"]}</span><span class="pill">{escape(row["level"])}</span><span class="pill">{escape(row["source"])}</span><span class="pill">{escape(row["event"])}</span></div>
  <div class="headline">{escape(row["title"])}</div>
  <div>{_pills(row["sectors"][:4])}</div>
  <div>{_pills(row["matched_keywords"][:5])}</div>
  <div class="meta"><span>{escape(row["duration"])}</span><a href="{escape(row["url"])}" target="_blank">原文</a></div>
</article>'''
        )
    return _section("重大利好新闻", cards)


def _pills(items: list[str]) -> str:
    return "".join(f'<span class="pill">{escape(item)}</span>' for item in items)


def _section(title: str, cards: list[str]) -> str:
    body = '<div class="empty">暂无达到阈值的信号</div>' if not cards else f'<div class="cards">{"".join(cards)}</div>'
    return f'<section class="section"><h2 class="title">{escape(title)}</h2>{body}</section>'
