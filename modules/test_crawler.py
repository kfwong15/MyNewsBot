import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

logger = logging.getLogger('news_crawler')

RSS_FEED = "https://www.chinanews.com.cn/rss/scroll-news.xml"
MIN_COUNT = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}

def fetch_news() -> list[dict]:
    try:
        resp = requests.get(RSS_FEED, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.error(f"RSS 请求失败: {e}", exc_info=True)
        return []

    news = []
    seen_titles = set()
    for item in root.findall('.//item'):
        raw_title = item.findtext('title', '').strip()
        link = item.findtext('link', '').strip()
        raw_desc = item.findtext('description', '').strip()

        # 清洗标题和内容
        title = ''.join(c for c in raw_title if c.isalnum() or c.isspace())
        soup = BeautifulSoup(raw_desc, 'html.parser')
        content = soup.get_text(separator=' ', strip=True)
        content = ''.join(c for c in content if c.isalnum() or c.isspace())

        # 提取图片（从 description 中的 <img>）
        img_tag = soup.find('img')
        image = img_tag['src'] if img_tag and img_tag.has_attr('src') else None

        if not title or not link or title in seen_titles or not image:
            continue

        news.append({
            "title": title,
            "link": link,
            "image": image,
            "content": content
        })
        seen_titles.add(title)
        if len(news) >= MIN_COUNT:
            break

    logger.info(f"✅ 抓到 {len(news)} 条新闻（已去重、清洗、带图）")
    return news

def select_random_news(news_list: list[dict], count: int = 10) -> list[dict]:
    import random
    return random.sample(news_list, min(len(news_list), count))
