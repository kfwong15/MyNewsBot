import argparse
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from modules.news_crawler import fetch_chinapress_news, select_random_news
from modules.telegram_bot import send_telegram_message, send_news_to_telegram


async def run(dry_run: bool, count: int):
    start = datetime.now()
    news = fetch_chinapress_news(max_items=max(count, 10))
    if not news:
        await send_telegram_message("❌ 抓取失败，未获取到中国报新闻")
        return

    debug = f"🔍 中国报抓取到 {len(news)} 条新闻：\n"
    for i, n in enumerate(news[:count], 1):
        debug += f"{i}. {n['title']}\n{n['link']}\n\n"

    # 发送抓取报告
    await send_telegram_message(debug)

    selected = select_random_news(news, count)
    if dry_run:
        # 仅打印，不推送
        for i, n in enumerate(selected, 1):
            print(f"{i}. {n['title']}\n{n['link']}\n")
        return

    sent = await send_news_to_telegram(selected)
    dur = (datetime.now() - start).total_seconds()
    summary = (
        f"📰 中国报推送报告\n"
        f"• 抓取: {len(news)} 条\n"
        f"• 推送: {sent} 条\n"
        f"• 耗时: {dur:.1f} 秒"
    )
    await send_telegram_message(summary)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="抓取中国报并发送到 Telegram")
    parser.add_argument("--count", type=int, default=10, help="推送条数（默认10）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不发送")
    args = parser.parse_args()

    asyncio.run(run(args.dry_run, args.count))


if __name__ == "__main__":
    main()