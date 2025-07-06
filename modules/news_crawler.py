import requests
from bs4 import BeautifulSoup
import random
import logging
from datetime import datetime
import re
import sqlite3
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('news_crawler')

# 新闻分类URL
NEWS_CATEGORIES = {
    'latest': 'https://www.thestar.com.my/news',
    'nation': 'https://www.thestar.com.my/news/nation',
    'politics': 'https://www.thestar.com.my/news/politics',
    'business': 'https://www.thestar.com.my/business',
    'sport': 'https://www.thestar.com.my/sport',
    'entertainment': 'https://www.thestar.com.my/entertainment',
    'tech': 'https://www.thestar.com.my/tech',
    'lifestyle': 'https://www.thestar.com.my/lifestyle'
}

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}

class NewsDatabase:
    def __init__(self, db_path='news.db'):
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS sent_news
                           (link TEXT PRIMARY KEY, sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()
    
    def is_duplicate(self, link):
        cursor = self.conn.execute("SELECT 1 FROM sent_news WHERE link=?", (link,))
        return cursor.fetchone() is not None
    
    def mark_as_sent(self, link):
        try:
            self.conn.execute("INSERT OR IGNORE INTO sent_news (link) VALUES (?)", (link,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # 忽略重复插入
    
    def cleanup_old_entries(self, days=7):
        """移除超过指定天数的条目"""
        self.conn.execute("DELETE FROM sent_news WHERE sent_time < datetime('now', ?)", (f'-{days} days',))
        self.conn.commit()

def fetch_news():
    """从TheStar抓取新闻"""
    db = NewsDatabase()
    all_news = []
    
    for category, url in NEWS_CATEGORIES.items():
        try:
            logger.info(f"抓取分类: {category}")
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 根据实际网站结构调整选择器
            articles = soup.select('div.timeline-item')[:20]  # 每类最多20条
            
            for article in articles:
                try:
                    title_elem = article.select_one('h2 a, h3 a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f'https://www.thestar.com.my{link}'
                    
                    # 跳过重复
                    if db.is_duplicate(link):
                        continue
                    
                    img_elem = article.select_one('img')
                    img_url = img_elem.get('src', '') if img_elem else ''
                    
                    summary_elem = article.select_one('p')
                    summary = summary_elem.text.strip() if summary_elem else ""
                    
                    time_elem = article.select_one('div.timestamp, time')
                    time_str = time_elem.text.strip() if time_elem else datetime.now().strftime('%Y-%m-%d')
                    
                    # 清理时间格式
                    time_str = re.sub(r'\s+', ' ', time_str)
                    
                    all_news.append({
                        'title': title,
                        'link': link,
                        'img_url': img_url,
                        'summary': summary,
                        'time': time_str,
                        'category': category
                    })
                except Exception as e:
                    logger.error(f"解析文章失败: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"抓取分类 {category} 失败: {e}", exc_info=True)
    
    # 清理旧条目
    db.cleanup_old_entries()
    
    return all_news

def select_random_news(news_list, min_news=30, max_news=50):
    """随机选择指定数量的新闻"""
    if not news_list:
        return []
    
    num_news = random.randint(min_news, min(max_news, len(news_list)))
    return random.sample(news_list, num_news)

def format_news_message(news):
    """格式化新闻为Telegram消息"""
    return (
        f"🔹 *{news['title']}*\n"
        f"⏰ {news['time']}\n"
        f"{news['summary']}\n"
        f"[阅读全文]({news['link']})"
    )

if __name__ == "__main__":
    # 测试爬虫
    news = fetch_news()
    print(f"抓取到 {len(news)} 条新闻")
    for i, item in enumerate(news[:3], 1):
        print(f"\n--- 新闻 {i} ---")
        print(f"标题: {item['title']}")
        print(f"分类: {item['category']}")
        print(f"链接: {item['link']}")
