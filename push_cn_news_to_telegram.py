import os
import sys
import time
import logging
import requests
import feedparser
import html
from typing import List, Dict

# ========== 配置 ==========
FEEDS = [
    {"name": "中国报", "url": "https://www.chinapress.com.my/feed/", "max_items": 3},
    {"name": "东方日报", "url": "https://www.orientaldaily.com.my/rss", "max_items": 1},
    # 你可以在这里添加更多 RSS 源
]
TELEGRAM_RETRY = 3          # Telegram 推送失败最大重试次数
TELEGRAM_RETRY_DELAY = 2    # 重试间隔秒数

# ========== 日志配置 ==========
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("news_telegram_bot.log", encoding="utf-8")
    ]
)

# ========== 环境变量检查 ==========
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
if not TG_BOT_TOKEN or not TG_CHAT_ID:
    logging.critical("环境变量 TG_BOT_TOKEN 和 TG_CHAT_ID 必须设置！")
    sys.exit(1)

API = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# ========== 抓取 RSS ==========
def fetch_feed(feed: Dict) -> List[str]:
    """抓取并格式化指定 RSS 源的新闻"""
    url = feed["url"]
    name = feed["name"]
    max_items = feed.get("max_items", 1)
    messages = []
    try:
        feed_data = feedparser.parse(url)
        if not feed_data.entries:
            msg = f"❌ <b>{name}</b> 抓取失败：RSS 无新闻"
            logging.warning(msg)
            messages.append(msg)
        for entry in feed_data.entries[:max_items]:
            title = html.escape(entry.title)
            link = entry.link
            messages.append(f"📰 <b>{name}</b>\n📌 {title}\n🔗 {link}")
    except Exception as e:
        msg = f"❌ <b>{name}</b> 抓取失败：{e}"
        logging.error(msg)
        messages.append(msg)
    return messages

# ========== 推送到 Telegram ==========
def send_telegram(msg: str) -> bool:
    """发送消息到 Telegram，自动重试"""
    for attempt in range(1, TELEGRAM_RETRY + 1):
        try:
            res = requests.post(API, json={
                "chat_id": TG_CHAT_ID,
                "text": msg,
                "parse_mode": "HTML"
            }, timeout=10)
            if res.ok:
                logging.info(f"推送成功: {msg[:30]}...")
                return True
            else:
                logging.warning(f"推送失败({res.status_code}): {res.text}")
        except Exception as e:
            logging.error(f"推送异常: {e}")
        if attempt < TELEGRAM_RETRY:
            time.sleep(TELEGRAM_RETRY_DELAY)
    logging.error("推送失败，已达最大重试次数。")
    return False

# ========== 主流程 ==========
def main():
    logging.info("开始抓取并推送新闻")
    all_messages = []
    for feed in FEEDS:
        msgs = fetch_feed(feed)
        all_messages.extend(msgs)
    for msg in all_messages:
        if msg:
            send_telegram(msg)
    logging.info("全部任务结束")

if __name__ == "__main__":
    main()
