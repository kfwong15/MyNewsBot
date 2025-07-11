import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from modules.news_crawler import fetch_news, select_random_news
from modules.telegram_bot import send_telegram_message, send_news_to_telegram
from telegram.ext import Application

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('main')


async def crawl_and_send():
    start = datetime.now()

    # 1. 同步调用 fetch_news，已返回 list
    news = fetch_news()
    total = len(news)

    if total == 0:
        await send_telegram_message("❌ 抓取失败，未获取到任何新闻")
        return

    # 2. 调试列表：标题 + 链接
    debug = f"🔍 抓取到 {total} 条新闻：\n"
    for i, n in enumerate(news, 1):
        debug += f"{i}. {n['title']}\n{n['link']}\n\n"
    await send_telegram_message(debug)

    # 3. 随机取 10 条并推送
    selected = select_random_news(news, 10)
    sent = await send_news_to_telegram(selected)

    # 4. 状态报告
    dur = (datetime.now() - start).total_seconds()
    summary = (
        f"📰 状态报告\n"
        f"• 抓取: {total} 条\n"
        f"• 推送: {sent} 条\n"
        f"• 耗时: {dur:.1f} 秒"
    )
    await send_telegram_message(summary)


def main():
    if os.getenv('GITHUB_ACTIONS') == 'true':
        asyncio.run(crawl_and_send())
    else:
        app = Application.builder().token(os.getenv('TG_BOT_TOKEN')).build()
        from modules.telegram_bot import setup_handlers
        setup_handlers(app)
        logger.info("Bot 启动中…")
        app.run_polling()


if __name__ == "__main__":
    main()
