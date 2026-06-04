import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"
DASHBOARD_PATH = OUTPUT_DIR / "dashboard.html"
DATA_PATH = OUTPUT_DIR / "data.json"
HISTORY_PATH = OUTPUT_DIR / "history.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

INTERVAL_MINUTES = 1
CACHE_TTL_SECONDS = 300
NOTIFY_THRESHOLD = 4

# 利好关键词体系 - 覆盖更广，评分更细
BULLISH_KEYWORDS = [
    # === 货币政策（最高分）===
    "降准","降息","增量资金","国家队","平准基金","中央汇金",
    "回购增持","回购注销","特别国债","专项债","财政政策","货币政策",
    # === 监管利好 ===
    "重大利好","重磅政策","政策支持","国九条","新国九条",
    "减税降费","提振信心","提振市场","稳定市场","活跃资本市场",
    "注册制","金融监管","金融改革",
    # === 重组并购 ===
    "并购重组","资产注入","借壳上市","重大资产重组","重大重组",
    # === 业绩 ===
    "业绩大增","扭亏为盈","大幅预增","利润暴涨",
    "涨停","大涨","暴涨","飙升","拉升",
    # === 军工航天 ===
    "火箭","发射成功","卫星","商业航天","航天","太空",
    "北斗","神舟","天宫","嫦娥","探月","空间站",
    "C919","大飞机","航空发动机","无人机","低空经济",
    "军工","国防","装备","军贸",
    # === 科技 ===
    "芯片","半导体","光刻机","算力",
    "AI","人工智能","大模型","机器人","无人驾驶",
    "量子","6G","通信","国产替代","自主可控","信创",
    # === 新能源 ===
    "新能源车","固态电池","储能","光伏","风电","氢能",
    # === 医药 ===
    "创新药","生物医药","医疗器械","FDA","获批",
    # === 事件驱动 ===
    "重大突破","重大合同","中标","订单大增",
    "北向资金","外资流入","主力净流入",
    "大基金","产业基金","补贴","扶持",
    "高质量发展","新质生产力","科技创新",
    "积极信号","见底","反转","复苏",
    # === 新增广泛捕获词 ===
    "首次","全球首发","里程碑","历史性","突破性",
    "世界第一","国内首款","自主研发","打破垄断",
    "大规模","百亿","千亿","万亿",
    # === 火箭/航天发射类 ===
    "成功发射","顺利升空","入轨","运载火箭",
    "XX火箭","飞行试验","空间探测",
]

BULLISH_SCORE = {
    "降准":8,"降息":9,"增量资金":7,"国家队":9,
    "平准基金":10,"中央汇金":9,"回购增持":6,"回购注销":7,
    "重大利好":9,"重磅政策":9,"政策支持":6,
    "并购重组":7,"重大资产重组":8,"业绩大增":7,
    "重大突破":8,"提振信心":6,"特别国债":8,
    "涨停":5,"北向资金":6,"外资流入":6,
    "发射成功":7,"火箭":6,"卫星":6,"商业航天":7,
    "航天":5,"太空":5,"成功发射":7,
    "芯片":6,"半导体":6,"光刻机":7,"算力":5,
    "AI":5,"人工智能":5,"大模型":5,"机器人":5,
    "创新药":5,"生物医药":5,
    "重大合同":6,"中标":5,"订单大增":6,
    "首次":5,"全球首发":7,"里程碑":6,"历史性":6,"突破性":6,
    "世界第一":7,"国内首款":6,"自主研发":5,"打破垄断":7,
    "大规模":5,"百亿":6,"千亿":7,"万亿":8,
    "成功发射":7,"运载火箭":7,"空间探测":6,
}
DEFAULT_SCORE = 3

NEWS_SOURCES = [
    {"name": "东方财富头条", "url":"https://finance.eastmoney.com/a/czqyw.html", "type":"html"},
    {"name": "财联社电报", "url":"https://www.cls.cn/telegraph", "type":"api",
     "api_url":"https://www.cls.cn/v1/roll/get_roll_list?app=Cailianshe&os=web&sv=8.8.8"},
    {"name": "新浪财经", "url":"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=20","type":"json"},
]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID","")
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY","")
BARK_KEY = os.environ.get("BARK_KEY","")
BARK_SERVER = os.environ.get("BARK_SERVER","https://api.day.app")
PUSHPLUS_KEY = os.environ.get("PUSHPLUS_KEY","")

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_DIR/"monitor.log",encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("AStockMonitor")
