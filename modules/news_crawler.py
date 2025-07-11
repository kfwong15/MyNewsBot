# modules/news_crawler.py

import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

# 采用南洋商报 (Nanyang Siang Pau) WordPress Feed
RSS_FEED    = "https://www.enanyang.my/feed"
BASE_DOMAIN = "https://www.enanyang.my"
MIN_COUNT   = 10

# 带 UA 防 403
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}

def fetch_news() -> list[dict]:
    """
    抓取南洋商报 RSS，返回最新 MIN_COUNT 条新闻，
    包含 title, link, image, content 摘要。
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
    for item in root.findall(".//item"):
        title = item.findtext("title", default="").strip()
        link  = item.findtext("link",  default="").strip()
        if not title or not link or link in seen:
            continue

        # description 里通常含摘要和首图
        desc_html = item.findtext("description", default="")
        soup = BeautifulSoup(desc_html, "html.parser")

        # 图片
        img_tag = soup.find("img")
        image = urljoin(BASE_DOMAIN, img_tag["src"]) if img_tag and img_tag.get("src") else None

        # 摘要：去掉 <img> 取纯文本
        if img_tag:
            img_tag.decompose()
        content = soup.get_text(separator=" ", strip=True)

        news.append({
            "title":   title,
            "link":    link,
            "image":   image,
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
