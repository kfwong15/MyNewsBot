import os
import requests
import feedparser
from bs4 import BeautifulSoup
import html

# 获取 Telegram Token 和 Chat ID（从环境变量读取）
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# ✅ 抓取中国报 RSS 最新 3 条
def fetch_chinapress(max_items=3):
    feed_url = "https://www.chinapress.com.my/feed/"
    feed = feedparser.parse(feed_url)
    messages = []
    for entry in feed.entries[:max_items]:
        title = html.escape(entry.title)
        link = entry.link
        messages.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
    return messages

# ✅ 抓取东方日报新闻列表第一页的第一条新闻（万能方式）
def fetch_oriental():
    url = "https://www.orientaldaily.com.my/news"
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if href.startswith("/news/") and text:
                title = html.escape(text)
                link = "https://www.orientaldaily.com.my" + href
                return [f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}"]

        return ["❌ 东方日报抓取失败：页面中未找到任何有效新闻链接"]
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

# ✅ 主程序：抓取 + 推送
def main():
    messages = []
    messages.extend(fetch_chinapress())
    messages.extend(fetch_oriental())
    for msg in messages:
        if msg:
            send(msg)

if __name__ == "__main__":
    main()
