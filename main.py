import os
import asyncio
import logging
from dotenv import load_dotenv
from modules import news_crawler
from modules.telegram_bot import setup_handlers, send_news_to_telegram, send_telegram_message
from telegram.ext import Application
from datetime import datetime

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('main')

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

async def send_status_notification(status, details=""):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📰 *新闻机器人状态报告* ({timestamp})\n\n"

        if status == "success":
            message += "✅ 新闻抓取任务完成\n\n" + details
        elif status == "partial_success":
            message += "⚠️ 新闻抓取部分完成\n\n" + details
        elif status == "warning":
            message += "⚠️ 新闻抓取遇到问题\n\n" + details
        else:
            message += "❌ 新闻抓取失败\n\n" + details

        await send_telegram_message(message, parse_mode=None)
    except Exception as e:
        logger.error(f"发送状态通知失败: {e}", exc_info=True)

async def github_actions_trigger():
    start_time = datetime.now()
    logger.info("开始执行新闻抓取任务")

    try:
        all_news = news_crawler.fetch_news()
        news_count = len(all_news)
        selected_news = news_crawler.select_random_news(all_news)
        selected_count = len(selected_news)

        sent_count = await send_news_to_telegram(selected_news)

        duration = (datetime.now() - start_time).total_seconds()
        details = (
            f"• 抓取分类: {len(news_crawler.NEWS_CATEGORIES)}\n"
            f"• 获取新闻: {news_count} 条\n"
            f"• 推送新闻: {sent_count} 条\n"
            f"• 耗时: {duration:.2f} 秒"
        )

        if news_count == 0:
            status = "error"
            details += "\n\n⚠️ 未抓取到任何新闻，请检查爬虫"
        elif news_count < 10:
            status = "warning"
            details += f"\n\n⚠️ 只抓取到少量新闻 ({news_count} 条)，可能需要检查网站结构"
        elif sent_count < selected_count:
            status = "partial_success"
            details += f"\n\n⚠️ 部分新闻推送失败 ({sent_count}/{selected_count})"
        else:
            status = "success"

        await send_status_notification(status, details)

    except Exception as e:
        logger.exception("执行过程中发生错误")
        await send_status_notification("error", f"错误详情: {str(e)}")

def main():
    required_vars = ['TG_BOT_TOKEN', 'TG_CHAT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"缺少环境变量: {', '.join(missing_vars)}")
        asyncio.run(send_telegram_message(f"❌ 启动失败: 缺少环境变量 {', '.join(missing_vars)}"))
        return

    if os.getenv('GITHUB_ACTIONS') == 'true':
        asyncio.run(github_actions_trigger())
    else:
        application = Application.builder().token(TG_BOT_TOKEN).build()
        setup_handlers(application)
        logger.info("DeepSeek新闻助手正在运行...")
        application.run_polling()

if __name__ == "__main__":
    main()
