import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger('news_crawler')

NEWS_CATEGORIES = [
    "latest", "nation", "metro", "business", "tech", "lifestyle", "sports", "world"
]

BASE_URL = "https://www.thestar.com.my/news/"

def fetch_news():
    all_news = []

    for category in NEWS_CATEGORIES:
        url = f"{BASE_URL}{category}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"分类 {category} 请求失败: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select(".listing__content")

            for article in articles:
                title_tag = article.select_one("h3")
                link_tag = article.select_one("a")
                img_tag = article.select_one("img")

                if title_tag and link_tag:
                    news_item = {
                        "title": title_tag.get_text(strip=True),
                        "link": link_tag['href'],
                        "image": img_tag['src'] if img_tag else None
                    }
                    all_news.append(news_item)

        except Exception as e:
            logger.error(f"抓取分类 {category} 失败: {e}", exc_info=True)

    logger.info(f"共抓取 {len(all_news)} 条新闻")
    return all_news

def select_random_news(news_list, count=5):
    import random
    return random.sample(news_list, min(count, len(news_list)))
