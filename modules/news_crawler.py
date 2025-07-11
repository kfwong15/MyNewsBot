# modules/news_crawler.py

import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

BASE_DOMAIN = "https://www.thestar.com.my"
LISTING_URL = f"{BASE_DOMAIN}/news/latest"
# 匹配 /news/<category>/YYYY/MM/DD/<slug> 这种链接
ARTICLE_RE = re.compile(r'href="(/news/[^"]+/\d{4}/\d{2}/\d{2}/[^"]+)"')
MIN_COUNT  = 10

def get_article_details(url: str) -> tuple[str, str | None, str | None]:
    """
    请求文章详情页，解析：
      - 标题：<meta property="og:title"> 或 <h1>
      - 图片：<meta property="og:image">
      - 正文开头：首个长度>50的 <p>
    返回 (title, image_url, content_snippet)
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 标题
        tag_t = soup.find('meta', property='og:title')
        title = tag_t['content'].strip() if tag_t and tag_t.get('content') else ""
        if not title:
            h1 = soup.find('h1')
            title = h1.get_text(strip=True) if h1 else ""

        # 图片
        tag_i = soup.find('meta', property='og:image')
        image = tag_i['content'].strip() if tag_i and tag_i.get('content') else None

        # 正文开头
        content = None
        for p in soup.find_all('p'):
            txt = p.get_text(strip=True)
            if txt and len(txt) > 50:
                content = txt
                break

        return title, image, content

    except Exception as e:
        logger.warning(f"详情页解析失败 {url}: {e}")
        return "", None, None


def fetch_news() -> list[dict]:
    """
    1. 抓取列表页，正则抽取前 MIN_COUNT 篇文章 URL
    2. 逐篇请求详情页，提取 title/image/content
    """
    news = []
    try:
        resp = requests.get(LISTING_URL, timeout=10)
        resp.raise_for_status()
        paths = ARTICLE_RE.findall(resp.text)
    except Exception as e:
        logger.error(f"列表页请求失败 {LISTING_URL}: {e}", exc_info=True)
        return news

    # 去重并取前 MIN_COUNT
    seen = []
    for p in paths:
        if p not in seen:
            seen.append(p)
        if len(seen) >= MIN_COUNT:
            break

    # 逐篇抓详情
    for path in seen:
        full_url = urljoin(BASE_DOMAIN, path)
        title, image, content = get_article_details(full_url)
        if not title:
            continue
        news.append({
            "title": title,
            "link": full_url,
            "image": image,
            "content": content or ""
        })

    logger.info(f"✅ 共抓取到 {len(news)} 条新闻")
    return news


def select_random_news(news_list: list, count: int = 10) -> list:
    """
    从新闻列表中随机选取 count 条（若不够则全选）。
    """
    import random
    return random.sample(news_list, min(len(news_list), count))
