# modules/news_crawler.py

import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

# 只用 Google News RSS 强制拿到至少 10 条
GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/"
    "search?q=site:thestar.com.my/news/latest&hl=en-MY&gl=MY&ceid=MY:en"
)
BASE_DOMAIN = "https://www.thestar.com.my"
MIN_COUNT = 10

def fetch_google_rss() -> list[dict]:
    """
    调用 Google News RSS，拿最新 /news/latest 下的文章链接和标题。
    最多返回 MIN_COUNT 条。
    """
    items = []
    try:
        resp = requests.get(GOOGLE_NEWS_RSS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.error(f"Google RSS 请求失败: {e}", exc_info=True)
        return items

    for node in root.findall('.//item'):
        title = node.findtext('title', default='').strip()
        link  = node.findtext('link',  default='').strip()
        if title and link:
            items.append({"title": title, "link": link})
        if len(items) >= MIN_COUNT:
            break

    logger.info(f"✅ Google RSS 抓到 {len(items)} 条")
    return items


def get_article_details(url: str) -> tuple[str, str | None, str]:
    """
    请求文章详情页，解析:
      - 标题: <meta property="og:title"> 或 <h1>
      - 图片:  <meta property="og:image">
      - 内容:  第一个长度 >50 的 <p> 作为摘要
    """
    title = ""
    image = None
    content = ""

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 标题
        ogt = soup.find('meta', property='og:title')
        if ogt and ogt.get('content'):
            title = ogt['content'].strip()
        else:
            h1 = soup.find('h1')
            title = h1.get_text(strip=True) if h1 else ""

        # 图片
        ogi = soup.find('meta', property='og:image')
        if ogi and ogi.get('content'):
            image = ogi['content'].strip()

        # 内容摘要
        for p in soup.find_all('p'):
            txt = p.get_text(strip=True)
            if len(txt) > 50:
                content = txt
                break

    except Exception as e:
        logger.warning(f"详情解析失败 {url}: {e}")

    return title, image, content


def fetch_news() -> list[dict]:
    """
    主调用：先从 Google RSS 拉标题和链接，
    再逐篇请求详情页补齐标题、配图和内容摘要。
    """
    raw = fetch_google_rss()
    news = []

    for item in raw:
        title, img, snippet = get_article_details(item['link'])
        # 如果详情页没有抓到标题，用 RSS 标题兜底
        final_title = title or item['title']
        news.append({
            "title": final_title,
            "link": item['link'],
            "image": img,
            "content": snippet
        })

    logger.info(f"🔚 最终组装 {len(news)} 条新闻")
    return news


def select_random_news(news_list: list[dict], count: int = 10) -> list[dict]:
    """
    从列表中随机选若干条新闻（或全选）。
    """
    import random
    return random.sample(news_list, min(len(news_list), count))
