import os
import requests
from bs4 import BeautifulSoup
import time

# 获取 Telegram Token 和 Chat ID
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# 通用请求头，模拟真实浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}

# ✅ 可靠的中国报新闻抓取
def fetch_chinapress():
    try:
        url = "https://www.chinapress.com.my/"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # 检查HTTP错误
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 查找最新新闻条目
        for article in soup.select('article.post-item')[:3]:
            title_tag = article.find('h3', class_='post-title')
            if not title_tag:
                continue
                
            title = title_tag.get_text(strip=True)
            link = title_tag.find('a')['href']
            
            # 确保链接完整
            if not link.startswith('http'):
                link = f"https://www.chinapress.com.my{link}"
                
            news_items.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
        
        return news_items if news_items else ["❌ 中国报抓取失败：未找到新闻内容"]
        
    except Exception as e:
        return [f"❌ 中国报抓取失败：{str(e)}"]

# ✅ 可靠的东方日报新闻抓取
def fetch_oriental():
    try:
        url = "https://www.orientaldaily.com.my"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # 查找头条新闻
        top_news = soup.select_one('div.top-news')
        if top_news:
            title_tag = top_news.find('h1')
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag.find('a')['href']
                if not link.startswith('http'):
                    link = f"https://www.orientaldaily.com.my{link}"
                news_items.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")
        
        # 查找其他新闻
        for article in soup.select('div.news-list')[:2]:
            title_tag = article.find('h2')
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag.find('a')['href']
                if not link.startswith('http'):
                    link = f"https://www.orientaldaily.com.my{link}"
                news_items.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")
                
        return news_items if news_items else ["❌ 东方日报抓取失败：未找到新闻内容"]
        
    except Exception as e:
        return [f"❌ 东方日报抓取失败：{str(e)}"]

# ✅ 可靠的Telegram消息发送
def send_telegram(message):
    try:
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(API_URL, json=payload, timeout=15)
        response.raise_for_status()
        
        print(f"✅ 消息发送成功: {message[:30]}...")
        return True
        
    except Exception as e:
        print(f"❌ 消息发送失败: {str(e)}")
        return False

# ✅ 主函数：抓取 + 推送
def main():
    print("开始抓取新闻...")
    
    # 获取新闻
    all_news = []
    all_news.extend(fetch_chinapress())
    all_news.extend(fetch_oriental())
    
    print(f"共找到 {len(all_news)} 条新闻")
    
    # 发送新闻
    for news in all_news:
        if "❌" not in news:  # 只发送成功抓取的新闻
            send_telegram(news)
            time.sleep(1)  # 避免发送过快被限制
    
    print("新闻推送完成！")

if __name__ == "__main__":
    main()
