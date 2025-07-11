# modules/news_crawler.py

import logging
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger('news_crawler')

# Google News “Malaysia” 话题 RSS，包含当天最新当地新闻
RSS_FEED = (
    "https://news.google.com/rss/topics/"
    "CAAqIggKIhxDQkFTRHdvSkwyMHZNRGx3Yld0MkVnSmxiaWdBUAE"
    "?hl=en-MY&gl=MY&ceid=MY:en"
)
MIN_COUNT = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}

def fetch_news() -> list[dict]:
    """
    抓取 Google News Malaysia RSS，返回最新 MIN_COUNT 条新闻：
    - title: 新闻标题
    - link: 原始文章链接
    - image: RSS 中的缩略图或 None
    - content: RSS 提供的摘要
    """
    try:
        resp = requests.get(RSS_FEED, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.error(f"RSS 请求失败 ({RSS_FEED}): {e}", exc_info=True)
        return []

    news = []
    seen = set()
    # Google News RSS 里 <item> 多媒体标签在 media:thumbnail 或 media:content
    ns = {'media': 'http://search.yahoo.com/mrss/'}

    for item in root.findall('.//item'):
        title = item.findtext('title', '').strip()
        link  = item.findtext('link',  '').strip()
        if not title or not link or link in seen:
            continue

        # 图片
        img = None
        thumb = item.find('media:thumbnail', ns)
        if thumb is not None and thumb.attrib.get('url'):
            img = thumb.attrib['url']
        else:
            mcont = item.find('media:content', ns)
            if mcont is not None and mcont.attrib.get('url'):
                img = mcont.attrib['url']

        # 摘要
        content = item.findtext('description', '').strip()

        news.append({
            "title":   title,
            "link":    link,
            "image":   img,
            "content": content
        })
        seen.add(link)
        if len(news) >= MIN_COUNT:
            break

    logger.info(f"✅ Google News RSS 抓到 {len(news)} 条新闻")
    return news

def select_random_news(news_list: list[dict], count: int = 10) -> list[dict]:
    import random
    return random.sample(news_list, min(len(news_list), count))
