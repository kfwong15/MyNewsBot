import os
import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import random
from fake_useragent import UserAgent

# ====== 配置 ======
# 从环境变量获取 Telegram 信息
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 验证环境变量是否设置
if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置 TG_BOT_TOKEN 和 TG_CHAT_ID 环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# 创建随机User-Agent生成器
ua = UserAgent()

# 获取随机代理列表（免费公共代理）
PROXY_LIST = [
    "http://45.95.147.106:8080",
    "http://45.151.101.129:8080",
    "http://103.152.112.162:80",
    "http://45.8.105.7:80",
    "http://103.155.217.1:41317",
    "http://103.174.102.211:8080",
    "http://103.161.164.109:8181",
    "http://103.169.149.9:8080"
]

# ✅ 改进的网站请求函数（带代理和重试）
def fetch_url(url, retries=3):
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
        "DNT": "1"
    }
    
    for attempt in range(retries):
        try:
            # 随机选择代理
            proxy = {"http": random.choice(PROXY_LIST)} if PROXY_LIST else None
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=15,
                proxies=proxy
            )
            
            # 检查状态码
            if response.status_code == 200:
                return response
            
            # 如果是403错误，更换User-Agent和代理重试
            print(f"⚠️ 尝试 {attempt+1}/{retries}: 状态码 {response.status_code}, 更换代理重试...")
            time.sleep(random.uniform(2, 5))  # 随机延迟
            
        except Exception as e:
            print(f"⚠️ 尝试 {attempt+1}/{retries} 失败: {str(e)}")
            time.sleep(random.uniform(3, 7))
    
    return None

# ✅ 中国报新闻抓取（带Cloudflare绕过）
def fetch_chinapress():
    try:
        url = "https://www.chinapress.com.my/"
        response = fetch_url(url)
        
        if not response:
            return ["❌ 中国报抓取失败：无法获取网页内容"]
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 尝试多种选择器策略
        selectors = [
            'div.top-story',  # 主要选择器
            'article.post-item',  # 备选选择器
            'div.post-box'  # 另一个备选
        ]
        
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                for article in articles[:3]:
                    # 尝试多种标题定位方式
                    title_tags = [
                        article.find('h1', class_='post-title'),
                        article.find('h2', class_='post-title'),
                        article.find('h3', class_='post-title'),
                        article.find('h1'),
                        article.find('h2'),
                        article.find('h3')
                    ]
                    
                    for title_tag in title_tags:
                        if title_tag and title_tag.a:
                            title = title_tag.get_text(strip=True)
                            link = title_tag.a.get('href', '')
                            
                            if link and not link.startswith('http'):
                                link = f"https://www.chinapress.com.my{link}"
                            
                            if title and link:
                                news_items.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
                                break
                
                if news_items:  # 如果找到新闻就停止尝试其他选择器
                    break
        
        return news_items[:3] if news_items else ["❌ 中国报抓取失败：未找到新闻内容"]
        
    except Exception as e:
        return [f"❌ 中国报抓取失败：{str(e)}"]

# ✅ 东方日报新闻抓取（带备用方案）
def fetch_oriental():
    try:
        # 尝试主网站
        url = "https://www.orientaldaily.com.my"
        response = fetch_url(url)
        
        if not response:
            # 尝试备用RSS源
            rss_url = "https://www.orientaldaily.com.my/rss"
            rss_response = fetch_url(rss_url)
            
            if rss_response and rss_response.status_code == 200:
                return parse_rss(rss_response.text, "东方日报")
            else:
                return ["❌ 东方日报抓取失败：无法获取网页内容"]
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 尝试多种选择器策略
        selectors = [
            'div.top-news',  # 主要选择器
            'div.news-list',  # 备选选择器
            'div.headline-news'  # 另一个备选
        ]
        
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                for article in articles[:2]:
                    # 尝试多种标题定位方式
                    title_tags = [
                        article.find('h1'),
                        article.find('h2'),
                        article.find('h3'),
                        article.find(class_='title'),
                        article.find(class_='headline')
                    ]
                    
                    for title_tag in title_tags:
                        if title_tag and title_tag.a:
                            title = title_tag.get_text(strip=True)
                            link = title_tag.a.get('href', '')
                            
                            if link and not link.startswith('http'):
                                link = f"https://www.orientaldaily.com.my{link}"
                            
                            if title and link:
                                news_items.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")
                                break
                
                if news_items:  # 如果找到新闻就停止尝试其他选择器
                    break
        
        return news_items[:2] if news_items else ["❌ 东方日报抓取失败：未找到新闻内容"]
        
    except Exception as e:
        return [f"❌ 东方日报抓取失败：{str(e)}"]

# ✅ RSS解析备用方案
def parse_rss(xml_content, source_name):
    try:
        from xml.etree import ElementTree as ET
        
        root = ET.fromstring(xml_content)
        news_items = []
        
        # 解析RSS/XML
        for item in root.findall('.//item')[:3]:
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            
            if title and link:
                news_items.append(f"📰 <b>{source_name}</b>\n📌 {title}\n🔗 {link}")
        
        return news_items if news_items else [f"❌ {source_name} RSS解析失败：无有效内容"]
    
    except Exception as e:
        return [f"❌ {source_name} RSS解析失败：{str(e)}"]

# ✅ Telegram消息发送（带HTML清理）
def send_telegram(message):
    try:
        # 清理消息中的无效字符
        clean_msg = re.sub(r'[^\x20-\x7E\u4E00-\u9FFF]', '', message)
        
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": clean_msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(API_URL, json=payload, timeout=25)
        response.raise_for_status()
        
        print(f"✅ 消息发送成功: {clean_msg[:50]}...")
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
    print("开始新闻推送任务")
    print("="*50)
    
    # 获取新闻
    print("\n抓取中国报新闻...")
    chinapress_news = fetch_chinapress()
    print(f"找到 {len([n for n in chinapress_news if '❌' not in n])} 条中国报新闻")
    
    print("\n抓取东方日报新闻...")
    oriental_news = fetch_oriental()
    print(f"找到 {len([n for n in oriental_news if '❌' not in n])} 条东方日报新闻")
    
    all_news = chinapress_news + oriental_news
    
    # 发送新闻（带重试机制）
    success_count = 0
    for news in all_news:
        if "❌" not in news:  # 只发送成功抓取的新闻
            max_retries = 3
            for attempt in range(max_retries):
                if send_telegram(news):
                    success_count += 1
                    time.sleep(random.uniform(1, 3))  # 随机消息间隔
                    break
                elif attempt < max_retries - 1:
                    print(f"等待{5+attempt*2}秒后重试 ({attempt+1}/{max_retries})...")
                    time.sleep(5 + attempt * 2)
    
    print("\n" + "="*50)
    print(f"新闻推送完成! 成功发送 {success_count}/{len(all_news)} 条新闻")
    print("="*50)
    
    # 如果有任何失败，非零退出码
    if success_count < len(all_news):
        sys.exit(1)

if __name__ == "__main__":
    main()
