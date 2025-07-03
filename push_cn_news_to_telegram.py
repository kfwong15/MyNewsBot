import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ✅ 加载 .env 中的环境变量
load_dotenv()
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ✅ 抓取中国报
def fetch_chinapress():
    try:
        url = "https://www.chinapress.com.my/"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        news_items = []
        for article in soup.select('article.post-item')[:3]:
            title_tag = article.find('h3', class_='post-title')
            if title_tag and title_tag.find('a'):
                title = title_tag.get_text(strip=True)
                link = title_tag.find('a')['href']
                if not link.startswith("http"):
                    link = f"https://www.chinapress.com.my{link}"
                news_items.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
        return news_items if news_items else ["❌ 中国报抓取失败：未找到内容"]
    except Exception as e:
        return [f"❌ 中国报抓取失败：{str(e)}"]

# ✅ 抓取东方日报
def fetch_oriental():
    try:
        url = "https://www.orientaldaily.com.my"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        news_items = []

        # 抓取头条
        top = soup.select_one('div.top-news h1 a')
        if top:
            title = top.get_text(strip=True)
            link = top['href']
            if not link.startswith("http"):
                link = f"https://www.orientaldaily.com.my{link}"
            news_items.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")

        # 抓取次要新闻
        for a in soup.select('div.news-list h2 a')[:2]:
            title = a.get_text(strip=True)
            link = a['href']
            if not link.startswith("http"):
                link = f"https://www.orientaldaily.com.my{link}"
            news_items.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")

        return news_items if news_items else ["❌ 东方日报抓取失败：未找到内容"]
    except Exception as e:
        return [f"❌ 东方日报抓取失败：{str(e)}"]

# ✅ 发送 Telegram 消息
def send_telegram(message):
    try:
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        res = requests.post(API_URL, json=payload, timeout=15)
        res.raise_for_status()
        print("✅ 已发送：", message[:30])
    except Exception as e:
        print("❌ 发送失败：", str(e))

# ✅ 主程序
def main():
    print("开始抓取新闻...")
    all_news = []
    all_news += fetch_chinapress()
    all_news += fetch_oriental()

    print(f"共抓到 {len(all_news)} 条新闻，开始推送...")
    for news in all_news:
        if "❌" not in news:
            send_telegram(news)
            time.sleep(1)
    print("✅ 所有新闻已推送完毕！")

if __name__ == "__main__":
    main()
