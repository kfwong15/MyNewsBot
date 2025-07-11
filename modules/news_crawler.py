# modules/news_crawler.py

import logging
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

# 星洲日报中文新闻 RSS 源
RSS_FEED   = "https://www.sinchew.com.my/rss/news.xml"
BASE_DOMAIN = "https://www.sinchew.com.my"
MIN_COUNT   = 10

def fetch_news() -> list[dict]:
    """
    抓取星洲日报 RSS，取最新 MIN_COUNT 条新闻，
    返回每条的 title, link, image（若有）, content（description）。
    """
    try:
        resp = requests.get(RSS_FEED, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.error(f"RSS 请求失败: {e}", exc_info=True)
        return []

    news = []
    seen = set()

    for item in root.findall('.//item'):
        title = item.findtext('title', default='').strip()
        link  = item.findtext('link',  default='').strip()
        if not title or not link or link in seen:
            continue

        # 尝试从 <enclosure> 取配图
        img = None
        enc = item.find('enclosure')
        if enc is not None and enc.attrib.get('url'):
            img = urljoin(BASE_DOMAIN, enc.attrib['url'])

        # 摘要
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

    logger.info(f"✅ 星洲日报 RSS 抓到 {len(news)} 条新闻")
    return news

def select_random_news(news_list: list[dict], count: int = 10) -> list[dict]:
    import random
    return random.sample(news_list, min(len(news_list), count))
