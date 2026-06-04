import logging
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"
DEPLOY_DIR = BASE_DIR / "deploy"

DASHBOARD_PATH = OUTPUT_DIR / "dashboard.html"
DATA_PATH = OUTPUT_DIR / "data.json"
HISTORY_PATH = OUTPUT_DIR / "history.json"
NOTIFY_STATE_PATH = OUTPUT_DIR / "notify_state.json"

for path in (OUTPUT_DIR, LOG_DIR, DEPLOY_DIR):
    path.mkdir(parents=True, exist_ok=True)

INTERVAL_MINUTES = 1
NOTIFY_THRESHOLD = 72
MAX_NEWS_ITEMS = 160
MAX_RECOMMENDATIONS = 18

NEWS_SOURCES = [
    {
        "name": "财联社电报",
        "url": "https://www.cls.cn/v1/roll/get_roll_list?app=Cailianshe&os=web&sv=8.8.8",
        "kind": "cls",
        "weight": 1.28,
    },
    {
        "name": "新浪财经",
        "url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=50",
        "kind": "sina",
        "weight": 0.95,
    },
    {
        "name": "东方财富",
        "url": "https://finance.eastmoney.com/a/czqyw.html",
        "kind": "html",
        "weight": 1.05,
    },
    {
        "name": "金融界",
        "url": "https://stock.jrj.com.cn/",
        "kind": "html",
        "weight": 0.90,
    },
]

EVENT_RULES = [
    {
        "event": "政策/流动性",
        "keywords": ["降准", "降息", "增量资金", "平准基金", "中央汇金", "国家队", "活跃资本市场", "长期资金入市", "险资入市", "并购重组政策"],
        "sectors": ["证券", "银行", "保险", "央企改革"],
        "stocks": ["东方财富", "中信证券", "华泰证券", "招商银行", "中国平安"],
        "base": 38,
        "duration": "1-4周",
    },
    {
        "event": "航天/军工",
        "keywords": ["火箭", "发射成功", "卫星", "商业航天", "航天", "北斗", "神舟", "天宫", "低空经济", "无人机", "军工", "国防"],
        "sectors": ["航天军工", "卫星互联网", "低空经济", "军工电子"],
        "stocks": ["中国卫星", "航天电子", "航天动力", "中航沈飞", "航发动力"],
        "base": 34,
        "duration": "1-5天",
    },
    {
        "event": "AI/算力",
        "keywords": ["AI", "人工智能", "大模型", "算力", "智能体", "机器人", "具身智能", "多模态", "数据中心", "液冷"],
        "sectors": ["AI应用", "算力", "传媒游戏", "机器人"],
        "stocks": ["科大讯飞", "中科曙光", "浪潮信息", "金山办公", "拓尔思"],
        "base": 30,
        "duration": "3-10天",
    },
    {
        "event": "半导体/国产替代",
        "keywords": ["芯片", "半导体", "光刻机", "晶圆", "封测", "先进封装", "国产替代", "自主可控", "存储"],
        "sectors": ["半导体", "芯片设备", "先进封装", "信创"],
        "stocks": ["中芯国际", "北方华创", "中微公司", "寒武纪", "海光信息"],
        "base": 31,
        "duration": "3-15天",
    },
    {
        "event": "新能源/汽车",
        "keywords": ["新能源汽车", "固态电池", "锂电池", "储能", "充电桩", "智能驾驶", "汽车出口", "飞行汽车"],
        "sectors": ["新能源汽车", "锂电池", "储能", "智能驾驶"],
        "stocks": ["比亚迪", "宁德时代", "亿纬锂能", "阳光电源", "德赛西威"],
        "base": 27,
        "duration": "2-10天",
    },
    {
        "event": "医药创新",
        "keywords": ["创新药", "生物医药", "临床", "获批", "FDA", "减肥药", "GLP-1", "医疗器械"],
        "sectors": ["创新药", "医疗器械", "CXO", "生物医药"],
        "stocks": ["恒瑞医药", "迈瑞医疗", "药明康德", "百济神州", "爱尔眼科"],
        "base": 26,
        "duration": "1-7天",
    },
    {
        "event": "并购/业绩",
        "keywords": ["并购重组", "资产注入", "重大资产重组", "回购增持", "业绩预增", "扭亏为盈", "大额订单", "中标", "合同金额"],
        "sectors": ["并购重组", "央企改革", "高景气行业"],
        "stocks": ["东方财富", "中国中车", "中国船舶", "中国中免"],
        "base": 26,
        "duration": "1-20天",
    },
]

NEGATIVE_KEYWORDS = ["减持", "监管函", "立案", "亏损", "下滑", "终止", "处罚", "风险提示", "退市", "问询函"]
CONFIRM_KEYWORDS = ["首次", "突破", "全球", "国家", "重大", "万亿", "千亿", "百亿", "中标", "获批", "成功", "落地"]
AUTHORITY_KEYWORDS = ["国务院", "央行", "证监会", "发改委", "财政部", "工信部", "国资委", "交易所"]
POPULAR_STOCKS = sorted({stock for rule in EVENT_RULES for stock in rule["stocks"]})

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")
BARK_KEY = os.environ.get("BARK_KEY", "")
BARK_SERVER = os.environ.get("BARK_SERVER", "https://api.day.app")
PUSHPLUS_KEY = os.environ.get("PUSHPLUS_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("AStockMonitor")
