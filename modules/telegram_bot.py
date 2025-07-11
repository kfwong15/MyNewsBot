import os
import logging
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import requests
import asyncio
import html

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('telegram_bot')

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

async def send_telegram_message(message, parse_mode=None):
    bot = Bot(token=TG_BOT_TOKEN)
    try:
        await bot.send_message(chat_id=TG_CHAT_ID, text=message, parse_mode=parse_mode)
        return True
    except Exception as e:
        logger.error(f"发送失败: {e}", exc_info=True)
        return False

async def send_news_to_telegram(news_list):
    bot = Bot(token=TG_BOT_TOKEN)
    sent_count = 0

    for news in news_list:
        try:
            caption = html.escape(news['title']) + "\n" + html.escape(news['link'])

            if news.get("image"):
                await bot.send_photo(
                    chat_id=TG_CHAT_ID,
                    photo=news["image"],
                    caption=caption,
                    parse_mode=None
                )
            else:
                await bot.send_message(
                    chat_id=TG_CHAT_ID,
                    text=caption,
                    parse_mode=None
                )

            sent_count += 1
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"发送新闻失败: {e}", exc_info=True)

    logger.info(f"成功发送 {sent_count}/{len(news_list)} 条新闻")
    return sent_count

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        rf"你好 {user.mention_html()}！我是 DeepSeek 新闻助手 🤖\n正在触发新闻抓取..."
    )

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    payload = {'ref': 'main'}

    try:
        response = requests.post(
            f'https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/thestar_news_bot.yml/dispatches',
            headers=headers,
            json=payload
        )

        if response.status_code == 204:
            await update.message.reply_text("✅ 成功触发新闻抓取！稍等几分钟即可收到最新马来西亚新闻")
        else:
            await update.message.reply_text(f"❌ 触发失败，状态码：{response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ 触发失败: {str(e)}")
        logger.exception("GitHub 触发失败")

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    logger.info("Telegram 命令处理器设置完成")
