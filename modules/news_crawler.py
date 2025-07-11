import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

logger = logging.getLogger('news_crawler')

# Google 新闻（中文）RSS，包含马来西亚新闻
RSS_FEED = "https://news.google.com/rss/search?q=马来西亚&hl=zh-CN&gl=MY&ceid=MY:zh-Hans"
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
    抓取 Google 新闻 RSS（中文），返回清晰标题、干净内容、图片、链接。
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
    ns = {'media': 'http://search.yahoo.com/mrss/'}

    for item in root.findall('.//item'):
        title = item.findtext('title', '').strip()
        link  = item.findtext('link', '').strip()
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

        # 内容清洗
        raw_desc = item.findtext('description', '').strip()
        soup = BeautifulSoup(raw_desc, 'html.parser')
        content = soup.get_text(separator=' ', strip=True)
        content = ''.join(c for c in content if c.isalnum() or c.isspace())

        news.append({
            "title":   ''.join(c for c in title if c.isalnum() or c.isspace()),
            "link":    link,
            "image":   img,
            "content": content
        })
        seen.add(link)
        if len(news) >= MIN_COUNT:
            break

    logger.info(f"✅ Google 中文新闻抓到 {len(news)} 条")
    return news

def select_random_news(news_list: list[dict], count: int = 10) -> list[dict]:
    import random
    return random.sample(news_list, min(len(news_list), count))
