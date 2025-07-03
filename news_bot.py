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

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

# ✅ 抓取中国报头条新闻
def fetch_chinapress():
    try:
        url = "https://m.chinapress.com.my/"  # 使用移动版
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 查找头条新闻
        headline = soup.find('div', class_='headline')
        if headline:
            title_tag = headline.find('h1')
            if title_tag and title_tag.a:
                title = clean_text(title_tag.get_text(strip=True))
                link = title_tag.a['href']
                if not link.startswith('http'):
                    link = f"https://m.chinapress.com.my{link}"
                news_items.append(f"📰 <b>中国报头条</b>\n📌 {title}\n🔗 {link}")
        
        # 如果没有找到头条，则尝试备用选择器
        if not news_items:
            for article in soup.select('div.article')[:3]:
                title_tag = article.find('h2')
                if title_tag and title_tag.a:
                    title = clean_text(title_tag.get_text(strip=True))
                    link = title_tag.a['href']
                    if not link.startswith('http'):
                        link = f"https://m.chinapress.com.my{link}"
                    news_items.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
        
        return news_items[:3]  # 最多3条
    
    except Exception as e:
        print(f"❌ 中国报抓取失败: {str(e)}")
        return []

# ✅ 抓取东方日报头条新闻
def fetch_oriental():
    try:
        url = "https://m.orientaldaily.com.my"  # 使用移动版
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 查找头条新闻
        headline = soup.find('div', class_='headline')
        if headline:
            title_tag = headline.find('h1')
            if title_tag and title_tag.a:
                title = clean_text(title_tag.get_text(strip=True))
                link = title_tag.a['href']
                if not link.startswith('http'):
                    link = f"https://m.orientaldaily.com.my{link}"
                news_items.append(f"📰 <b>东方日报头条</b>\n📌 {title}\n🔗 {link}")
        
        # 如果没有找到头条，则尝试备用选择器
        if not news_items:
            for article in soup.select('div.news-item')[:3]:
                title_tag = article.find('h2')
                if title_tag and title_tag.a:
                    title = clean_text(title_tag.get_text(strip=True))
                    link = title_tag.a['href']
                    if not link.startswith('http'):
                        link = f"https://m.orientaldaily.com.my{link}"
                    news_items.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")
        
        return news_items[:3]  # 最多3条
    
    except Exception as e:
        print(f"❌ 东方日报抓取失败: {str(e)}")
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
    
    # 获取所有新闻
    all_news = []
    all_news.extend(fetch_chinapress())
    all_news.extend(fetch_oriental())
    
    # 如果没有新闻，添加默认消息
    if not all_news:
        all_news = ["📢 今日新闻抓取失败，请稍后重试"]
    
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
