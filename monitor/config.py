import os
from pathlib import Path

# In GitHub Actions, BASE_DIR = repo root = github-deploy/
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"
DASHBOARD_PATH = OUTPUT_DIR / "dashboard.html"
HISTORY_PATH = OUTPUT_DIR / "history.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

INTERVAL_MINUTES = 1
CACHE_TTL_SECONDS = 600
NOTIFY_THRESHOLD = 6

BULLISH_KEYWORDS = [
    "降准", "降息", "增量资金", "国家队", "平准基金",
    "中央汇金", "社保基金", "险资入市", "回购增持", "回购注销",
    "重大利好", "重磅政策", "政策支持", "国九条", "新国九条",
    "并购重组", "资产注入", "借壳上市", "重大资产重组",
    "业绩大增", "扭亏为盈", "大幅预增", "利润暴增",
    "重大突破", "国产替代", "自主可控",
    "提振信心", "提振市场", "稳定市场",
    "特别国债", "专项债", "财政政策", "货币政策",
    "减税降费", "涨停", "大涨", "暴涨", "飙升",
    "重大合同", "中标", "订单大增",
    "北向资金", "外资流入", "主力净流入",
    "大基金", "产业基金", "补贴", "扶持",
    "高质量发展", "新质生产力", "科技创新",
    "积极信号", "见底", "反转", "复苏",
    "火箭", "发射成功", "卫星", "商业航天", "航天", "太空",
    "北斗", "神舟", "天宫", "嫦娥", "探月", "空间站",
    "C919", "大飞机", "国产大飞机", "航空发动机",
    "无人机", "军工", "国防", "装备",
    "芯片", "半导体", "光刻机", "算力",
    "AI", "人工智能", "大模型", "机器人",
    "新能源车", "固态电池", "储能", "光伏",
    "创新药", "生物医药", "医疗器械",
]

BULLISH_SCORE = {
    "降准": 8, "降息": 9, "增量资金": 7, "国家队": 9,
    "平准基金": 10, "中央汇金": 9, "回购增持": 6,
    "重大利好": 9, "重磅政策": 9, "政策支持": 6,
    "并购重组": 7, "重大资产重组": 8, "业绩大增": 7,
    "重大突破": 7, "提振信心": 6, "特别国债": 8,
    "涨停": 5, "北向资金": 6, "外资流入": 6,
}
DEFAULT_SCORE = 4

NEWS_SOURCES = [
    {"name": "东方财富头条", "url": "https://finance.eastmoney.com/a/czqyw.html", "type": "html"},
    {"name": "财联社电报", "url": "https://www.cls.cn/telegraph", "type": "api",
     "api_url": "https://www.cls.cn/v1/roll/get_roll_list?app=Cailianshe&os=web&sv=8.8.8"},
    {"name": "新浪财经", "url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=20", "type": "json"},
]

# Push notification config (set via GitHub Actions secrets -> env variables)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")
BARK_KEY = os.environ.get("BARK_KEY", "")
BARK_SERVER = os.environ.get("BARK_SERVER", "https://api.day.app")

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "monitor.log", encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("AStockMonitor")
