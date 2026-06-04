#!/usr/bin/env python
"""
A股利好监控 v2 — 升级版分析引擎
量化风格：行业分类 + 相关股票映射 + 多维度情感评分 + 时间衰减
"""
from datetime import datetime
import hashlib, re
from .config import BULLISH_KEYWORDS, BULLISH_SCORE, DEFAULT_SCORE, HISTORY_PATH, logger

# ═══════════════════════════════════════════
# 1. 行业分类系统
# ═══════════════════════════════════════════

SECTORS = {
    "航天军工": {
        "keywords": ["火箭", "发射成功", "卫星", "商业航天", "航天", "太空", "北斗", "神舟",
                     "天宫", "嫦娥", "探月", "空间站", "军工", "国防", "装备", "军贸", "军售",
                     "导弹", "雷达", "舰船", "战斗机", "无人机", "航空发动机"],
        "stocks": ["航天科技", "航天科工", "中航", "中国卫星", "航天电子", "航天动力",
                   "中航沈飞", "中航西飞", "航发动力", "中国船舶"],
    },
    "芯片半导体": {
        "keywords": ["芯片", "半导体", "光刻机", "光刻胶", "晶圆", "封测", "EDA",
                     "集成电路", "先进封装", "chip", "Chip", "GPU", "NPU", "AI芯片",
                     "存储芯片", "MCU", "IGBT", "SiC", "碳化硅", "氮化镓", "第三代半导体",
                     "中芯", "华虹", "长电", "北方华创", "拓荆"],
        "stocks": ["中芯国际", "北方华创", "韦尔股份", "海光信息", "寒武纪",
                   "长电科技", "华虹公司", "中微公司", "兆易创新", "卓胜微"],
    },
    "AI人工智能": {
        "keywords": ["AI", "人工智能", "大模型", "算力", "AIGC", "ChatGPT", "GPT",
                     "大语言模型", "多模态", "智能体", "机器人", "具身智能",
                     "深度学习", "神经网络", "计算机视觉", "自然语言处理",
                     "AI应用", "AI赋能", "AI+", "智能化"],
        "stocks": ["科大讯飞", "百度", "商汤", "金山办公", "中科创达",
                   "拓尔思", "海康威视", "大华股份", "云从科技", "格灵深瞳"],
    },
    "新能源汽车": {
        "keywords": ["新能源车", "电动车", "锂电池", "固态电池", "钠离子电池",
                     "充电桩", "换电", "自动驾驶", "智能驾驶", "FSD", "NOA",
                     "比亚迪", "特斯拉", "蔚来", "小鹏", "理想", "小米汽车",
                     "汽车出口", "汽车出海"],
        "stocks": ["比亚迪", "宁德时代", "赣锋锂业", "天齐锂业", "华友钴业",
                   "亿纬锂能", "国轩高科", "先导智能", "拓普集团", "德赛西威"],
    },
    "医药医疗": {
        "keywords": ["创新药", "生物医药", "医疗器械", "CXO", "CRO", "CDMO",
                     "疫苗", "基因治疗", "细胞治疗", "GLP-1", "减肥药",
                     "中药", "中医药", "集采", "医保谈判",
                     "FDA", "NMPA", "临床", "获批", "突破性疗法"],
        "stocks": ["恒瑞医药", "迈瑞医疗", "药明康德", "百济神州", "智飞生物",
                   "爱尔眼科", "联影医疗", "康龙化成", "泰格医药", "片仔癀"],
    },
    "金融政策": {
        "keywords": ["降准", "降息", "加息", "增量资金", "国家队", "平准基金",
                     "中央汇金", "社保基金", "险资入市", "回购增持",
                     "特别国债", "专项债", "财政政策", "货币政策", "MLF", "LPR",
                     "证监会", "金融监管", "资本市场改革", "注册制",
                     "国九条", "新国九条", "活跃资本市场"],
        "stocks": ["中信证券", "东方财富", "工商银行", "招商银行", "中国平安",
                   "同花顺", "华泰证券", "中金公司", "中国人寿"],
    },
    "消费": {
        "keywords": ["消费", "零售", "电商", "免税", "旅游", "酒店", "餐饮",
                     "白酒", "食品", "饮料", "家电", "国潮", "以旧换新",
                     "促消费", "扩大内需", "双循环"],
        "stocks": ["贵州茅台", "五粮液", "美的集团", "格力电器", "海尔智家",
                   "中国中免", "伊利股份", "海天味业", "安井食品"],
    },
    "新能源/储能": {
        "keywords": ["光伏", "风电", "储能", "氢能", "太阳能", "逆变器",
                     "TOPCon", "HJT", "钙钛矿", "海上风电", "储能电池",
                     "虚拟电厂", "微电网", "新能源装机", "能源转型"],
        "stocks": ["隆基绿能", "通威股份", "阳光电源", "晶科能源", "天合光能",
                   "明阳智能", "金风科技", "固德威", "锦浪科技"],
    },
    "信创/国产替代": {
        "keywords": ["信创", "国产替代", "自主可控", "操作系统", "数据库",
                     "CPU", "服务器", "信息安全", "网络安全", "数据安全",
                     "华为", "鸿蒙", "鲲鹏", "昇腾", "欧拉",
                     "软件", "SaaS", "工业软件", "CAD", "EDA软件"],
        "stocks": ["金山办公", "用友网络", "中科曙光", "浪潮信息", "紫光股份",
                   "中国软件", "诚迈科技", "东方通", "宝信软件", "广联达"],
    },
}

