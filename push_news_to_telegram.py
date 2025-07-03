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

        # ✅ 保存 HTML 页面到本地
        with open("sinchew.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        soup = BeautifulSoup(response.text, "html.parser")
        ...




def send_to_telegram(message):
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    r = requests.post(API_URL, json=payload)
    return r.ok

if __name__ == "__main__":
    news = fetch_sinchew()
    if news:
        ok = send_to_telegram(news)
        print("✅ 推送成功" if ok else "❌ 推送失败")
