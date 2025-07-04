import os
import requests
import time
import sys
import random
from bs4 import BeautifulSoup
from datetime import datetime

# ====== 配置 ======
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置TG_BOT_TOKEN和TG_CHAT_ID环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# Google新闻马来西亚版URL
GOOGLE_NEWS_URL = "https://news.google.com/home?hl=en-MY&gl=MY&ceid=MY:en"

# 多个新闻分类URL
NEWS_CATEGORIES = [
    "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB?hl=en-MY&gl=MY&ceid=MY%3Aen",  # 头条
    "https://news.google.com/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFp4WkRNU0FtVnVLQUFQAQ?hl=en-MY&gl=MY&ceid=MY%3Aen",  # 马来西亚
    "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-MY&gl=MY&ceid=MY%3Aen",  # 世界
    "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-MY&gl=MY&ceid=MY%3Aen",  # 商业
    "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-MY&gl=MY&ceid=MY%3Aen",  # 科技
    "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-MY&gl=MY&ceid=MY%3Aen",  # 娱乐
    "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-MY&gl=MY&ceid=MY%3Aen"   # 体育
]

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

def fetch_google_news(max_news=50):
    all_news = []
    seen_links = set()  # 用于去重
    
    print(f"🔍 开始抓取Google马来西亚新闻，目标数量: {max_news}")
    
    # 随机打乱分类顺序，避免模式化访问
    random.shuffle(NEWS_CATEGORIES)
    
    for category_url in NEWS_CATEGORIES:
        if len(all_news) >= max_news:
            break
            
        try:
            print(f"⏳ 抓取分类: {category_url.split('/')[-1].split('?')[0]}")
            response = requests.get(category_url, headers=get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('article.IBr9hb')
            
            for article in articles:
                if len(all_news) >= max_news:
                    break
                    
                title_tag = article.select_one('h4')
                source_tag = article.select_one('.vr1PYe')
                time_tag = article.select_one('time')
                link = article.find('a')['href']
                
                if not title_tag or not link:
                    continue
                
                # 补全链接
                if link.startswith('./'):
                    full_link = f"https://news.google.com{link[1:]}"
                else:
                    full_link = link
                
                # 去重检查
                if full_link in seen_links:
                    continue
                seen_links.add(full_link)
                
                title = title_tag.get_text(strip=True)
                source = source_tag.get_text(strip=True) if source_tag else "未知来源"
                time_text = time_tag['datetime'] if time_tag else ""
                
                news_item = f"📰 <b>{title}</b>\n" \
                           f"🏷️ 来源: {source}\n" \
                           f"⏰ 时间: {time_text}\n" \
                           f"🔗 {full_link}"
                all_news.append(news_item)
                
                # 添加随机延迟
                time.sleep(random.uniform(0.1, 0.3))
            
            # 分类间延迟
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"⚠️ 分类抓取失败: {str(e)}")
    
    return all_news[:max_news]

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
    print(f"📅 Google马来西亚新闻推送任务开始 {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 获取30-50条新闻
    target_count = random.randint(30, 50)
    news_items = fetch_google_news(target_count)
    
    if not news_items:
        print("❌ 未找到任何新闻，发送通知")
        news_items = ["📢 今日未能获取马来西亚新闻，请稍后重试"]
    
    print(f"\n📊 共找到 {len(news_items)} 条新闻，准备发送...")
    
    success_count = 0
    for index, news in enumerate(news_items, 1):
        if send_telegram(news):
            success_count += 1
            print(f"✅ 已发送 {index}/{len(news_items)}")
            
            # 随机延迟，避免发送过快
            delay = random.uniform(0.5, 2.0)
            time.sleep(delay)
    
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
             f"✅ 成功发送: {success_count}\n" \
             f"🔁 下次运行: 5小时后"
    
    send_telegram(report)
    
    if success_count < len(news_items):
        sys.exit(1)

if __name__ == "__main__":
    main()
