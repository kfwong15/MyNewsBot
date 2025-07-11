# modules/news_crawler.py

import logging
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

# 光华日报官方 RSS
RSS_FEED    = "https://www.kwongwah.com.my/feed"
BASE_DOMAIN = "https://www.kwongwah.com.my"
MIN_COUNT   = 10

# 防止 403，加浏览器 UA
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}

def fetch_news() -> list[dict]:
    """
    抓取光华日报 RSS，返回最新 MIN_COUNT 条新闻（title, link, image, content）。
    """
    try:
        resp = requests.get(RSS_FEED, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        logger.info(f"RSS 请求成功: {RSS_FEED}")
    except Exception as e:
        logger.error(f"RSS 请求失败 ({RSS_FEED}): {e}", exc_info=True)
        return []

    news = []
    seen = set()
    for item in root.findall('.//item'):
        title = item.findtext('title', default='').strip()
        link  = item.findtext('link',  default='').strip()
        if not title or not link or link in seen:
            continue

        # enclosure 中的图片
        img = None
        enc = item.find('enclosure')
        if enc is not None and enc.attrib.get('url'):
            img = urljoin(BASE_DOMAIN, enc.attrib['url'])

        # description 作为摘要
        content = item.findtext('description', default='').strip()

        news.append({
            "title":   title,
            "link":    link,
            "image":   img,
            "content": content
        })
        seen.add(link)
        if len(news) >= MIN_COUNT:
            break

    logger.info(f"✅ RSS 抓到 {len(news)} 条新闻")
    return news


def select_random_news(news_list: list[dict], count: int = 10) -> list[dict]:
    import random
    return random.sample(news_list, min(len(news_list), count))
