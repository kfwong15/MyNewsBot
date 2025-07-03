import os
import requests
from bs4 import BeautifulSoup

# 读取 GitHub Secrets 中的环境变量
TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def fetch_sinchew():
    url = "https://www.sinchew.com.my/"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        # 找到首页的第一篇新闻
        article = soup.find("a", class_="article-link")
        if not article:
            raise Exception("未找到文章链接")
        title = article.find("h2").get_text(strip=True)
        link = article["href"]

        # 如果是相对链接，补上域名
        if not link.startswith("http"):
            link = "https://www.sinchew.com.my" + link

        return f"📰 <b>星洲日报</b>\n\n📌 {title}\n🔗 {link}"
    except Exception as e:
        return f"❌ 获取星洲新闻失败: {e}"

def send_to_telegram(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # 支持粗体 / 换行
    }
    response = requests.post(API_URL, json=payload)
    return response.ok

if __name__ == "__main__":
    news = fetch_sinchew()
    if news:
        success = send_to_telegram(news)
        print("✅ 推送成功" if success else "❌ 推送失败")
