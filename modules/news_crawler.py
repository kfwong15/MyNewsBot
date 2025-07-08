import requests
from bs4 import BeautifulSoup
import random
import logging
from datetime import datetime
import re
import sqlite3
import os
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('news_crawler')

# 新闻分类URL - 已更新并验证
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

# 多个用户代理轮换使用
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
]

class NewsDatabase:
    def __init__(self, db_path='news.db'):
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS sent_news
                           (link TEXT PRIMARY KEY, sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()
    
    def is_duplicate(self, link):
        """检查链接是否已发送过"""
        cursor = self.conn.execute("SELECT 1 FROM sent_news WHERE link=?", (link,))
        return cursor.fetchone() is not None
    
    def mark_as_sent(self, link):
        """标记链接为已发送"""
        try:
            self.conn.execute("INSERT OR IGNORE INTO sent_news (link) VALUES (?)", (link,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # 忽略重复插入
    
    def cleanup_old_entries(self, days=7):
        """移除超过指定天数的条目"""
        self.conn.execute("DELETE FROM sent_news WHERE sent_time < datetime('now', ?)", (f'-{days} days',))
        self.conn.commit()
        logger.info(f"清理了 {self.conn.total_changes} 条旧记录")

def get_random_user_agent():
    """获取随机用户代理"""
    return random.choice(USER_AGENTS)

def create_session():
    """创建带有随机用户代理的会话"""
    session = requests.Session()
    user_agent = get_random_user_agent()
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.thestar.com.my/',
    })
    logger.info(f"使用用户代理: {user_agent[:60]}...")
    return session

def get_proxy():
    """从环境变量获取代理设置"""
    proxy_url = os.getenv('PROXY_URL')
    if proxy_url:
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    return None

def check_website_health(session):
    """检查TheStar网站是否可用"""
    try:
        logger.info("检查网站健康状况...")
        response = session.get('https://www.thestar.com.my', timeout=10)
        
        if response.status_code == 200:
            logger.info("网站状态正常")
            return True
        else:
            logger.warning(f"网站返回非200状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"网站健康检查失败: {e}")
        return False

def fetch_category_news(session, category, url, db):
    """抓取单个分类的新闻"""
    logger.info(f"开始抓取分类: {category} ({url})")
    news_items = []
    
    try:
        # 设置代理
        proxies = get_proxy()
        
        # 发送请求
        response = session.get(url, timeout=15, proxies=proxies)
        logger.info(f"响应状态: {response.status_code}")
        
        # 处理重定向
        if response.history:
            logger.info(f"请求被重定向至: {response.url}")
        
        # 检查状态码
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 多种可能的选择器
        possible_selectors = [
            'div.timeline-item',
            'article.card',
            '.story-list .story',
            '.news-list .item',
            '.headline-list .item',
            'div.article'
        ]
        
        articles = None
        for selector in possible_selectors:
            articles = soup.select(selector)
            if articles:
                logger.info(f"使用选择器 '{selector}' 找到 {len(articles)} 篇文章")
                articles = articles[:20]  # 每类最多20条
                break
        
        # 备用解析策略
        if not articles:
            logger.warning(f"未找到文章容器，尝试备用方法...")
            
            # 尝试查找所有包含新闻链接的元素
            news_links = soup.select('a[href*="/news/"]')
            if news_links:
                logger.info(f"找到 {len(news_links)} 个新闻链接")
                # 获取链接的父容器作为文章元素
                articles = [link.find_parent('div') for link in news_links]
                articles = [a for a in articles if a is not None][:20]
        
        if not articles:
            logger.warning(f"分类 {category} 未找到任何文章")
            return []
        
        # 解析每篇文章
        for article in articles:
            try:
                # 尝试多种选择器找到标题
                title_elem = article.select_one('h2 a, h3 a, .headline a, .title a, a.headline')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')
                
                # 处理相对URL
                if link and not link.startswith('http'):
                    if link.startswith('//'):
                        link = f'https:{link}'
                    else:
                        link = f'https://www.thestar.com.my{link}'
                
                # 跳过重复
                if db.is_duplicate(link):
                    continue
                
                # 尝试多种选择器找到图片
                img_elem = article.select_one('img, .image img, .thumbnail img')
                img_url = img_elem.get('src', '') if img_elem else ''
                if img_url and img_url.startswith('//'):
                    img_url = f'https:{img_url}'
                elif img_url and img_url.startswith('/'):
                    img_url = f'https://www.thestar.com.my{img_url}'
                
                # 尝试多种选择器找到摘要
                summary_elem = article.select_one('p, .summary, .description, .excerpt')
                summary = summary_elem.get_text(strip=True) if summary_elem else ""
                
                # 尝试多种选择器找到时间
                time_elem = article.select_one('div.timestamp, time, .date, .publish-date')
                time_str = time_elem.get_text(strip=True) if time_elem else datetime.now().strftime('%Y-%m-%d')
                
                # 清理时间格式
                time_str = re.sub(r'\s+', ' ', time_str)
                
                # 添加到结果列表
                news_items.append({
                    'title': title,
                    'link': link,
                    'img_url': img_url,
                    'summary': summary,
                    'time': time_str,
                    'category': category
                })
                
                # 标记为已发送
                db.mark_as_sent(link)
                
            except Exception as e:
                logger.error(f"解析文章失败: {e}", exc_info=True)
        
        logger.info(f"成功抓取 {len(news_items)} 条 {category} 新闻")
        return news_items
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "未知"
        logger.error(f"HTTP错误 ({status_code}): {e}")
        
        # 对于政治分类使用备用URL
        if status_code == 404 and "politics" in category:
            logger.warning("尝试使用政治分类备用URL")
            return fetch_category_news(session, category, "https://www.thestar.com.my/news/nation/politics", db)
        
        return []
    
    except Exception as e:
        logger.error(f"抓取分类 {category} 失败: {e}", exc_info=True)
        return []

def fetch_news():
    """从TheStar抓取新闻"""
    db = NewsDatabase()
    all_news = []
    
    # 创建会话
    session = create_session()
    
    # 首先访问主页获取必要的 cookies
    try:
        logger.info("访问主页获取 cookies...")
        homepage_response = session.get('https://www.thestar.com.my', timeout=15)
        homepage_response.raise_for_status()
    except Exception as e:
        logger.warning(f"获取主页 cookies 失败: {e}")
    
    # 检查网站健康状态
    if not check_website_health(session):
        logger.error("网站不可用，跳过抓取")
        return []
    
    # 遍历所有分类
    for category, url in NEWS_CATEGORIES.items():
        max_retries = 2
        retry_count = 0
        category_news = []
        
        while retry_count < max_retries and not category_news:
            category_news = fetch_category_news(session, category, url, db)
            retry_count += 1
            
            if not category_news and retry_count < max_retries:
                wait_time = 3
                logger.info(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
        
        all_news.extend(category_news)
    
    # 清理旧条目
    db.cleanup_old_entries()
    
    logger.info(f"总共抓取到 {len(all_news)} 条新闻")
    return all_news

def select_random_news(news_list, min_news=30, max_news=50):
    """随机选择指定数量的新闻"""
    if not news_list:
        logger.warning("新闻列表为空，无法选择")
        return []
    
    num_news = random.randint(min_news, min(max_news, len(news_list)))
    selected = random.sample(news_list, num_news)
    logger.info(f"从 {len(news_list)} 条新闻中随机选择了 {num_news} 条")
    return selected

def format_news_message(news):
    """格式化新闻为Telegram消息"""
    # 清理特殊字符以避免Markdown解析问题
    def escape_markdown(text):
        for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            text = text.replace(char, f'\\{char}')
        return text
    
    title = escape_markdown(news['title'])
    summary = escape_markdown(news['summary'])
    
    return (
        f"🔹 *{title}*\n"
        f"⏰ {news['time']}\n"
        f"{summary}\n"
        f"[阅读全文]({news['link']})"
    )

if __name__ == "__main__":
    # 测试爬虫
    print("=" * 50)
    print("开始测试新闻爬虫")
    print("=" * 50)
    
    news = fetch_news()
    print(f"\n抓取到 {len(news)} 条新闻")
    
    if news:
        print("\n前3条新闻示例:")
        for i, item in enumerate(news[:3], 1):
            print(f"\n--- 新闻 {i} ---")
            print(f"标题: {item['title']}")
            print(f"分类: {item['category']}")
            print(f"链接: {item['link']}")
            print(f"图片: {item['img_url']}")
            print(f"摘要: {item['summary']}")
            print(f"时间: {item['time']}")
        
        # 测试随机选择
        selected = select_random_news(news)
        print(f"\n随机选择 {len(selected)} 条新闻")
        
        # 测试消息格式化
        print("\n格式化消息示例:")
        print(format_news_message(news[0]))
    else:
        print("未抓取到任何新闻")
