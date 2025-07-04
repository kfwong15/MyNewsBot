import os
import requests
import time
import sys
import random
from datetime import datetime
from bs4 import BeautifulSoup

# ====== 配置 ======
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置TG_BOT_TOKEN和TG_CHAT_ID环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# The Star 新闻分类
THE_STAR_CATEGORIES = {
    "最新新闻": "https://www.thestar.com.my/news",
    "国内新闻": "https://www.thestar.com.my/news/nation",
    "政治新闻": "https://www.thestar.com.my/news/politics",
    "商业新闻": "https://www.thestar.com.my/business",
    "体育新闻": "https://www.thestar.com.my/sport",
    "娱乐新闻": "https://www.thestar.com.my/entertainment",
    "科技新闻": "https://www.thestar.com.my/tech",
    "生活方式": "https://www.thestar.com.my/lifestyle"
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
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "DNT": "1"
    }

def fetch_thestar_news(max_news=50):
    """抓取The Star新闻"""
    all_news = []
    seen_links = set()  # 用于去重
    
    print(f"🔍 开始抓取The Star新闻，目标数量: {max_news}")
    
    # 随机打乱分类顺序
    categories = list(THE_STAR_CATEGORIES.items())
    random.shuffle(categories)
    
    for category_name, category_url in categories:
        if len(all_news) >= max_news:
            break
            
        try:
            print(f"⏳ 抓取分类: {category_name}...")
            response = requests.get(category_url, headers=get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻卡片
            news_cards = soup.select('div.story-card')
            
            for card in news_cards:
                if len(all_news) >= max_news:
                    break
                    
                # 提取标题
                title_tag = card.select_one('h2.story-title a, h3.story-title a')
                if not title_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                
                # 提取链接
                link = title_tag.get('href', '')
                if not link.startswith('http'):
                    link = f"https://www.thestar.com.my{link}"
                
                # 去重检查
                if link in seen_links:
                    continue
                seen_links.add(link)
                
                # 提取图片（如果有）
                img_tag = card.select_one('img')
                img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
                
                # 提取描述
                desc_tag = card.select_one('p.story-summary')
                description = desc_tag.get_text(strip=True) if desc_tag else ""
                
                # 提取发布时间
                time_tag = card.select_one('div.timestamp')
                pub_time = time_tag.get_text(strip=True) if time_tag else ""
                
                # 构建消息
                news_item = f"📰 <b>{title}</b>\n" \
                           f"🏷️ 分类: {category_name}\n"
                
                if pub_time:
                    news_item += f"⏰ 时间: {pub_time}\n"
                
                if description:
                    news_item += f"📝 {description}\n"
                
                if img_url:
                    # 在Telegram中，图片需要单独发送
                    # 这里先发送文本消息，稍后发送图片
                    news_item += f"🖼️ 图片: [查看图片]"
                
                news_item += f"🔗 {link}"
                
                all_news.append({
                    "text": news_item,
                    "image": img_url
                })
            
            # 分类间延迟
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"⚠️ 分类 '{category_name}' 抓取失败: {str(e)}")
    
    return all_news[:max_news]

def send_telegram_text(message):
    """发送文本消息到Telegram"""
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
        print(f"❌ 文本发送失败: {str(e)}")
        return False

def send_telegram_photo(image_url, caption=""):
    """发送图片到Telegram"""
    try:
        photo_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": TG_CHAT_ID,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML"
        }
        
        response = requests.post(photo_url, json=payload, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ 图片发送失败: {str(e)}")
        return False

def main():
    print("="*50)
    start_time = datetime.now()
    print(f"📅 The Star新闻推送任务开始 {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 获取30-50条新闻
    target_count = random.randint(30, 50)
    news_items = fetch_thestar_news(target_count)
    
    if not news_items:
        print("❌ 未找到任何新闻，发送通知")
        news_items = [{"text": "📢 今日未能获取The Star新闻，请稍后重试", "image": ""}]
    
    print(f"\n📊 共找到 {len(news_items)} 条新闻，准备发送...")
    
    success_count = 0
    for index, news in enumerate(news_items, 1):
        # 先发送文本消息
        if send_telegram_text(news["text"]):
            success_count += 1
            
            # 如果有图片，发送图片
            if news["image"] and news["image"].startswith("http"):
                time.sleep(0.5)  # 文本和图片之间延迟
                send_telegram_photo(news["image"])
            
            print(f"✅ 已发送 {index}/{len(news_items)}")
            
            # 随机延迟，避免发送过快
            delay = random.uniform(1.0, 3.0)
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
    report = f"📊 The Star新闻推送报告\n" \
             f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n" \
             f"⏰ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n" \
             f"⏱️ 总耗时: {duration.total_seconds():.1f}秒\n" \
             f"📰 目标数量: {target_count}\n" \
             f"✅ 成功发送: {success_count}\n" \
             f"🔁 下次运行: 5小时后"
    
    send_telegram_text(report)
    
    if success_count < len(news_items):
        sys.exit(1)

if __name__ == "__main__":
    main()
