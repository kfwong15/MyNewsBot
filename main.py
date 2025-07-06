import os
import asyncio
import logging
from dotenv import load_dotenv
from modules import telegram_bot, news_crawler
from modules.telegram_bot import setup_handlers, send_news_to_telegram
from telegram.ext import Application

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('main')

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')

async def github_actions_trigger():
    """GitHub Actions 触发的主函数"""
    logger.info("开始执行新闻抓取任务")
    
    try:
        # 1. 抓取新闻
        all_news = news_crawler.fetch_news()
        logger.info(f"共抓取 {len(all_news)} 条新闻")
        
        # 2. 随机选择新闻
        selected_news = news_crawler.select_random_news(all_news)
        logger.info(f"随机选择 {len(selected_news)} 条新闻进行推送")
        
        # 3. 推送到Telegram
        await send_news_to_telegram(selected_news)
        
        logger.info("新闻推送完成")
    except Exception as e:
        logger.exception("执行过程中发生错误")

def main():
    """主程序入口"""
    # 检查环境变量
    required_vars = ['TG_BOT_TOKEN', 'GITHUB_TOKEN', 'OPENAI_API_KEY', 'TG_CHAT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少必需的环境变量: {', '.join(missing_vars)}")
        return
    
    # 判断运行模式
    if os.getenv('GITHUB_ACTIONS') == 'true':
        asyncio.run(github_actions_trigger())
    else:
        # 启动Telegram Bot
        application = Application.builder().token(TG_BOT_TOKEN).build()
        telegram_bot.setup_handlers(application)
        
        logger.info("DeepSeek新闻助手正在运行...")
        application.run_polling()

if __name__ == "__main__":
    main()
