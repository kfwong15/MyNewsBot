import os
import logging
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import asyncio
import html

load_dotenv()
logger = logging.getLogger('telegram_bot')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

async def send_telegram_message(message: str, parse_mode=None) -> bool:
    """
    发送纯文本状态消息
    """
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        logger.error("TG_BOT_TOKEN 或 TG_CHAT_ID 未设置")
        return False

    bot = Bot(token=TG_BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=TG_CHAT_ID,
            text=message,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        logger.error(f"send_message 失败: {e}", exc_info=True)
        return False

async def send_news_to_telegram(news_list: list) -> int:
    """
    将抓取到的新闻列表逐条推送到 Telegram，若有图片则附上。
    返回成功发送的条数。
    """
    bot = Bot(token=TG_BOT_TOKEN)
    sent = 0

    for item in news_list:
        title = html.escape(item["title"])
        link = html.escape(item["link"])
        caption = f"{title}\n{link}"

        try:
            if item.get("image"):
                # 附带图片推送
                await bot.send_photo(
                    chat_id=TG_CHAT_ID,
                    photo=item["image"],
                    caption=caption,
                    parse_mode=None
                )
            else:
                # 纯文本推送
                await bot.send_message(
                    chat_id=TG_CHAT_ID,
                    text=caption,
                    parse_mode=None
                )

            sent += 1
            await asyncio.sleep(2)  # 限速
        except Exception as e:
            logger.error(f"推送新闻失败: {e}", exc_info=True)

    logger.info(f"✅ 成功推送 {sent}/{len(news_list)} 条新闻")
    return sent

async def start_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /start 命令：触发 GitHub Actions 工作流抓取新闻
    """
    user = update.effective_user
    await update.message.reply_html(
        rf"你好 {user.mention_html()}！准备抓取新闻..."
    )

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"ref": "main"}

    try:
        res = requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/thestar_news_bot.yml/dispatches",
            headers=headers, json=payload
        )
        if res.status_code == 204:
            await update.message.reply_text("✅ 已触发抓取，稍候将推送最新新闻。")
        else:
            await update.message.reply_text(f"❌ 触发失败：{res.status_code}")
            logger.error(f"GitHub Dispatch 失败: {res.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ 触发异常：{e}")
        logger.exception("Trigger GitHub Actions 出错")

def setup_handlers(app: Application):
    """
    注册 /start 命令
    """
    app.add_handler(CommandHandler("start", start_command))
    logger.info("Telegram handlers 已注册")
