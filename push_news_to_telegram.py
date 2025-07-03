import requests
from bs4 import BeautifulSoup
import json
import os

TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
PUSHED_FILE = "pushed.json"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def get_sinchew_news():
    url = "https://www.sinchew.com.my/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    news = []
    for a in soup.select("a.item-title"):
        title = a.get_text(strip=True)
        link = a['href']
        if not link.startswith("http"):
            link = "https://www.sinchew.com.my" + link
        news.append({"title": title, "link": link})
    return news

def load_pushed():
    if os.path.exists(PUSHED_FILE):
        with open(PUSHED_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_pushed(ids):
    with open(PUSHED_FILE, 'w') as f:
        json.dump(list(ids), f)

def main():
    pushed_ids = load_pushed()
    new_ids = set()
    for item in get_sinchew_news():
        if item["link"] not in pushed_ids:
            message = f"📰 <b>{item['title']}</b>\n🔗 {item['link']}"
            send_telegram_message(message)
            print("✅ 推送：" + item["title"])
        new_ids.add(item["link"])
    save_pushed(new_ids)

if __name__ == "__main__":
    main()
