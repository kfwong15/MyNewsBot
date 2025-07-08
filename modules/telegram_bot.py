# 修改 send_telegram_message 函数
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
                    global TG_CHAT_ID
                    TG_CHAT_ID = new_chat_id
                    
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
