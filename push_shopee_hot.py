import requests
import os

# Telegram Bot
TOKEN = os.environ.get("TG_BOT_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def fetch_shopee_hot(keyword="耳机", limit=3):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    search_url = f"https://shopee.com.my/api/v4/search/search_items?by=sales&keyword={keyword}&limit={limit}&newest=0&order=desc&page_type=search"

    try:
        res = requests.get(search_url, headers=headers, timeout=10)
        data = res.json()

        items = data["items"]
        message = f"🛒 <b>Shopee 热卖商品 TOP{limit}：{keyword}</b>\n"

        for idx, item in enumerate(items, 1):
            detail = item["item_basic"]
            name = detail["name"]
            price = detail["price"] / 100000
            sold = detail["sold"]
            itemid = detail["itemid"]
            shopid = detail["shopid"]
            url = f"https://shopee.com.my/product/{shopid}/{itemid}"

            message += f"\n{idx}️⃣ {name[:30]} 🔥\n📦 销量：{sold} | 💰 RM {price:.2f}\n🔗 {url}\n"

        return message

    except Exception as e:
        return f"❌ 获取 Shopee 热卖失败：{e}"

def send(msg):
    return requests.post(API, json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }).ok

if __name__ == "__main__":
    result = fetch_shopee_hot("耳机")  # 你可以改成“手机壳” “耳机” “USB”等
    send(result)
