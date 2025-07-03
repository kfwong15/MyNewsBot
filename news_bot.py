import os
import requests
import feedparser
import time
import sys
import re
from datetime import datetime
import random

# ====== 配置 ======
# 从环境变量获取 Telegram 信息
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 验证环境变量是否设置
if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置 TG_BOT_TOKEN 和 TG_CHAT_ID 环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# 可靠的 RSS 新闻源配置
RSS_SOURCES = [
    {
        "name": "星洲日报",
        "url": "https://www.sinchew.com.my/rss.xml",
        "fallback": "https://www.sinchew.com.my"
    },
    {
        "name": "南洋商报",
        "url": "https://www.enanyang.my/rss.xml",
        "fallback": "https://www.enanyang.my"
    },
    {
        "name": "东方日报",
        "url": "https://www.orientaldaily.com.my/rss",
        "fallback": "https://www.orientaldaily.com.my"
    },
    {
        "name": "中国报",
        "url": "https://www.chinapress.com.my/feed/",
        "fallback": "https://www.chinapress.com.my"
    },
    {
        "name": "BBC 中文网",
        "url": "https://www.bbc.com/zhongwen/simp/index.xml"
    },
    {
        "name": "联合早报",
        "url": "https://www.zaobao.com.sg/realtime/singapore/feed"
    }
]

# 代理服务器列表
PROXIES = [
    "http://45.95.147.106:8080",
    "http://45.151.101.129:8080",
    "http://103.152.112.162:80",
    "http://45.8.105.7:80",
    "http://103.155.217.1:41317",
    "http://103.174.102.211:8080",
    "http://103.161.164.109:8181",
    "http://103.169.149.9:8080"
]

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

# ✅ 获取 RSS 内容（带代理和重试）
def fetch_rss(source, max_retries=3):
    name = source["name"]
    url = source["url"]
    
    for attempt in range(max_retries):
        try:
            # 随机选择代理
            proxy = {"http": random.choice(PROXIES)} if PROXIES else None
            
            # 设置超时
            timeout = 15 + attempt * 5  # 每次重试增加超时时间
            
            print(f"🔍 尝试 {attempt+1}/{max_retries}: 抓取 {name} RSS...")
            
            # 发送请求
            response = requests.get(
                url, 
                headers=HEADERS, 
                proxies=proxy, 
                timeout=timeout
            )
            
            if response.status_code == 200:
                print(f"✅ {name} RSS 抓取成功")
                return response.content
            
            print(f"⚠️ {name} 返回状态码: {response.status_code}")
            
        except Exception as e:
            print(f"⚠️ {name} 抓取失败: {str(e)}")
        
        # 重试前等待
        if attempt < max_retries - 1:
            wait_time = 3 + attempt * 2
            print(f"等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    print(f"❌ {name} RSS 抓取失败，所有尝试均失败")
    return None

# ✅ 解析 RSS 内容
def parse_rss(content, source_name):
    try:
        feed = feedparser.parse(content)
        news_items = []
        
        if not feed.entries:
            return [f"❌ {source_name} RSS 无新闻内容"]
        
        for entry in feed.entries[:3]:  # 最多3条
            # 确保有标题和链接
            title = getattr(entry, 'title', '无标题')
            link = getattr(entry, 'link', '')
            
            # 清理文本
            title = clean_text(title)
            
            # 添加发布日期
            date_info = ""
            if hasattr(entry, 'published_parsed'):
                pub_date = datetime(*entry.published_parsed[:6])
                date_info = f"\n⏰ {pub_date.strftime('%Y-%m-%d %H:%M')}"
            
            news_items.append(f"📰 <b>{source_name}</b>\n📌 {title}{date_info}\n🔗 {link}")
        
        return news_items
    
    except Exception as e:
        return [f"❌ {source_name} RSS 解析失败: {str(e)}"]

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
    for source in RSS_SOURCES:
        rss_content = fetch_rss(source)
        if rss_content:
            news = parse_rss(rss_content, source["name"])
            all_news.extend(news)
        else:
            all_news.append(f"❌ {source['name']} 抓取失败")
        
        time.sleep(1)  # 请求间延迟
    
    # 如果没有新闻，添加默认消息
    if not all_news or all(news.startswith("❌") for news in all_news):
        all_news = ["📢 今日新闻抓取遇到问题，请稍后重试或检查日志"]
    
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
