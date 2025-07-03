import os
import requests
from bs4 import BeautifulSoup
import time
import re
import sys

# ====== 配置 ======
# 从环境变量获取 Telegram 信息
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 验证环境变量是否设置
if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置 TG_BOT_TOKEN 和 TG_CHAT_ID 环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# 通用请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}

# ✅ 中国报新闻抓取
def fetch_chinapress():
    try:
        url = "https://www.chinapress.com.my/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 查找头条新闻
        top_news = soup.select_one('div.top-story')
        if top_news:
            title_tag = top_news.find('h1', class_='post-title')
            if title_tag and title_tag.a:
                title = title_tag.get_text(strip=True)
                link = title_tag.a['href']
                news_items.append(f"📰 <b>中国报头条</b>\n📌 {title}\n🔗 {link}")
        
        # 查找其他新闻（最多2条）
        for article in soup.select('div.post-box:not(.top-story)')[:2]:
            title_tag = article.find('h3', class_='post-title')
            if title_tag and title_tag.a:
                title = title_tag.get_text(strip=True)
                link = title_tag.a['href']
                news_items.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
                
        return news_items if news_items else ["❌ 中国报抓取失败：未找到新闻内容"]
        
    except Exception as e:
        return [f"❌ 中国报抓取失败：{str(e)}"]

# ✅ 东方日报新闻抓取
def fetch_oriental():
    try:
        url = "https://www.orientaldaily.com.my"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 查找头条新闻
        top_news = soup.select_one('div.top-news')
        if top_news:
            title_tag = top_news.find('h1')
            if title_tag and title_tag.a:
                title = title_tag.get_text(strip=True)
                link = title_tag.a['href']
                if not link.startswith('http'):
                    link = f"https://www.orientaldaily.com.my{link}"
                news_items.append(f"📰 <b>东方日报头条</b>\n📌 {title}\n🔗 {link}")
        
        # 查找其他新闻（最多2条）
        for article in soup.select('div.news-list')[:2]:
            title_tag = article.find('h2')
            if title_tag and title_tag.a:
                title = title_tag.get_text(strip=True)
                link = title_tag.a['href']
                if not link.startswith('http'):
                    link = f"https://www.orientaldaily.com.my{link}"
                news_items.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")
                
        return news_items if news_items else ["❌ 东方日报抓取失败：未找到新闻内容"]
        
    except Exception as e:
        return [f"❌ 东方日报抓取失败：{str(e)}"]

# ✅ Telegram消息发送
def send_telegram(message):
    try:
        # 清理消息中的无效字符
        clean_msg = re.sub(r'[\x00-\x1F\x7F]', '', message)
        
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": clean_msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(API_URL, json=payload, timeout=20)
        response.raise_for_status()
        
        print(f"✅ 消息发送成功: {clean_msg[:50]}...")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram API请求失败: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"HTTP状态码: {e.response.status_code}")
            # 不打印完整响应，避免泄露敏感信息
        return False
    except Exception as e:
        print(f"❌ 发送消息时发生未知错误: {str(e)}")
        return False

# ✅ 主函数
def main():
    print("="*50)
    print("开始新闻推送任务")
    print("="*50)
    
    # 获取新闻
    all_news = []
    all_news.extend(fetch_chinapress())
    all_news.extend(fetch_oriental())
    
    print(f"\n共抓取到 {len(all_news)} 条新闻:")
    for i, news in enumerate(all_news, 1):
        print(f"{i}. {news[:60]}{'...' if len(news) > 60 else ''}")
    
    # 发送新闻（带重试机制）
    for news in all_news:
        if "❌" not in news:  # 只发送成功抓取的新闻
            max_retries = 3
            for attempt in range(max_retries):
                if send_telegram(news):
                    break
                elif attempt < max_retries - 1:
                    print(f"等待5秒后重试 ({attempt+1}/{max_retries})...")
                    time.sleep(5)
            time.sleep(2)  # 消息间间隔
    
    print("\n" + "="*50)
    print("新闻推送任务完成!")
    print("="*50)

if __name__ == "__main__":
    main()
