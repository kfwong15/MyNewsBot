import os
import requests
import feedparser
from bs4 import BeautifulSoup
import json
import html

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

def fetch_chinapress(max_items=3):
    feed_url = "https://www.chinapress.com.my/feed/"
    feed = feedparser.parse(feed_url)
    messages = []
    for entry in feed.entries[:max_items]:
        title = html.escape(entry.title)
        link = entry.link
        messages.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
    return messages

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
                    title = html.escape(data.get("headline", ""))
                    link = data.get("mainEntityOfPage", {}).get("@id") or data.get("url")
                    if link and not link.startswith("http"):
                        link = "https://www.orientaldaily.com.my" + link
                    return [f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}"]
            except Exception:
                continue
        return ["❌ 东方日报抓取失败：未找到结构化数据"]
    except Exception as e:
        return [f"❌ 东方日报抓取失败：{e}"]

def send(msg):
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    res = requests.post(API, json=payload)
    print("准备发送：", msg)
    print("✅ 推送成功" if res.ok else f"❌ 推送失败 {res.status_code}")
    return res.ok

def main():
    messages = []
    messages.extend(fetch_chinapress())
    messages.extend(fetch_oriental())
    for msg in messages:
        if msg:
            send(msg)

if __name__ == "__main__":
    main()
