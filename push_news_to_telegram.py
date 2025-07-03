import os
import requests
from bs4 import BeautifulSoup

# Telegram Bot Token & Chat ID 来自 GitHub Secrets
TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

#####
def fetch_sinchew():
    url = "https://www.sinchew.com.my/"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找第一个首页新闻（使用 class 名更精准）
        article = soup.select_one("div.article-card a[href*='/news/']")
        if not article:
            raise Exception("未找到有效新闻链接")

        # 新闻标题
        title_tag = article.select_one(".title")
        if not title_tag:
            title = article.get("title") or "（无标题）"
        else:
            title = title_tag.get_text(strip=True)

        # 新闻链接
        link = article["href"]
        if not link.startswith("http"):
            link = "https://www.sinchew.com.my" + link

        return f"📰 <b>星洲日报</b>\n\n📌 {title}\n🔗 {link}"

    except Exception as e:
        return f"❌ 获取星洲新闻失败: {e}"


#####
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
