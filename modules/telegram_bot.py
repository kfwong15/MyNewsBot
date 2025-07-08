import os
import logging
import telegram
from telegram.error import TelegramError, ChatMigrated
from dotenv import load_dotenv

# 加载 .env 文件中的变量
load_dotenv()

# 读取环境变量
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')  # 初始 chat_id

# 日志配置
logger = logging.getLogger("telegram_bot")
logging.basicConfig(level=logging.INFO)

# 初始化 bot
bot = telegram.Bot(token=TG_BOT_TOKEN)

def send_news_batch(news_items, title="📢 Latest News"):
    """
    将多条新闻通过 Telegram 分批发送
    """
    global TG_CHAT_ID  # 允许更新 chat_id

    try:
        # 发送分类标题
        bot.send_message(chat_id=TG_CHAT_ID, text=title, parse_mode='Markdown')
        
        # 分批发送
        for news in news_items:
            message = format_news_message(news)
            try:
                bot.send_message(chat_id=TG_CHAT_ID, text=message, parse_mode='Markdown', disable_web_page_preview=False)
            except TelegramError as e:
                logger.error(f"发送单条新闻失败: {e}")
    
    except ChatMigrated as e:
        new_chat_id = e.new_chat_id
        logger.warning(f"群组迁移，新的 chat_id 为: {new_chat_id}")
        TG_CHAT_ID = new_chat_id

        # 尝试重新发送标题
        try:
            bot.send_message(chat_id=TG_CHAT_ID, text=title, parse_mode='Markdown')
        except TelegramError as ex:
            logger.error(f"迁移后重新发送失败: {ex}")
    
    except TelegramError as e:
        logger.error(f"Telegram 消息发送失败: {e}")
