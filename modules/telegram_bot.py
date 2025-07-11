import os
import logging
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import requests
import asyncio
from modules import news_crawler, ai_assistant
from datetime import datetime
import html

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
TG_CHAT_ID = os.getenv('TG_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

async def send_telegram_message(message, parse_mode=None):
    """发送文本消息到 Telegram"""
    global TG_CHAT_ID

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

        # 处理群组迁移错误
        if "Group migrated to supergroup" in str(e):
            try:
                error_str = str(e)
                start_idx = error_str.find("New chat id: ") + len("New chat id: ")
                end_idx = error_str.find("\n", start_idx) if "\n" in error_str else len(error_str)
                new_chat_id = error_str[start_idx:end_idx].strip()

                if new_chat_id:
                    logger.warning(f"检测到群组迁移，新群组ID: {new_chat_id}")
                    os.environ['TG_CHAT_ID'] = new_chat_id
                    TG_CHAT_ID = new_chat_id

                    await bot.send_message(
                        chat_id=new_chat_id,
                        text=message,
                        parse_mode=parse_mode
                    )
                    return True
            except Exception as inner_e:
                logger.error(f"处理群组迁移失败: {inner_e}", exc_info=True)

        return False

async def send_news_to_telegram(news_list):
    """将新闻列表发送到 Telegram 群组"""
    bot = Bot(token=TG_BOT_TOKEN)
    sent_count = 0

    for news in news_list:
        try:
            # 转义标题和链接，避免 Markdown 报错
            safe_title = html.escape(news['title'])
            safe_link = html.escape(news['link'])
            message = f"{safe_title}\n{safe_link}"

            # 使用纯文本发送
            await bot.send_message(
                chat_id=TG_CHAT_ID,
                text=message,
                parse_mode=None
            )
            sent_count += 1
            await asyncio.sleep(2)  # 避免 Telegram 限速
        except Exception as e:
            logger.error(f"发送新闻失败: {e}", exc_info=True)

            # 后备尝试：发送未转义文本
            try:
                fallback_message = f"{news['title']}\n{news['link']}"
                await bot.send_message(
                    chat_id=TG_CHAT_ID,
                    text=fallback_message,
                    parse_mode=None
                )
                sent_count += 1
                await asyncio.sleep(2)
            except Exception as fallback_e:
                logger.error(f"后备发送也失败: {fallback_e}", exc_info=True)

    logger.info(f"成功发送 {sent_count}/{len(news_list)} 条新闻")
    return sent_count

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令 - 触发 GitHub Actions 抓取新闻"""
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
            error_msg = f"❌ 触发失败，状态码：{response.status_code}"
            await update.message.reply_text(error_msg)
            logger.error(error_msg)
    except Exception as e:
        error_msg = f"❌ 触发失败: {str(e)}"
        await update.message.reply_text(error_msg)
        logger.exception("触发 GitHub 工作流失败")

def setup_handlers(application):
    """设置 Telegram 命令处理器"""
    from modules.ai_assistant import (
        ask_command, summary_command, translate_command,
        help_command, handle_message
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("translate", translate_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.COMMAND, handle_message))
    logger.info("Telegram 命令处理器设置完成")
