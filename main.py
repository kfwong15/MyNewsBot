import os
import asyncio
import logging
from dotenv import load_dotenv
from modules import telegram_bot, news_crawler
from modules.telegram_bot import setup_handlers, send_news_to_telegram
from telegram.ext import Application

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('main')

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')

async def github_actions_trigger():
    """Main function for GitHub Actions trigger"""
    logger.info("Starting news crawl task")
    
    # 1. Fetch news
    all_news = news_crawler.fetch_news()
    logger.info(f"Fetched {len(all_news)} news items")
    
    # 2. Select random news
    selected_news = news_crawler.select_random_news(all_news)
    logger.info(f"Selected {len(selected_news)} news items for sending")
    
    # 3. Send to Telegram
    await send_news_to_telegram(selected_news)
    
    logger.info("News sending completed")

def main():
    """Main entry point"""
    # Check required environment variables
    required_vars = ['TG_BOT_TOKEN', 'GITHUB_TOKEN', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    # Determine run mode
    if os.getenv('GITHUB_ACTIONS') == 'true':
        asyncio.run(github_actions_trigger())
    else:
        # Start Telegram Bot
        application = Application.builder().token(TG_BOT_TOKEN).build()
        setup_handlers(application)
        
        logger.info("Bot is running...")
        application.run_polling()

if __name__ == "__main__":
    main()
