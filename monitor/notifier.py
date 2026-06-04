import json, urllib.request, urllib.parse
from datetime import datetime
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SERVERCHAN_KEY, BARK_KEY, BARK_SERVER, PUSHPLUS_KEY, logger

def send_telegram(title, message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        ok = result.get("ok", False)
        if ok: logger.info("Telegram push OK")
        return ok
    except Exception as e:
        logger.warning(f"Telegram error: {e}")
        return False

def send_serverchan(title, content):
    if not SERVERCHAN_KEY:
        return False
    try:
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
        data = urllib.parse.urlencode({"title": f"A股利好警报 {title}", "desp": content}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        ok = result.get("code") == 0
        if ok: logger.info("ServerChan push OK")
        return ok
    except Exception as e:
        logger.warning(f"ServerChan error: {e}")
        return False

def send_bark(title, body):
    if not BARK_KEY:
        return False
    try:
        et = urllib.parse.quote(title)
        eb = urllib.parse.quote(body)
        url = f"{BARK_SERVER}/{BARK_KEY}/{et}/{eb}?group=AStock"
        urllib.request.urlopen(url, timeout=10)
        logger.info("Bark push OK")
        return True
    except Exception as e:
        logger.warning(f"Bark error: {e}")
        return False

def send_pushplus(title, content):
    if not PUSHPLUS_KEY:
        return False
    try:
        data = json.dumps({
            "token": PUSHPLUS_KEY,
            "title": f"A股利好监控: {title}",
            "content": content,
            "topic": "",
            "template": "txt"
        }).encode()
        req = urllib.request.Request(
            "https://www.pushplus.plus/send",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        ok = result.get("code") == 200
        if ok: logger.info("PushPlus push OK")
        return ok
    except Exception as e:
        logger.warning(f"PushPlus error: {e}")
        return False

def notify_all(title, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full = f"🕐 {now}\n{message}"
    r = {
        "tg": send_telegram(title, full),
        "sc": send_serverchan(title, full),
        "bark": send_bark(title, full),
        "pushplus": send_pushplus(title, full),
    }
    if any(r.values()):
        logger.info(f"Push results: {r}")
    else:
        logger.info("No push channel configured - set SERVERCHAN_KEY or PUSHPLUS_KEY as GitHub Secrets")
    return r
