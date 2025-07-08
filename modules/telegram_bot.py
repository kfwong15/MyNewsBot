import os
import logging
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import requests
import asyncio
from modules import news_crawler, ai_assistant
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('telegram_bot')

# 获取环境变量
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

async def send_telegram_message(message, parse_mode='Markdown'):
    """发送文本消息到 Telegram"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        logger.error("无法发送消息: TG_BOT_TOKEN 或 TG_CHAT_ID 未设置")
        return False
    
    try:
        bot = Bot(token=TG_BOT_TOKEN)
        await bot.send_message(
            chat_id=TG_CHAT_ID,
            text=message,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        logger.error(f"发送Telegram消息失败: {e}", exc_info=True)
        return False

# ... 原有的命令处理函数保持不变 (start_command, ask_command, etc.) ...

async def send_news_to_telegram(news_list):
    """将新闻推送到Telegram"""
    if not news_list:
        logger.warning("没有新闻需要发送")
        return
    
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        logger.error("TG_BOT_TOKEN 或 TG_CHAT_ID 未设置，跳过新闻推送")
        return False
    
    try:
        bot = Bot(token=TG_BOT_TOKEN)
        sent_count = 0
        
        # 按类别分组新闻
        news_by_category = {}
        for news in news_list:
            if news['category'] not in news_by_category:
                news_by_category[news['category']] = []
            news_by_category[news['category']].append(news)
        
        # 发送新闻
        for category, news_items in news_by_category.items():
            category_title = f"📰 *{category.upper()} 新闻* 📰"
            await bot.send_message(chat_id=TG_CHAT_ID, text=category_title, parse_mode='Markdown')
            
            for news in news_items:
                try:
                    message = news_crawler.format_news_message(news)
                    
                    if news.get('img_url'):
                        await bot.send_photo(
                            chat_id=TG_CHAT_ID,
                            photo=news['img_url'],
                            caption=message,
                            parse_mode='Markdown'
                        )
                    else:
                        await bot.send_message(
                            chat_id=TG_CHAT_ID,
                            text=message,
                            parse_mode='Markdown'
                        )
                    
                    sent_count += 1
                    # 避免发送过快
                    await asyncio.sleep(1.5)
                except Exception as e:
                    logger.error(f"发送新闻失败: {e}", exc_info=True)
        
        logger.info(f"成功发送 {sent_count}/{len(news_list)} 条新闻")
        return sent_count
    except Exception as e:
        logger.error(f"新闻推送失败: {e}", exc_info=True)
        return 0

# ... 原有的 setup_handlers 函数保持不变 ...
