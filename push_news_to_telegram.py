import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


import os, requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def fetch_oriental():
    url = "https://www.orientaldaily.com.my/"
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 找新闻列表里第一个含链接的 <a> 标签
        a = soup.select_one("div.clearfix ul li a[href*='/news/']")
        if not a:
            raise Exception("未找到新闻链接")

        title = a.get_text(strip=True)
        link = a["href"]
        if not link.startswith("http"):
            link = "https://www.orientaldaily.com.my" + link

        return f"📰 <b>东方日报</b>\n\n📌 {title}\n🔗 {link}"
    except Exception as e:
        return f"❌ 获取东方日报失败: {e}"

def send(msg):
    return requests.post(API, json={"chat_id":CHAT_ID, "text":msg, "parse_mode":"HTML"}).ok

if __name__ == "__main__":
    news = fetch_oriental()
    if news:
        res = send(news)
        print("✅ 推送成功" if res else "❌ 推送失败")
def send_to_telegram(message):
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    r = requests.post(API_URL, json=payload)
    return r.ok

if __name__ == "__main__":
    news = fetch_sinchew()
    if news:
        ok = send_to_telegram(news)
        print("✅ 推送成功" if ok else "❌ 推送失败")
