import asyncio
from datetime import datetime
from dotenv import load_dotenv

from modules.news_crawler import fetch_chinapress_news, select_random_news
from modules.telegram_bot import send_telegram_message, send_news_to_telegram


def main():
    load_dotenv()

    news = fetch_chinapress_news(max_items=50)
    if not news:
        asyncio.run(send_telegram_message("❌ 抓取失败，未获取到中国报新闻"))
        return

    # 抓取报告
    debug = f"🔍 中国报抓取到 {len(news)} 条新闻：\n"
    for i, n in enumerate(news[:10], 1):
        debug += f"{i}. {n['title']}\n{n['link']}\n\n"
    asyncio.run(send_telegram_message(debug))

    # 推送 10 条
    selected = select_random_news(news, 10)
    sent = asyncio.run(send_news_to_telegram(selected))

    summary = (
        f"📰 中国报推送报告\n"
        f"• 抓取: {len(news)} 条\n"
        f"• 推送: {sent} 条\n"
        f"• 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    asyncio.run(send_telegram_message(summary))


if __name__ == "__main__":
    main()