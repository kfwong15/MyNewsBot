import requests
import logging
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

API_URL    = "https://api.thestar.com.my/mobile-json/news/latest"
BASE_DOMAIN = "https://www.thestar.com.my"
MIN_COUNT   = 10

def fetch_news() -> list[dict]:
    """
    调用 Mobile JSON API，直接获取最新新闻，
    包含 title, link, image, summary。
    """
    try:
        resp = requests.get(API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"API 请求失败: {e}", exc_info=True)
        return []

    news = []
    for item in data.get('items', [])[:MIN_COUNT]:
        title   = item.get('title')
        path    = item.get('uri')
        link    = urljoin(BASE_DOMAIN, path)
        image   = item.get('imageUrl')
        content = item.get('summary') or item.get('teaser')

        news.append({
            "title": title,
            "link": link,
            "image": image,
            "content": content
        })

    logger.info(f"✅ API 抓取到 {len(news)} 条新闻")
    return news

def select_random_news(news_list: list, count: int = 10) -> list[dict]:
    import random
    return random.sample(news_list, min(count, len(news_list)))
