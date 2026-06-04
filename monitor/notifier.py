import json
import urllib.parse
import urllib.request
from datetime import datetime

from .config import (
    BARK_KEY,
    BARK_SERVER,
    NOTIFY_STATE_PATH,
    PUSHPLUS_KEY,
    SERVERCHAN_KEY,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    logger,
)


def should_notify(fingerprint: str) -> bool:
    if not fingerprint:
        return False
    today = datetime.now().strftime("%Y-%m-%d")
    state = _load_state()
    sent = state.get(today, [])
    if fingerprint in sent:
        logger.info("Push skipped: duplicate fingerprint %s", fingerprint[:10])
        return False
    sent.append(fingerprint)
    state = {today: sent[-80:]}
    NOTIFY_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def notify_all(title: str, message: str) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full = f"{now}\n{message}"
    result = {
        "telegram": send_telegram(title, full),
        "serverchan": send_serverchan(title, full),
        "bark": send_bark(title, full),
        "pushplus": send_pushplus(title, full),
    }
    if any(result.values()):
        logger.info("Push results: %s", result)
    else:
        logger.info("No push channel configured or all channels failed.")
    return result


def send_telegram(title: str, message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": f"{title}\n{message}"}).encode()
        result = _post_json(url, data)
        ok = bool(result.get("ok"))
        if ok:
            logger.info("Telegram push OK")
        return ok
    except Exception as exc:
        logger.warning("Telegram error: %s", exc)
        return False


def send_serverchan(title: str, content: str) -> bool:
    if not SERVERCHAN_KEY:
        return False
    try:
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
        data = urllib.parse.urlencode({"title": f"A股重大利好: {title}", "desp": content}).encode()
        result = _post_json(url, data)
        ok = result.get("code") == 0
        if ok:
            logger.info("ServerChan push OK")
        return ok
    except Exception as exc:
        logger.warning("ServerChan error: %s", exc)
        return False


def send_bark(title: str, body: str) -> bool:
    if not BARK_KEY:
        return False
    try:
        url = f"{BARK_SERVER.rstrip('/')}/{BARK_KEY}/{urllib.parse.quote(title)}/{urllib.parse.quote(body)}?group=AStock"
        with urllib.request.urlopen(url, timeout=10):
            pass
        logger.info("Bark push OK")
        return True
    except Exception as exc:
        logger.warning("Bark error: %s", exc)
        return False


def send_pushplus(title: str, content: str) -> bool:
    if not PUSHPLUS_KEY:
        return False
    try:
        url = "https://www.pushplus.plus/send"
        payload = json.dumps({"token": PUSHPLUS_KEY, "title": title, "content": content, "template": "txt"}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8", errors="replace"))
        ok = result.get("code") == 200
        if ok:
            logger.info("PushPlus push OK")
        return ok
    except Exception as exc:
        logger.warning("PushPlus error: %s", exc)
        return False


def _post_json(url: str, data: bytes) -> dict:
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _load_state() -> dict:
    if NOTIFY_STATE_PATH.exists():
        try:
            return json.loads(NOTIFY_STATE_PATH.read_text("utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}
