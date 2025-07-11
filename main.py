import os, asyncio, logging
from datetime import datetime
from dotenv import load_dotenv
from modules import news_crawler
from modules.telegram_bot import (
    setup_handlers, send_news_to_telegram, send_telegram_message
)
from telegram.ext import Application

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('main')

async def send_status_report(status: str, details: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"📰 新闻机器人状态报告 ({ts})\n\n{status}\n\n{details}"
    await send_telegram_message(msg, parse_mode=None)

async def crawl_and_push():
    start = datetime.now()
    news = news_crawler.fetch_news()
    total = len(news)
    selected = news_crawler.select_random_news(news, count=10)
    sent = await send_news_to_telegram(selected)
    dur = (datetime.now() - start).total_seconds()
    details = f"• 抓取总数: {total} 条\n• 推送: {sent} 条\n• 耗时: {dur:.2f} 秒"
    status = "✅ 抓取并推送完成" if sent else "❌ 抓取或推送失败"
    await send_status_report(status, details)

def main():
    if os.getenv("GITHUB_ACTIONS") == "true":
        asyncio.run(crawl_and_push())
    else:
        token = os.getenv("TG_BOT_TOKEN")
        app = Application.builder().token(token).build()
        setup_handlers(app)
        logger.info("Bot 启动中…")
        app.run_polling()

if __name__ == "__main__":
    main()
