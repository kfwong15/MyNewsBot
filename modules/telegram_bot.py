import os
import logging
import asyncio
import html
from dotenv import load_dotenv
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('telegram_bot')

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID   = os.getenv('TG_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO  = os.getenv('GITHUB_REPO')


async def send_telegram_message(text: str, parse_mode=None) -> bool:
    bot = Bot(token=TG_BOT_TOKEN)
    try:
        await bot.send_message(chat_id=TG_CHAT_ID, text=text, parse_mode=parse_mode)
        return True
    except Exception as e:
        logger.error(f"send_message 失败: {e}", exc_info=True)
        return False


async def send_news_to_telegram(news_list: list) -> int:
    bot = Bot(token=TG_BOT_TOKEN)
    sent = 0

    for item in news_list:
        title   = html.escape(item.get('title', ''))
        content = html.escape(item.get('content') or '')
        link    = item.get('link', '')
        image   = item.get('image')

        caption = f"{title}\n\n{content}"

        try:
            if image:
                # 推送图片 + 跳转按钮
                await bot.send_photo(
                    chat_id=TG_CHAT_ID,
                    photo=image,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔗 阅读原文", url=link)]
                    ])
                )
            else:
                # 无图则纯文本推送
                await bot.send_message(
                    chat_id=TG_CHAT_ID,
                    text=f"{caption}\n\n{link}"
                )

            sent += 1
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"推送失败: {e}", exc_info=True)

    logger.info(f"✅ 成功推送 {sent}/{len(news_list)} 条新闻")
    return sent


async def start_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        rf"你好 {user.mention_html()}！正在触发新闻抓取…"
    )

    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    payload = {'ref': 'main'}
    url = (
        f"https://api.github.com/repos/{GITHUB_REPO}"
        "/actions/workflows/thestar_news_bot.yml/dispatches"
    )

    try:
        r = __import__('requests').post(url, headers=headers, json=payload)
        if r.status_code == 204:
            await update.message.reply_text("✅ 已触发，稍后将推送最新新闻。")
        else:
            await update.message.reply_text(f"❌ 触发失败：{r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ 异常：{e}")
        logger.exception("GitHub Dispatch 出错")


def setup_handlers(app: Application):
    app.add_handler(CommandHandler("start", start_command))
    logger.info("Telegram handlers 注册完成")
