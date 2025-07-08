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
    # 声明全局变量
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
                # 尝试从错误信息中提取新群组ID
                error_str = str(e)
                start_idx = error_str.find("New chat id: ") + len("New chat id: ")
                end_idx = error_str.find("\n", start_idx) if "\n" in error_str else len(error_str)
                new_chat_id = error_str[start_idx:end_idx].strip()
                
                if new_chat_id:
                    logger.error(f"检测到群组迁移，新群组ID: {new_chat_id}")
                    # 更新环境变量（仅限当前进程）
                    os.environ['TG_CHAT_ID'] = new_chat_id
                    TG_CHAT_ID = new_chat_id  # 更新全局变量
                    
                    # 重试发送
                    await bot.send_message(
                        chat_id=new_chat_id,
                        text=message,
                        parse_mode=parse_mode
                    )
                    return True
            except Exception as inner_e:
                logger.error(f"处理群组迁移失败: {inner_e}", exc_info=True)
        
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令 - 触发新闻抓取工作流"""
    user = update.effective_user
    await update.message.reply_html(
        rf"你好 {user.mention_html()}！我是DeepSeek新闻助手 🤖\n正在触发新闻抓取...",
    )
    
    # 通过 GitHub API 触发工作流
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
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
        logger.exception("触发GitHub工作流失败")

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /ask 命令 - 向DeepSeek AI提问"""
    if not context.args:
        await update.message.reply_text("请提供问题，例如：/ask 马来西亚今天有什么重要新闻？")
        return
    
    question = " ".join(context.args)
    await update.message.reply_text("🤖 DeepSeek AI 正在思考...")
    
    try:
        answer = ai_assistant.ask_ai(question)
        # 分片发送长消息（Telegram消息长度限制）
        for i in range(0, len(answer), 4096):
            await update.message.reply_text(answer[i:i+4096])
    except Exception as e:
        logger.exception("处理AI请求时出错")
        await update.message.reply_text("⚠️ 处理您的请求时出错，请稍后再试")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /summary 命令 - 总结URL内容"""
    if not context.args:
        await update.message.reply_text("请提供URL，例如：/summary https://www.thestar.com.my/news/article")
        return
    
    url = context.args[0]
    await update.message.reply_text("📝 DeepSeek AI 正在生成摘要...")
    
    try:
        summary = ai_assistant.summarize_webpage(url)
        await update.message.reply_text(summary)
    except Exception as e:
        logger.exception("总结文章时出错")
        await update.message.reply_text("⚠️ 生成摘要时出错，请稍后再试")

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /translate 命令 - 翻译文本"""
    if not context.args:
        await update.message.reply_text("请提供要翻译的文本，例如：/translate Good morning")
        return
    
    text = " ".join(context.args)
    await update.message.reply_text("🌐 DeepSeek AI 正在翻译...")
    
    try:
        translation = ai_assistant.translate_text(text)
        await update.message.reply_text(translation)
    except Exception as e:
        logger.exception("翻译时出错")
        await update.message.reply_text("⚠️ 翻译时出错，请稍后再试")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令 - 显示帮助"""
    help_text = """
🤖 DeepSeek 新闻助手使用指南：

/start - 手动触发新闻抓取（马来西亚TheStar新闻）
/ask <问题> - 向DeepSeek AI提问
/summary <URL> - 生成文章摘要
/translate <文本> - 翻译文本
/help - 显示帮助信息

示例：
/ask 马来西亚经济现状如何？
/summary https://www.thestar.com.my/news/article123
/translate Good morning
"""
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理无效命令"""
    await update.message.reply_text("⚠️ 无法识别的命令，使用 /help 查看可用指令")

async def send_news_to_telegram(news_list):
    """将新闻推送到Telegram"""
    # 声明全局变量
    global TG_CHAT_ID
    
    if not news_list:
        logger.warning("没有新闻需要发送")
        return 0
    
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        logger.error("TG_BOT_TOKEN 或 TG_CHAT_ID 未设置，跳过新闻推送")
        return 0
    
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
                    logger.info(f"准备发送新闻: {news['title'][:50]}...")
                    
                    # 检查图片URL是否有效
                    img_url_valid = False
                    if news.get('img_url'):
                        try:
                            # 简单检查图片URL格式
                            if news['img_url'].startswith('http'):
                                # 快速HEAD请求检查
                                response = requests.head(news['img_url'], timeout=5)
                                if response.status_code == 200:
                                    img_url_valid = True
                                    logger.debug(f"图片URL有效: {news['img_url']}")
                                else:
                                    logger.warning(f"图片URL无效 (状态码 {response.status_code}): {news['img_url']}")
                            else:
                                logger.warning(f"图片URL格式无效: {news['img_url']}")
                        except Exception as img_e:
                            logger.warning(f"图片URL验证失败: {img_e}")
                    
                    if img_url_valid:
                        logger.info(f"发送带图片的新闻: {news['title'][:50]}...")
                        await bot.send_photo(
                            chat_id=TG_CHAT_ID,
                            photo=news['img_url'],
                            caption=message,
                            parse_mode='Markdown'
                        )
                    else:
                        logger.info(f"发送纯文本新闻: {news['title'][:50]}...")
                        await bot.send_message(
                            chat_id=TG_CHAT_ID,
                            text=message,
                            parse_mode='Markdown'
                        )
                    
                    sent_count += 1
                    # 增加发送间隔避免限制
                    await asyncio.sleep(3)
                except Exception as e:
                    logger.error(f"发送新闻失败: {e}", exc_info=True)
                    # 尝试发送纯文本作为后备
                    try:
                        logger.info("尝试发送纯文本作为后备")
                        simple_message = f"*{news['title']}*\n{news['link']}"
                        await bot.send_message(
                            chat_id=TG_CHAT_ID,
                            text=simple_message,
                            parse_mode='Markdown'
                        )
                        sent_count += 1
                    except Exception as fallback_e:
                        logger.error(f"后备发送也失败: {fallback_e}")
        
        logger.info(f"成功发送 {sent_count}/{len(news_list)} 条新闻")
        return sent_count
    except Exception as e:
        logger.error(f"新闻推送失败: {e}", exc_info=True)
        return 0

def setup_handlers(application):
    """设置Telegram命令处理器"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("translate", translate_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.COMMAND, handle_message))
    logger.info("Telegram 命令处理器设置完成")
