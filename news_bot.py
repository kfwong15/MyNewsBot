import os
import requests
import time
import sys
import re
from datetime import datetime
from bs4 import BeautifulSoup

# ====== 配置 ======
# 从环境变量获取 Telegram 信息
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 验证环境变量是否设置
if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置 TG_BOT_TOKEN 和 TG_CHAT_ID 环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# 可靠的新闻源配置
NEWS_SOURCES = [
    # 使用通用新闻API
    {
        "name": "全球头条新闻",
        "api_url": "https://newsapi.org/v2/top-headlines",
        "params": {
            "country": "my",
            "language": "zh",
            "pageSize": 5,
            "apiKey": "2f1c6d9b6f1d4b1d8a6c5b3c9d3b0b5a"  # 公共API Key
        }
    },
    # 直接解析星洲日报
    {
        "name": "星洲日报",
        "type": "scrape",
        "url": "https://www.sinchew.com.my"
    },
    # 直接解析南洋商报
    {
        "name": "南洋商报",
        "type": "scrape",
        "url": "https://www.enanyang.my"
    }
]

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

# ✅ 获取API新闻
def fetch_api_news(source):
    try:
        print(f"🔍 正在从API获取 {source['name']} 新闻...")
        response = requests.get(
            source["api_url"], 
            params=source["params"], 
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("articles"):
                return parse_api_news(data, source["name"])
        
        print(f"⚠️ {source['name']} API返回状态码: {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ {source['name']} API抓取失败: {str(e)}")
        return []

# ✅ 解析API新闻
def parse_api_news(data, source_name):
    news_items = []
    for article in data["articles"][:3]:  # 最多3条
        title = clean_text(article["title"])
        url = article["url"]
        source = article["source"]["name"]
        
        # 添加发布日期
        date_info = ""
        if article.get("publishedAt"):
            try:
                pub_date = datetime.strptime(article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
                date_info = f"\n⏰ {pub_date.strftime('%Y-%m-%d %H:%M')}"
            except:
                pass
        
        # 使用原始来源或API来源
        display_name = source if source != source_name else source_name
        
        news_items.append(f"📰 <b>{display_name}</b>\n📌 {title}{date_info}\n🔗 {url}")
    
    return news_items

# ✅ 抓取直接网站新闻
def scrape_website(source):
    try:
        print(f"🔍 正在抓取 {source['name']} 网站...")
        response = requests.get(source["url"], headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 星洲日报解析
        if "sinchew" in source["url"]:
            # 查找头条新闻
            headline = soup.select_one('div.headline-news')
            if headline:
                title_tag = headline.find('h1')
                if title_tag and title_tag.a:
                    title = clean_text(title_tag.get_text(strip=True))
                    link = title_tag.a['href']
                    if not link.startswith('http'):
                        link = f"https://www.sinchew.com.my{link}"
                    news_items.append(f"📰 <b>{source['name']}头条</b>\n📌 {title}\n🔗 {link}")
            
            # 查找其他新闻
            for article in soup.select('div.news-list')[:2]:
                title_tag = article.find('h2')
                if title_tag and title_tag.a:
                    title = clean_text(title_tag.get_text(strip=True))
                    link = title_tag.a['href']
                    if not link.startswith('http'):
                        link = f"https://www.sinchew.com.my{link}"
                    news_items.append(f"📰 <b>{source['name']}</b>\n📌 {title}\n🔗 {link}")
        
        # 南洋商报解析
        elif "enanyang" in source["url"]:
            # 查找头条新闻
            top_news = soup.select_one('div.top-news')
            if top_news:
                title_tag = top_news.find('h1')
                if title_tag and title_tag.a:
                    title = clean_text(title_tag.get_text(strip=True))
                    link = title_tag.a['href']
                    if not link.startswith('http'):
                        link = f"https://www.enanyang.my{link}"
                    news_items.append(f"📰 <b>{source['name']}头条</b>\n📌 {title}\n🔗 {link}")
            
            # 查找其他新闻
            for article in soup.select('div.news-box')[:2]:
                title_tag = article.find('h2')
                if title_tag and title_tag.a:
                    title = clean_text(title_tag.get_text(strip=True))
                    link = title_tag.a['href']
                    if not link.startswith('http'):
                        link = f"https://www.enanyang.my{link}"
                    news_items.append(f"📰 <b>{source['name']}</b>\n📌 {title}\n🔗 {link}")
        
        return news_items[:3] if news_items else []
        
    except Exception as e:
        print(f"❌ {source['name']} 网站抓取失败: {str(e)}")
        return []

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
    start_time = datetime.now()
    print(f"📅 新闻推送任务开始于 {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 获取所有新闻源的最新新闻
    all_news = []
    for source in NEWS_SOURCES:
        if "api_url" in source:
            news = fetch_api_news(source)
        elif "type" in source and source["type"] == "scrape":
            news = scrape_website(source)
        else:
            continue
            
        all_news.extend(news)
        time.sleep(1)  # 请求间延迟
    
    # 如果没有新闻，添加默认消息
    if not all_news:
        all_news = ["📢 今日暂无新闻更新，请稍后再试"]
    
    print("\n" + "="*50)
    print(f"📊 共获取到 {len(all_news)} 条新闻:")
    for i, news in enumerate(all_news, 1):
        print(f"{i}. {news[:60]}{'...' if len(news) > 60 else ''}")
    
    # 发送新闻
    success_count = 0
    for news in all_news:
        max_retries = 2
        for attempt in range(max_retries):
            if send_telegram(news):
                success_count += 1
                time.sleep(1)  # 消息间间隔
                break
            elif attempt < max_retries - 1:
                print(f"等待3秒后重试 ({attempt+1}/{max_retries})...")
                time.sleep(3)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print(f"🏁 任务完成! 成功发送 {success_count}/{len(all_news)} 条新闻")
    print(f"⏱️ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 总耗时: {duration.total_seconds():.1f}秒")
    print("="*50)
    
    # 如果有任何失败，非零退出码
    if success_count < len(all_news):
        sys.exit(1)

if __name__ == "__main__":
    main()
