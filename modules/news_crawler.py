import requests
from bs4 import BeautifulSoup
import random
import logging
from datetime import datetime
import re
import sqlite3
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('news_crawler')

# News category URLs
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

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
            pass  # Ignore duplicate inserts
    
    def cleanup_old_entries(self, days=7):
        """Remove entries older than specified days"""
        self.conn.execute("DELETE FROM sent_news WHERE sent_time < datetime('now', ?)", (f'-{days} days',))
        self.conn.commit()

def fetch_news():
    """Fetch news from TheStar"""
    db = NewsDatabase()
    all_news = []
    
    for category, url in NEWS_CATEGORIES.items():
        try:
            logger.info(f"Fetching category: {category}")
            response = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Select articles - adjust selector based on actual site structure
            articles = soup.select('div.timeline-item')[:20]  # Limit to 20 per category
            
            for article in articles:
                try:
                    title_elem = article.select_one('h2 a, h3 a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f'https://www.thestar.com.my{link}'
                    
                    # Skip duplicates
                    if db.is_duplicate(link):
                        continue
                    
                    img_elem = article.select_one('img')
                    img_url = img_elem.get('src', '') if img_elem else ''
                    
                    summary_elem = article.select_one('p')
                    summary = summary_elem.text.strip() if summary_elem else ""
                    
                    time_elem = article.select_one('div.timestamp, time')
                    time_str = time_elem.text.strip() if time_elem else datetime.now().strftime('%Y-%m-%d')
                    
                    # Clean time format
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
                    logger.error(f"Error parsing article: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error fetching category {category}: {e}", exc_info=True)
    
    # Clean up old entries
    db.cleanup_old_entries()
    
    return all_news

def select_random_news(news_list, min_news=30, max_news=50):
    """Select random news items"""
    if not news_list:
        return []
    
    num_news = random.randint(min_news, min(max_news, len(news_list)))
    return random.sample(news_list, num_news)

def format_news_message(news):
    """Format news for Telegram"""
    return (
        f"🔹 *{news['title']}*\n"
        f"⏰ {news['time']}\n"
        f"{news['summary']}\n"
        f"[Read more]({news['link']})"
    )

if __name__ == "__main__":
    # Test crawler
    news = fetch_news()
    print(f"Fetched {len(news)} news items")
    for i, item in enumerate(news[:3], 1):
        print(f"\n--- News {i} ---")
        print(f"Title: {item['title']}")
        print(f"Category: {item['category']}")
        print(f"Link: {item['link']}")
