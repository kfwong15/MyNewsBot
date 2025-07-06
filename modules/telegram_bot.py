import os
import logging
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import requests
import asyncio
from modules import news_crawler, ai_assistant

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('telegram_bot')

# Get environment variables
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - trigger news crawl"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! 正在触发新闻抓取...",
    )
    
    # Trigger GitHub Actions workflow
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
    payload = {'ref': 'main'}
    
    try:
        response = requests.post(
            f'https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/thestar_news_bot.yml/dispatches',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 204:
            await update.message.reply_text("✅ 成功触发新闻抓取！稍等几分钟即可收到最新新闻")
        else:
            error_msg = f"❌ 触发失败，状态码：{response.status_code}"
            await update.message.reply_text(error_msg)
            logger.error(error_msg)
    except Exception as e:
        error_msg = f"❌ 触发失败: {str(e)}"
        await update.message.reply_text(error_msg)
        logger.exception("Failed to trigger GitHub workflow")

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask command - ask AI"""
    if not context.args:
        await update.message.reply_text("请提供问题，例如：/ask 马来西亚今天有什么新闻？")
        return
    
    question = " ".join(context.args)
    await update.message.reply_text("🤖 正在思考...")
    
    try:
        answer = ai_assistant.ask_ai(question)
        # Split long messages (Telegram has 4096 char limit)
        for i in range(0, len(answer), 4096):
            await update.message.reply_text(answer[i:i+4096])
    except Exception as e:
        logger.exception("Error processing AI request")
        await update.message.reply_text("⚠️ 处理您的请求时出错，请稍后再试")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /summary command - summarize URL"""
    if not context.args:
        await update.message.reply_text("请提供URL，例如：/summary https://example.com/article")
        return
    
    url = context.args[0]
    await update.message.reply_text("📝 正在生成摘要...")
    
    try:
        summary = ai_assistant.summarize_webpage(url)
        await update.message.reply_text(summary)
    except Exception as e:
        logger.exception("Error summarizing article")
        await update.message.reply_text("⚠️ 生成摘要时出错，请稍后再试")

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /translate command - translate text"""
    if not context.args:
        await update.message.reply_text("请提供要翻译的文本，例如：/translate Hello world")
        return
    
    text = " ".join(context.args)
    await update.message.reply_text("🌐 正在翻译...")
    
    try:
        translation = ai_assistant.translate_text(text)
        await update.message.reply_text(translation)
    except Exception as e:
        logger.exception("Error translating text")
        await update.message.reply_text("⚠️ 翻译时出错，请稍后再试")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - show help"""
    help_text = """
📚 MyNewsBot 使用指南：

/start - 手动触发新闻抓取
/ask <问题> - 向AI助手提问
/summary <URL> - 生成文章摘要
/translate <文本> - 翻译文本
/help - 显示帮助信息
"""
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle invalid commands"""
    await update.message.reply_text("⚠️ 无法识别的命令，使用 /help 查看可用指令")

async def send_news_to_telegram(news_list):
    """Send news to Telegram"""
    if not TG_CHAT_ID:
        logger.error("TG_CHAT_ID not set, skipping news sending")
        return
    
    bot = Bot(token=TG_BOT_TOKEN)
    
    # Group news by category
    news_by_category = {}
    for news in news_list:
        if news['category'] not in news_by_category:
            news_by_category[news['category']] = []
        news_by_category[news['category']].append(news)
    
    # Send news
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
                
                # Avoid rate limiting
                await asyncio.sleep(1.5)
            except Exception as e:
                logger.error(f"Error sending news: {e}", exc_info=True)

def setup_handlers(application):
    """Set up Telegram command handlers"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("translate", translate_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.COMMAND, handle_message))
