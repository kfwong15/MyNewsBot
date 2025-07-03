import requests
import os

# 从环境变量读取 Telegram 配置
TG_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
TG_API = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

# 要抓的关键词
KEYWORDS = ["耳机", "手机壳", "行充"]
ITEM_LIMIT = 3  # 每个关键词显示几件商品

def fetch_shopee_hot(keyword, limit=3):
    url = f"https://shopee.com.my/api/v4/search/search_items?by=sales&keyword={keyword}&limit={limit}&newest=0&order=desc&page_type=search"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        items = data["items"]
        if not items:
            return f"\n⚠️ 没找到「{keyword}」的热卖商品\n"

        msg = f"\n🔍 <b>{keyword} 热卖 TOP{limit}</b>：\n"
        for idx, item in enumerate(items, 1):
            info = item["item_basic"]
            name = info["name"]
            price = info["price"] / 100000
            sold = info["sold"]
            itemid = info["itemid"]
            shopid = info["shopid"]
            link = f"https://shopee.com.my/product/{shopid}/{itemid}"
            msg += f"{idx}️⃣ {name[:30]}\n📦 销量：{sold} | 💰 RM {price:.2f}\n🔗 {link}\n\n"
        return msg

    except Exception as e:
        return f"\n❌ 获取「{keyword}」失败：{e}"

def send_telegram(msg):
    return requests.post(TG_API, json={
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }).ok

if __name__ == "__main__":
    final_msg = "🛒 <b>Shopee 热卖商品</b>\n"
    for kw in KEYWORDS:
        final_msg += fetch_shopee_hot(kw, ITEM_LIMIT)
    send_telegram(final_msg)
