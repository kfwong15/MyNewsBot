import os
import asyncio
import logging
from dotenv import load_dotenv
from modules import news_crawler
from modules.telegram_bot import (
    setup_handlers, send_news_to_telegram, send_telegram_message
)
from telegram.ext import Application
from datetime import datetime

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('main')

async def send_status(status: str, details: str):
    """
    发送抓取状态报告
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"📰 新闻机器人状态报告 ({ts})\n\n{status}\n\n{details}"
    await send_telegram_message(msg, parse_mode=None)

async def crawl_and_send():
    start = datetime.now()
    news = news_crawler.fetch_news()
    count_all = len(news)

    selected = news_crawler.select_random_news(news, count=10)
    count_sel = len(selected)

    sent = await send_news_to_telegram(selected)

    dur = (datetime.now() - start).total_seconds()
    details = (
        f"• 抓取总数: {count_all} 条\n"
        f"• 选择推送: {count_sel} 条\n"
        f"• 实际推送: {sent} 条\n"
        f"• 耗时: {dur:.2f} 秒"
    )
    status = "✅ 抓取并推送完成" if sent else "❌ 抓取或推送出错"
    await send_status(status, details)

def main():
    token = os.getenv("TG_BOT_TOKEN")
    if os.getenv("GITHUB_ACTIONS") == "true":
        # GitHub Actions 定时或手动触发
        asyncio.run(crawl_and_send())
    else:
        # 本地/长期运行模式，启动 Telegram Bot
        app = Application.builder().token(token).build()
        setup_handlers(app)
        logger.info("DeepSeek 新闻助手 启动中…")
        app.run_polling()

if __name__ == "__main__":
    main()
