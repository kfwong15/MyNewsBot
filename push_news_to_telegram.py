import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def fetch_sinchew():
    try:
        response = requests.get("https://www.sinchew.com.my/", timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
        })
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        # 获取第一个新闻卡片
        article = soup.select_one("div.article-item a.article-link")
        if article:
            title_tag = article.find("p", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else "（无标题）"
            link = article["href"]
            if not link.startswith("http"):
                link = "https://www.sinchew.com.my" + link
            return f"📰 <b>星洲日报</b>\n\n📌 {title}\n🔗 {link}"
        else:
            raise Exception("❌ 页面结构可能变了，找不到新闻区块")
    except Exception as e:
        return f"❌ 获取星洲新闻失败: {e}"


def send_to_telegram(message):
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    r = requests.post(API_URL, json=payload)
    return r.ok

if __name__ == "__main__":
    news = fetch_sinchew()
    if news:
        ok = send_to_telegram(news)
        print("✅ 推送成功" if ok else "❌ 推送失败")
