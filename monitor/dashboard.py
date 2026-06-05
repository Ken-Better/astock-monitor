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
    initial_json = json.dumps(data, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A股重大利好监控 v5.2</title>
<style>
:root {{
  --bg:#000000; --panel:#090b0d; --panel2:#0d1115; --line:#26313a;
  --text:#e7edf5; --muted:#7b8794; --green:#00e676; --red:#ff3b30;
  --amber:#ffb800; --blue:#58a6ff; --soft:#111820;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:"JetBrains Mono","IBM Plex Mono","Consolas","Microsoft YaHei",monospace;font-size:13px;letter-spacing:0;font-variant-numeric:tabular-nums}}
a{{color:var(--blue);text-decoration:none}}
.wrap{{max-width:1280px;margin:0 auto;padding:12px}}
.top{{display:grid;grid-template-columns:1fr auto;gap:12px;border:1px solid var(--line);background:var(--panel);padding:12px}}
.brand{{font-size:22px;font-weight:800;color:var(--green)}} .sub{{color:var(--muted);font-size:12px;margin-top:4px;line-height:1.6}}
.status{{text-align:right;color:var(--muted);font-size:11px;line-height:1.7}}
.dot{{display:inline-block;width:8px;height:8px;background:var(--green);border-radius:50%;margin-right:6px;box-shadow:0 0 10px var(--green)}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:8px 0}}
.metric,.panel,.card{{background:var(--panel);border:1px solid var(--line);border-radius:0}}
.metric{{padding:10px;min-height:72px}} .metric b{{display:block;font-size:22px;color:var(--green)}} .metric span{{font-size:11px;color:var(--muted)}}
.layout{{display:grid;grid-template-columns:1.3fr .9fr;gap:8px}} .section{{margin:8px 0}} .title{{font-size:12px;color:#aeb8c4;margin:0;padding:8px 10px;border-bottom:1px solid var(--line);background:var(--soft)}}
.panelBody{{padding:10px}} .cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}} .card{{padding:10px;border-left:3px solid var(--blue);min-width:0}}
.rec.strong_buy{{border-left-color:var(--green)}} .rec.buy{{border-left-color:var(--amber)}} .rec.watch{{border-left-color:var(--blue)}}
.row{{display:flex;align-items:center;justify-content:space-between;gap:8px}} .stock{{font-size:15px;font-weight:800}} .action{{font-size:12px;color:var(--green);white-space:nowrap}}
.pill{{display:inline-block;border:1px solid var(--line);background:#050708;padding:2px 6px;margin:2px 3px 2px 0;font-size:10px;color:#aeb8c4;line-height:1.6}}
.score{{display:inline-block;background:var(--green);color:#00170a;font-weight:800;padding:1px 6px;margin-right:6px}}
.headline{{line-height:1.55;margin:7px 0;color:#dbe5ef;word-break:break-word}} .meta,.plan{{font-size:11px;color:var(--muted);line-height:1.6;margin-top:6px}}
.factor{{display:grid;grid-template-columns:88px 1fr 38px;gap:6px;align-items:center;margin:4px 0;font-size:10px;color:var(--muted)}} .bar{{height:6px;background:#101820;border:1px solid #1d2a32}} .bar i{{display:block;height:100%;background:var(--green);width:0}}
.table{{width:100%;border-collapse:collapse;font-size:11px}} .table td{{border-bottom:1px solid #172029;padding:6px 4px;color:#b8c2cf}} .table td:last-child{{text-align:right;color:var(--green)}}
.band{{border:1px solid var(--line);background:#06110a;color:#b7ffd5;padding:10px;margin:8px 0;line-height:1.6}}
.empty{{color:var(--muted);border:1px dashed var(--line);padding:12px;text-align:center;background:#050708}}
.foot{{color:#647180;text-align:center;font-size:11px;line-height:1.6;padding:18px 0}}
@media(max-width:980px){{.layout{{grid-template-columns:1fr}}.grid{{grid-template-columns:repeat(3,1fr)}}.cards{{grid-template-columns:1fr}}.top{{grid-template-columns:1fr}}.status{{text-align:left}}}}
@media(max-width:560px){{.grid{{grid-template-columns:repeat(2,1fr)}}.wrap{{padding:8px}}.brand{{font-size:18px}}}}
</style>
</head>
<body>
<main class="wrap">
  <header class="top">
    <div>
      <div class="brand">A股重大利好监控 <span style="font-size:12px;color:var(--muted)">v5.2</span></div>
      <div class="sub">云端自动扫描 / 新闻事件评分 / 板块资金 / 人气股计划 / 风险边界</div>
    </div>
    <div class="status"><span class="dot"></span>GitHub Actions 云端运行<br>页面生成 {generated}</div>
  </header>
  <div id="app"></div>
  <div class="foot">本页是事件监控和交易计划辅助，不构成投资建议。GitHub 定时任务可能有分钟级延迟；非交易时段不会覆盖最近有效看板。</div>
</main>
<script id="initial-data" type="application/json">{escape(initial_json)}</script>
<script>
function esc(s) {{ return String(s ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function pct(v) {{ const n = Number(v || 0); return (n > 0 ? '+' : '') + n.toFixed(2) + '%'; }}
function pills(items) {{ return (items || []).map(x => `<span class="pill">${{esc(x)}}</span>`).join(''); }}
function section(title, body) {{ return `<section class="section panel"><h2 class="title">${{esc(title)}}</h2><div class="panelBody">${{body}}</div></section>`; }}
function empty(text) {{ return `<div class="empty">${{esc(text)}}</div>`; }}
function factor(label, value, max) {{
  const n = Math.max(0, Math.min(100, Number(value || 0) / max * 100));
  return `<div class="factor"><span>${{esc(label)}}</span><span class="bar"><i style="width:${{n}}%"></i></span><span>${{esc(value)}}</span></div>`;
}}
function render(data) {{
  const s = data.summary || {{}};
  const pulse = data.market_pulse || {{}};
  const auto = data.automation || {{}};
  const topText = s.top_stock ? `首选观察：${{esc(s.top_stock)}} / ${{esc(s.top_action)}}` : '当前没有达到重大阈值，保持观察。';
  const metrics = `<section class="grid">
    <div class="metric"><b>${{esc(s.important_count || 0)}}</b><span>重大利好</span></div>
    <div class="metric"><b>${{esc(s.matched_count || 0)}}</b><span>匹配信号</span></div>
    <div class="metric"><b>${{esc(s.sector_count || 0)}}</b><span>影响板块</span></div>
    <div class="metric"><b>${{esc((s.mood || {{}}).score || 50)}}</b><span>市场情绪：${{esc((s.mood || {{}}).label || '中性')}}</span></div>
    <div class="metric"><b>${{esc((pulse.northbound || {{}}).net || 0)}}</b><span>北向/指数信号</span></div>
    <div class="metric"><b>${{pulse.market_open ? 'OPEN' : 'WAIT'}}</b><span>${{esc(auto.runtime || 'GitHub Actions')}}</span></div>
  </section>`;
  const band = `<div class="band">${{topText}}<br>更新时间：${{esc((s.timestamp || '').replace('T',' '))}} / 目标频率：${{esc(s.scan_interval || '1分钟')}} / 电脑开机：不需要</div>`;
  document.getElementById('app').innerHTML = metrics + band + `<div class="layout"><div>${{recommendations(data)}}${{news(data)}}</div><aside>${{pulsePanel(data)}}${{sectorPanel(data)}}${{gainersPanel(data)}}${{keywordPanel(data)}}</aside></div>`;
}}
function recommendations(data) {{
  const cards = (data.recommendations || []).slice(0, 12).map(r => `<article class="card rec ${{esc(r.action)}}">
    <div class="row"><div class="stock">#${{esc(r.rank)}} ${{esc(r.stock)}}</div><div class="action">${{esc(r.action_label)}} / ${{esc(r.score)}}</div></div>
    <div>${{pills(r.sectors)}}${{pills(r.events)}}</div>
    <div class="plan">仓位上限：${{esc(r.position_pct)}}% / 入场：${{esc(r.entry)}}<br>止损：${{esc(r.stop_loss)}} / 止盈：${{esc(r.take_profit)}} / 时间止损：${{esc(r.time_stop)}}</div>
    <div class="plan">${{esc(r.decision || '')}}</div>
    ${{factor('新闻热度', (r.factors || {{}}).news_heat, 40)}}${{factor('题材宽度', (r.factors || {{}}).event_breadth, 14)}}${{factor('板块资金', (r.factors || {{}}).sector_flow, 12)}}
    <div class="plan">${{pills((r.reasons || []).slice(0,2))}}</div>
  </article>`);
  return section('人气股交易计划', cards.length ? `<div class="cards">${{cards.join('')}}</div>` : empty('暂无推荐计划'));
}}
function news(data) {{
  const rows = ((data.important_news || []).length ? data.important_news : (data.scored_news || [])).slice(0, 16);
  const cards = rows.map(n => `<article class="card">
    <div><span class="score">${{esc(n.score)}}</span><span class="pill">${{esc(n.level)}}</span><span class="pill">${{esc(n.source)}}</span><span class="pill">${{esc(n.event)}}</span></div>
    <div class="headline">${{esc(n.title)}}</div><div>${{pills((n.sectors || []).slice(0,4))}}</div>
    <div>${{pills((n.matched_keywords || []).slice(0,6))}}</div>
    <div class="meta"><span>${{esc(n.duration)}}</span><a href="${{esc(n.url)}}" target="_blank">原文</a></div>
  </article>`);
  return section('信号新闻流', cards.length ? `<div class="cards">${{cards.join('')}}</div>` : empty('暂无匹配新闻'));
}}
function pulsePanel(data) {{
  const a = data.automation || {{}};
  const p = data.market_pulse || {{}};
  return section('云端运行状态', `<table class="table">
    <tr><td>运行平台</td><td>${{esc(a.runtime || 'GitHub Actions')}}</td></tr>
    <tr><td>网站托管</td><td>${{esc(a.hosting || 'GitHub Pages')}}</td></tr>
    <tr><td>电脑开机</td><td>${{a.computer_required === false ? '不需要' : '未知'}}</td></tr>
    <tr><td>扫描窗口</td><td>${{esc(a.schedule || '')}}</td></tr>
    <tr><td>市场状态</td><td>${{p.market_open ? '交易中' : '等待交易'}}</td></tr>
  </table><div class="meta">${{esc(a.note || '')}}</div>`);
}}
function sectorPanel(data) {{
  const rows = ((data.market_pulse || {{}}).top_sectors || []).slice(0, 10);
  const html = rows.map(x => `<tr><td>${{esc(x.name)}}</td><td>${{pct(x.change_pct)}}</td></tr>`).join('');
  return section('板块涨幅', html ? `<table class="table">${{html}}</table>` : empty('暂无板块数据'));
}}
function gainersPanel(data) {{
  const rows = ((data.market_pulse || {{}}).top_gainers || []).slice(0, 10);
  const html = rows.map(x => `<tr><td>${{esc(x.name)}} <span class="meta">${{esc(x.code)}}</span></td><td>${{pct(x.change_pct)}}</td></tr>`).join('');
  return section('人气涨幅榜', html ? `<table class="table">${{html}}</table>` : empty('暂无涨幅榜数据'));
}}
function keywordPanel(data) {{
  const rows = ((data.market_pulse || {{}}).hot_keywords || []).slice(0, 12);
  return section('热点关键词', rows.length ? rows.map(x => `<span class="pill">${{esc(x.word)}} · ${{esc(x.count)}}</span>`).join('') : empty('暂无热点关键词'));
}}
async function refreshData() {{
  try {{
    const res = await fetch('data.json?ts=' + Date.now());
    if (!res.ok) return;
    render(await res.json());
  }} catch (e) {{}}
}}
try {{ render(JSON.parse(document.getElementById('initial-data').textContent)); }} catch(e) {{}}
refreshData();
setInterval(refreshData, 60000);
</script>
</body>
</html>"""
