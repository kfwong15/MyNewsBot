import os
import requests
from bs4 import BeautifulSoup

# 获取 Telegram Bot Token 和 Chat ID（需放在环境变量中或 GitHub Secrets）
TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# 东方日报抓取函数
def fetch_oriental():
    url = "https://www.orientaldaily.com.my/"
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 选择第一个新闻链接
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

# 发送到 Telegram 群组或频道
def send(msg):
    return requests.post(API, json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }).ok

# 主入口
if __name__ == "__main__":
    news = fetch_oriental()
    if news:
        res = send(news)
        print("✅ 推送成功" if res else "❌ 推送失败")
