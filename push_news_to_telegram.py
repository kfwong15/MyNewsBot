import os
import requests
from bs4 import BeautifulSoup

# Telegram Bot Token & Chat ID 来自 GitHub Secrets
TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def fetch_sinchew():
    url = "https://www.sinchew.com.my/"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ 更稳健方式：遍历所有 a 标签，找出带 /news/ 且有标题的
        for a in soup.find_all("a", href=True):
            if "/news/" in a["href"] and a.find("h2"):
                title = a.find("h2").get_text(strip=True)
                link = a["href"]
                if not link.startswith("http"):
                    link = "https://www.sinchew.com.my" + link
                return f"📰 <b>星洲日报</b>\n\n📌 {title}\n🔗 {link}"

        raise Exception("未找到有效新闻链接")
    except Exception as e:
        return f"❌ 获取星洲新闻失败: {e}"

def send_to_telegram(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # 支持换行 / 粗体
    }
    response = requests.post(API_URL, json=payload)
    return response.ok

if __name__ == "__main__":
    news = fetch_sinchew()
    if news:
        success = send_to_telegram(news)
        print("✅ 推送成功" if success else "❌ 推送失败")
