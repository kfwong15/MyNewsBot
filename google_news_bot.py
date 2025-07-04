import os
import requests
import time
import sys
import random
import json
from datetime import datetime
from bs4 import BeautifulSoup

# ====== 配置 ======
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置TG_BOT_TOKEN和TG_CHAT_ID环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# Google新闻API URL (更可靠的方法)
GOOGLE_NEWS_API_URL = "https://news.google.com/rss?hl=en-MY&gl=MY&ceid=MY:en"

# 直接解析替代方案
NEWS_SOURCES = {
    "MalaysiaKini": "https://www.malaysiakini.com/news",
    "The Star": "https://www.thestar.com.my/news",
    "New Straits Times": "https://www.nst.com.my/news",
    "Malay Mail": "https://www.malaymail.com/news/malaysia",
    "Free Malaysia Today": "https://www.freemalaysiatoday.com/category/nation/"
}

# 请求头列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.5",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }

def fetch_google_news_api(max_news=50):
    """使用Google RSS API获取新闻"""
    try:
        print("🔍 使用Google RSS API获取新闻...")
        response = requests.get(GOOGLE_NEWS_API_URL, headers=get_headers(), timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')  # 注意使用xml解析器
        items = soup.find_all('item')[:max_news]
        
        news_items = []
        for item in items:
            title = item.title.text if item.title else "无标题"
            link = item.link.text if item.link else "#"
            pub_date = item.pubDate.text if item.pubDate else ""
            source = item.source.text if item.source else "未知来源"
            
            news_item = f"📰 <b>{title}</b>\n" \
                       f"🏷️ 来源: {source}\n" \
                       f"⏰ 时间: {pub_date}\n" \
                       f"🔗 {link}"
            news_items.append(news_item)
        
        return news_items
    
    except Exception as e:
        print(f"❌ Google RSS API请求失败: {str(e)}")
        return []

def fetch_direct_news_sources(max_news=50):
    """直接抓取马来西亚新闻网站"""
    print("🔍 直接抓取马来西亚新闻网站...")
    all_news = []
    sources = list(NEWS_SOURCES.items())
    random.shuffle(sources)  # 随机打乱顺序
    
    for source_name, url in sources:
        if len(all_news) >= max_news:
            break
            
        try:
            print(f"⏳ 抓取 {source_name}...")
            response = requests.get(url, headers=get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            # 针对不同网站使用不同的选择器
            if source_name == "MalaysiaKini":
                articles = soup.select('h3.title')[:10]  # 取前10条
            elif source_name == "The Star":
                articles = soup.select('div.story-card a')[:10]
            elif source_name == "New Straits Times":
                articles = soup.select('h5.card-title a')[:10]
            elif source_name == "Malay Mail":
                articles = soup.select('h4.card-title a')[:10]
            elif source_name == "Free Malaysia Today":
                articles = soup.select('h3.entry-title a')[:10]
            
            for article in articles:
                if len(all_news) >= max_news:
                    break
                    
                title = article.get_text(strip=True)
                link = article.get('href', '')
                
                # 确保链接完整
                if link and not link.startswith('http'):
                    if source_name == "The Star":
                        link = f"https://www.thestar.com.my{link}"
                    elif source_name == "New Straits Times":
                        link = f"https://www.nst.com.my{link}"
                
                if title and link:
                    news_item = f"📰 <b>{title}</b>\n" \
                               f"🏷️ 来源: {source_name}\n" \
                               f"🔗 {link}"
                    all_news.append(news_item)
            
            time.sleep(random.uniform(1, 2))  # 网站间延迟
            
        except Exception as e:
            print(f"⚠️ {source_name} 抓取失败: {str(e)}")
    
    return all_news

def fetch_news(max_news=50):
    """主抓取函数，尝试多种方法"""
    print(f"🎯 目标抓取 {max_news} 条新闻")
    
    # 首先尝试Google RSS API
    news_items = fetch_google_news_api(max_news)
    
    # 如果API方法失败或数量不足，使用直接抓取
    if len(news_items) < max_news:
        needed = max_news - len(news_items)
        direct_news = fetch_direct_news_sources(needed)
        news_items.extend(direct_news)
    
    # 如果仍然没有足够新闻，添加备用新闻
    if not news_items:
        print("⚠️ 所有方法均失败，使用备用新闻")
        news_items = [
            "📢 今日新闻抓取遇到问题，请稍后重试",
            "📰 <b>马来西亚最新新闻</b>\n🏷️ 来源: 系统通知\n🔗 https://www.thestar.com.my",
            "📰 <b>查看马来西亚新闻</b>\n🏷️ 来源: 系统通知\n🔗 https://www.nst.com.my"
        ]
    
    return news_items[:max_news]

def send_telegram(message):
    try:
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        
        response = requests.post(API_URL, json=payload, timeout=25)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ 发送失败: {str(e)}")
        return False

def main():
    print("="*50)
    start_time = datetime.now()
    print(f"📅 马来西亚新闻推送任务开始 {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 获取30-50条新闻
    target_count = random.randint(30, 50)
    news_items = fetch_news(target_count)
    
    print(f"\n📊 共找到 {len(news_items)} 条新闻，准备发送...")
    
    success_count = 0
    for index, news in enumerate(news_items, 1):
        if send_telegram(news):
            success_count += 1
            print(f"✅ 已发送 {index}/{len(news_items)}")
            
            # 随机延迟，避免发送过快
            delay = random.uniform(0.5, 2.0)
            time.sleep(delay)
        else:
            print(f"⚠️ 发送失败 {index}/{len(news_items)}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print(f"🏁 任务完成! 成功发送 {success_count}/{len(news_items)} 条新闻")
    print(f"⏱️ 总耗时: {duration.total_seconds():.1f}秒")
    print("="*50)
    
    # 生成报告消息
    report = f"📊 新闻推送报告\n" \
             f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n" \
             f"⏰ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n" \
             f"⏱️ 总耗时: {duration.total_seconds():.1f}秒\n" \
             f"📰 目标数量: {target_count}\n" \
             f"✅ 成功发送: {success_count}"
    
    send_telegram(report)
    
    if success_count < len(news_items):
        sys.exit(1)

if __name__ == "__main__":
    main()
