import requests
import os

# Telegram Bot 信息（从 GitHub Secrets 读取）
TG_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
TG_API = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

# 要抓的 Shopee 关键词
KEYWORDS = ["耳机", "手机壳", "行充"]  # ✅ 你可以改成任何类目
ITEM_LIMIT = 3  # 每个关键词显示几件热销商品


def fetch_shopee_hot(keyword, limit=3):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    url = f"https://shopee.com.my/api/v4/search/search_items?by=sales&keyword={keyword}&limit={limit}&newest=0&order=desc&page_type=search"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        items = res.json()["items"]
        if not items:
            return f"\n⚠️ 找不到 {keyword} 商品\n"

        msg = f"\n🔍 <b>{keyword} 热卖 TOP{limit}</b>：\n"
        for i, item in enumerate(items, 1):
            info = item["item_basic"]
            name = info["name"]
            price = info["price"] / 100000
            sold = info["sold"]
            itemid = info["itemid"]
            shopid = info["shopid"]
            link = f"https://shopee.com.my/product/{shopid}/{itemid}"
            msg += f"{i}️⃣ {name[:30]}\n📦 销量：{sold} | 💰 RM {price:.2f}\n🔗 {link}\n\n"
        return msg

    except Exception as e:
        return f"\n❌ 抓取 {keyword} 失败：{e}\n"


def send_telegram(msg):
    data = {
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    return requests.post(TG_API, json=data).ok


if __name__ == "__main__":
    full_msg = "🛒 <b>Shopee 热卖商品（自动抓取）</b>\n"
    for kw in KEYWORDS:
        full_msg += fetch_shopee_hot(kw, ITEM_LIMIT)
    send_telegram(full_msg)