# 来源权威性权重
SOURCE_WEIGHTS = {
    "东方财富": 1.0,
    "财联社": 1.2,
    "新浪财经": 0.9,
}

# 利好信号位置权重
POSITION_WEIGHTS = [1.0, 0.95, 0.9, 0.85, 0.8]


# ═══════════════════════════════════════════
# 2. 多维度评分引擎
# ═══════════════════════════════════════════

def classify_sectors(title: str, content: str = "") -> list:
    """识别新闻涉及的行业"""
    text = title + " " + content
    matched_sectors = {}
    for sector, data in SECTORS.items():
        score = 0
        matched_kws = []
        for kw in data["keywords"]:
            if kw in text:
                matched_kws.append(kw)
                score += 1
        if score > 0:
            matched_sectors[sector] = {
                "score": score,
                "keywords": matched_kws,
                "relevant_stocks": data["stocks"],
            }
    result = sorted(matched_sectors.items(), key=lambda x: x[1]["score"], reverse=True)
    return result[:3]


def map_stocks(title: str, sectors: list) -> list:
    """映射相关股票"""
    stocks = {}
    for sector_name, sector_info in sectors:
        for s in sector_info["relevant_stocks"]:
            if s not in stocks:
                stocks[s] = {"name": s, "sectors": [sector_name], "count": 0}
            else:
                if sector_name not in stocks[s]["sectors"]:
                    stocks[s]["sectors"].append(sector_name)
        for s in sector_info["relevant_stocks"]:
            if s in title:
                if s not in stocks:
                    stocks[s] = {"name": s, "sectors": [sector_name], "count": 1}
                stocks[s]["count"] += 2
    return list(stocks.values())[:5]


def score_news(news_item: dict, position: int = 0) -> dict:
    """
    多维度评分：
    - keyword_score: 关键词匹配分
    - source_weight: 来源权重
    - position_bonus: 位置权重
    - specificity: 具体性（是否提到具体数字/公司）
    - recency: 时效性
    """
    title = news_item["title"]
    source = news_item.get("source", "未知")
    now = datetime.now()

    # 1. 关键词基础分
    matched_keywords = []
    raw_score = 0
    for keyword in BULLISH_KEYWORDS:
        if keyword in title:
            s = BULLISH_SCORE.get(keyword, DEFAULT_SCORE)
            matched_keywords.append({"keyword": keyword, "score": s})
            raw_score += s

    # 2. 来源权重
    src_w = SOURCE_WEIGHTS.get(source, 0.8)

    # 3. 位置权重
    pos_w = POSITION_WEIGHTS[min(position, len(POSITION_WEIGHTS) - 1)]

    # 4. 具体性加成
    specificity_bonus = 0
    if re.search(r'\d+[%％]', title): specificity_bonus += 2
    if re.search(r'\d+亿', title): specificity_bonus += 3
    if re.search(r'\d+[万亿]', title): specificity_bonus += 3
    if re.search(r'[A-Z]+', title): specificity_bonus += 1

    # 5. 行业分类
    sectors = classify_sectors(title)
    stocks = map_stocks(title, sectors)

    # 6. 综合评分
    final_score = raw_score * src_w * pos_w + specificity_bonus
    final_score = round(final_score, 1)

    # 7. 信号级别
    if final_score >= 15:
        level = "重大利好"
        level_class = "level-high"
    elif final_score >= 10:
        level = "显著利好"
        level_class = "level-mid"
    elif final_score >= 6:
        level = "关注利好"
        level_class = "level-low"
    else:
        level = "一般信号"
        level_class = "level-info"

    return {
        "title": title,
        "url": news_item.get("url", ""),
        "source": source,
        "raw_score": raw_score,
        "source_weight": src_w,
        "position_bonus": pos_w,
        "specificity_bonus": specificity_bonus,
        "final_score": final_score,
        "level": level,
        "level_class": level_class,
        "matched_keywords": matched_keywords,
        "sectors": [s[0] for s in sectors],
        "stocks": stocks,
        "fingerprint": hashlib.md5(title.encode()).hexdigest(),
        "timestamp": now.isoformat(),
    }


def score_all_news(news_list: list) -> list:
    """对所有新闻进行评分"""
    results = []
    for i, news in enumerate(news_list):
        scored = score_news(news, i)
        if scored["matched_keywords"]:
            results.append(scored)
    results.sort(key=lambda x: x["final_score"], reverse=True)
    logger.info(f"v2 Analyzer: {len(results)} scored items")
    return results
