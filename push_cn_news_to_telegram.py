import os
import requests
import feedparser
from bs4 import BeautifulSoup
import json

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# ✅ 1. 抓中国报（稳定 RSS）
def fetch_chinapress(max_items=3):
    feed_url = "https://www.chinapress.com.my/feed/"
    feed = feedparser.parse(feed_url)
    messages = []
    for entry in feed.entries[:max_items]:
        title = entry.title
        link = entry.link
        messages.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
    return messages

# ✅ 2. 抓东方日报（网页结构化数据）
def fetch_oriental():
    url = "https://www.orientaldaily.com.my/"
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "NewsArticle":
                    title = data.get("headline")
                    link = data.get("mainEntityOfPage", {}).get("@id") or data.get("url")
                    if link and not link.startswith("http"):
                        link = "https://www.orientaldaily.com.my" + link
                    return [f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}"]
            except Exception:
                continue
        return []
    except Exception as e:
        return [f"❌ 东方日报抓取失败: {e}"]

# ✅ 3. Telegram 发送消息
def send(msg):
    return requests.post(API, json={
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }).ok

# ✅ 主函数：整合抓取 + 推送
def main():
    messages = []

    # 抓中国报
    messages.extend(fetch_chinapress(max_items=3))

    # 抓东方日报
    messages.extend(fetch_oriental())

    # 推送每条消息
    for msg in messages:
        if msg:
            res = send(msg)
            print("✅ 推送成功" if res else "❌ 推送失败")

if __name__ == "__main__":
    main()
