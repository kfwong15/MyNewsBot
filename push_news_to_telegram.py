import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def fetch_sinchew():
    url = "https://www.sinchew.com.my/"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("div.article-item a.article-link")
        for card in cards:
            href = card.get("href", "")
            if "/news/" not in href:
                continue
            title_tag = card.find("h2") or card.find("p", class_="title")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = href if href.startswith("http") else "https://www.sinchew.com.my" + href
            return f"📰 <b>星洲日报</b>\n\n📌 {title}\n🔗 {link}"
        raise Exception("未找到有效新闻卡片")
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
