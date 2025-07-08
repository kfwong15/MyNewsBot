import os
import logging
import telegram
from telegram.error import TelegramError, ChatMigrated
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取环境变量
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')  # 初始 chat_id

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("telegram_bot")

# 初始化 bot
bot = telegram.Bot(token=TG_BOT_TOKEN)

def escape_markdown(text):
    """转义 Markdown 特殊字符"""
    if not text:
        return ""
    for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(char, f'\\{char}')
    return text

def format_news_message(news):
    """格式化单条新闻为 Telegram Markdown 消息"""
    title = escape_markdown(news.get('title', '无标题'))
    summary = escape_markdown(news.get('summary', ''))
    time_str = escape_markdown(news.get('time', ''))
    link = news.get('link', '#')
    return (
        f"🔹 *{title}*\n"
        f"⏰ {time_str}\n"
        f"{summary}\n"
        f"[阅读全文]({link})"
    )

def send_news_batch(news_items, title="📰 今日新闻更新"):
    """分批发送多条新闻消息到 Telegram"""
    global TG_CHAT_ID  # 允许更新 chat_id 变量（处理群迁移）

    try:
        # 先发送标题
        bot.send_message(chat_id=TG_CHAT_ID, text=title, parse_mode='Markdown')

        for news in news_items:
            message = format_news_message(news)
            try:
                bot.send_message(
                    chat_id=TG_CHAT_ID,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )
            except TelegramError as e:
                logger.error(f"发送单条新闻失败: {e}")

    except ChatMigrated as e:
        # 处理群迁移错误，更新 chat_id 并重发
        new_chat_id = e.new_chat_id
        logger.warning(f"群组迁移，新的 chat_id 为: {new_chat_id}")
        TG_CHAT_ID = new_chat_id

        try:
            bot.send_message(chat_id=TG_CHAT_ID, text=title, parse_mode='Markdown')
            for news in news_items:
                message = format_news_message(news)
                try:
                    bot.send_message(chat_id=TG_CHAT_ID, text=message, parse_mode='Markdown')
                except TelegramError as ex:
                    logger.error(f"发送失败: {ex}")
        except TelegramError as ex:
            logger.error(f"群迁移后发送标题失败: {ex}")

    except TelegramError as e:
        logger.error(f"Telegram 发送失败: {e}")
