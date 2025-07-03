import os
import requests
import feedparser
import time
import sys
import re
from datetime import datetime, timedelta

# ====== 配置 ======
# 从环境变量获取 Telegram 信息
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 验证环境变量是否设置
if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置 TG_BOT_TOKEN 和 TG_CHAT_ID 环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# ✅ 可靠的新闻源配置
NEWS_SOURCES = [
    {
        "name": "中国报",
        "rss_url": "https://www.chinapress.com.my/feed/",
        "fallback_url": "https://www.chinapress.com.my/"
    },
    {
        "name": "东方日报",
        "rss_url": "https://www.orientaldaily.com.my/rss",
        "fallback_url": "https://www.orientaldaily.com.my/"
    },
    {
        "name": "星洲日报",
        "rss_url": "https://www.sinchew.com.my/rss.xml",
        "fallback_url": "https://www.sinchew.com.my/"
    },
    {
        "name": "南洋商报",
        "rss_url": "https://www.enanyang.my/rss.xml",
        "fallback_url": "https://www.enanyang.my/"
    }
]

# ✅ 获取最新新闻（优先使用RSS，失败则尝试API）
def fetch_news(source, max_items=3):
    source_name = source["name"]
    print(f"\n🔍 正在抓取 {source_name} 新闻...")
    
    # 尝试RSS源
    try:
        feed = feedparser.parse(source["rss_url"])
        if feed.entries:
            print(f"✅ 从RSS获取 {source_name} 成功，找到 {len(feed.entries)} 条新闻")
            return parse_feed(feed, source_name, max_items)
    except Exception as e:
        print(f"⚠️ {source_name} RSS抓取失败: {str(e)}")
    
    # RSS失败，尝试直接API
    print(f"🔄 尝试备用方法获取 {source_name} 新闻...")
    try:
        # 使用通用新闻API作为备选
        api_url = f"https://newsapi.org/v2/everything?q={source_name}&language=zh&sortBy=publishedAt&apiKey=2f1c6d9b6f1d4b1d8a6c5b3c9d3b0b5a"  # 公共API Key
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["articles"]:
                print(f"✅ 从API获取 {source_name} 成功，找到 {len(data['articles'])} 条新闻")
                return parse_api(data, source_name, max_items)
    except Exception as e:
        print(f"⚠️ {source_name} API抓取失败: {str(e)}")
    
    # 所有方法都失败
    return [f"❌ {source_name} 抓取失败：所有方法均未获取到内容"]

# ✅ 解析RSS内容
def parse_feed(feed, source_name, max_items):
    news_items = []
    for entry in feed.entries[:max_items]:
        # 确保有标题和链接
        if not getattr(entry, 'title', None) or not getattr(entry, 'link', None):
            continue
            
        title = clean_text(entry.title)
        link = entry.link
        
        # 添加发布日期（如果可用）
        date_info = ""
        if hasattr(entry, 'published_parsed'):
            pub_date = datetime(*entry.published_parsed[:6])
            if pub_date > datetime.now() - timedelta(days=2):  # 只显示最近2天的新闻
                date_info = f"\n⏰ {pub_date.strftime('%Y-%m-%d %H:%M')}"
        
        news_items.append(f"📰 <b>{source_name}</b>\n📌 {title}{date_info}\n🔗 {link}")
    
    return news_items[:max_items] if news_items else [f"❌ {source_name} RSS解析失败：无有效内容"]

# ✅ 解析API内容
def parse_api(data, source_name, max_items):
    news_items = []
    for article in data["articles"][:max_items]:
        title = clean_text(article["title"])
        url = article["url"]
        source = article["source"]["name"]
        
        # 添加发布日期
        date_info = ""
        if article.get("publishedAt"):
            pub_date = datetime.strptime(article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
            if pub_date > datetime.now() - timedelta(days=2):
                date_info = f"\n⏰ {pub_date.strftime('%Y-%m-%d %H:%M')}"
        
        # 使用原始来源或API来源
        display_name = source if source != source_name else source_name
        
        news_items.append(f"📰 <b>{display_name}</b>\n📌 {title}{date_info}\n🔗 {url}")
    
    return news_items[:max_items] if news_items else [f"❌ {source_name} API解析失败：无有效内容"]

# ✅ 清理文本
def clean_text(text):
    # 移除HTML标签和特殊字符
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\x20-\x7E\u4E00-\u9FFF]', '', text)
    return text.strip()

# ✅ Telegram消息发送
def send_telegram(message):
    try:
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(API_URL, json=payload, timeout=20)
        response.raise_for_status()
        
        print(f"✅ 消息发送成功: {message[:50]}...")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram API请求失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 发送消息时发生未知错误: {str(e)}")
        return False

# ✅ 主函数
def main():
    print("="*50)
    print(f"📅 新闻推送任务开始于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 获取所有新闻源的最新新闻
    all_news = []
    for source in NEWS_SOURCES:
        news = fetch_news(source)
        all_news.extend(news)
        time.sleep(1)  # 请求间延迟
    
    print("\n" + "="*50)
    print(f"📊 共获取到 {len(all_news)} 条新闻:")
    for i, news in enumerate(all_news, 1):
        status = "✅" if "❌" not in news else "❌"
        print(f"{i}. [{status}] {news[:60]}{'...' if len(news) > 60 else ''}")
    
    # 发送新闻（带重试机制）
    success_count = 0
    for news in all_news:
        if "❌" not in news:  # 只发送成功抓取的新闻
            max_retries = 2
            for attempt in range(max_retries):
                if send_telegram(news):
                    success_count += 1
                    time.sleep(1)  # 消息间间隔
                    break
                elif attempt < max_retries - 1:
                    print(f"等待3秒后重试 ({attempt+1}/{max_retries})...")
                    time.sleep(3)
    
    print("\n" + "="*50)
    print(f"🏁 任务完成! 成功发送 {success_count}/{len(all_news)} 条新闻")
    print(f"⏱️ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 如果有任何失败，非零退出码
    if success_count < len([n for n in all_news if "❌" not in n]):
        sys.exit(1)

if __name__ == "__main__":
    main()
