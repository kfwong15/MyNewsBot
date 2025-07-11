# modules/news_crawler.py

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

BASE_DOMAIN = "https://www.thestar.com.my"
LATEST_PATH = "/news/latest/"  # 注意要带斜杠
MIN_COUNT = 10

def fetch_news():
    """
    抓取最新栏目至少 MIN_COUNT 条新闻（title + link + 可选 image）。
    不用类名匹配，直接根据 href 前缀过滤 <a> 标签。
    """
    url = urljoin(BASE_DOMAIN, LATEST_PATH)
    logger.info(f"▶ 抓取最新新闻列表: {url}")

    try:
        resp = requests.get(url, timeout=10)
        logger.info(f"  状态码: {resp.status_code}")
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"HTTP 请求失败: {e}", exc_info=True)
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    seen = set()
    news_list = []

    # 遍历所有 <a>，挑出 /news/latest/ 开头的链接
    for a in soup.find_all("a", href=True):
        href = a['href']
        if not href.startswith(LATEST_PATH):
            continue

        full_link = urljoin(BASE_DOMAIN, href)
        title = a.get_text(strip=True)
        if not title or full_link in seen:
            continue

        # 尝试找图片
        img_tag = a.find("img")
        img_url = None
        if img_tag and img_tag.get("src"):
            img_url = urljoin(BASE_DOMAIN, img_tag["src"])

        news_list.append({
            "title": title,
            "link": full_link,
            "image": img_url
        })
        seen.add(full_link)

        if len(news_list) >= MIN_COUNT:
            break

    logger.info(f"✅ 抓取到 {len(news_list)} 条最新新闻")
    return news_list

def select_random_news(news_list, count=10):
    import random
    return random.sample(news_list, min(len(news_list), count))
