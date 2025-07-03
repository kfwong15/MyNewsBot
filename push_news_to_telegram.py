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
        soup = BeautifulSoup(response.text, "html.parser")
        headline = soup.find("h2", class_="article-title").get_text(strip=True)
        link = soup.find("h2", class_="article-title").find("a")["href"]
        return f"📰 【星洲日报】{headline}\n🔗 {link}"
    except Exception as e:
        return f"❌ 获取星洲新闻失败: {e}"

def send_to_telegram(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(API_URL, json=payload)
    return response.ok

if __name__ == "__main__":
    news = fetch_sinchew()
    if news:
        success = send_to_telegram(news)
        print("✅ 推送成功" if success else "❌ 推送失败")
