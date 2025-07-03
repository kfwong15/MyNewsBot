import os
import requests
import feedparser
from bs4 import BeautifulSoup
import html

# 获取 Telegram Token 和 Chat ID（从环境变量读取，建议使用 GitHub Secrets 配置）
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# ✅ 抓取中国报 RSS（前 3 条）
def fetch_chinapress(max_items=3):
    feed_url = "https://www.chinapress.com.my/feed/"
    feed = feedparser.parse(feed_url)
    messages = []
    for entry in feed.entries[:max_items]:
        title = html.escape(entry.title)
        link = entry.link
        messages.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
    return messages

# ✅ 抓取东方日报 RSS（稳定，不依赖网页结构）
def fetch_oriental(max_items=1):
    feed_url = "https://www.orientaldaily.com.my/rss"
    try:
        feed = feedparser.parse(feed_url)
        messages = []
        for entry in feed.entries[:max_items]:
            title = html.escape(entry.title)
            link = entry.link
            messages.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")
        if not messages:
            return ["❌ 东方日报抓取失败：RSS 无新闻"]
        return messages
    except Exception as e:
        return [f"❌ 东方日报抓取失败：{e}"]

# ✅ 发送消息到 Telegram
def send(msg):
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    res = requests.post(API, json=payload)
    print("准备发送：", msg)
    print("✅ 推送成功" if res.ok else f"❌ 推送失败，状态码：{res.status_code}")
    return res.ok

# ✅ 主函数：抓取新闻 + 发送消息
def main():
    messages = []
    messages.extend(fetch_chinapress())       # 中国报前3条
    messages.extend(fetch_oriental())         # 东方日报前1条
    for msg in messages:
        if msg:
            send(msg)

if __name__ == "__main__":
    main()
