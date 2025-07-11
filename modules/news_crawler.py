# modules/news_crawler.py

import requests
import xml.etree.ElementTree as ET
import logging
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

# RSS 源地址
RSS_FEED_URL = "https://www.thestar.com.my/rss/latest.rss"
MIN_COUNT = 10

def fetch_news():
    """
    从 The Star 官方 RSS 提取至少 MIN_COUNT 条最新新闻。
    """
    try:
        resp = requests.get(RSS_FEED_URL, timeout=10)
        resp.raise_for_status()
        logger.info(f"▶ RSS 请求成功: {RSS_FEED_URL}")
    except Exception as e:
        logger.error(f"RSS 请求失败: {e}", exc_info=True)
        return []

    news_list = []
    seen = set()

    # 解析 RSS XML
    root = ET.fromstring(resp.content)
    # 找到所有 <item>
    for item in root.findall('.//item'):
        title = item.findtext('title', default='').strip()
        link = item.findtext('link', default='').strip()
        if not title or not link or link in seen:
            continue

        # 尝试找图片：<enclosure url="...">
        img_url = None
        enclosure = item.find('enclosure')
        if enclosure is not None and 'url' in enclosure.attrib:
            img_url = urljoin(link, enclosure.attrib['url'])
        else:
            # 尝试 media:content
            media = item.find('{http://search.yahoo.com/mrss/}content')
            if media is not None and 'url' in media.attrib:
                img_url = urljoin(link, media.attrib['url'])

        news_list.append({
            "title": title,
            "link": link,
            "image": img_url
        })
        seen.add(link)

        if len(news_list) >= MIN_COUNT:
            break

    logger.info(f"✅ 从 RSS 抓取到 {len(news_list)} 条新闻")
    return news_list

def select_random_news(news_list, count=10):
    import random
    return random.sample(news_list, min(len(news_list), count))
