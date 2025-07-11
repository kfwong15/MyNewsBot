import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

# 想抓取的分类列表
NEWS_CATEGORIES = [
    "latest", "nation", "metro", "business", "tech", "lifestyle", "world"
]

BASE_DOMAIN = "https://www.thestar.com.my"
BASE_PATH = "/news/"

# 最少期望抓取文章总量
MIN_TOTAL_NEWS = 10

def fetch_news():
    """
    按分类抓取新闻，包含标题、链接、图片、分类。
    """
    all_news = []

    for category in NEWS_CATEGORIES:
        url = urljoin(BASE_DOMAIN, BASE_PATH + category)
        logger.info(f"▶ 抓取分类 {category} → {url}")

        try:
            resp = requests.get(url, timeout=10)
            logger.info(f"  状态码: {resp.status_code}")
            if resp.status_code != 200:
                continue

            html_text = resp.text
            soup = BeautifulSoup(html_text, 'html.parser')

            # 依次尝试多个选择器
            selectors = [
                ".listing__content",
                ".main-content-list__item",
                "article",
            ]
            articles = []
            for sel in selectors:
                found = soup.select(sel)
                if found:
                    articles = found
                    logger.info(f"  使用选择器 `{sel}` 找到 {len(found)} 篇文章")
                    break

            if not articles:
                logger.warning(f"  ❌ 未匹配到任何文章")
                continue

            for art in articles:
                link_tag = art.find("a", href=True)
                title_tag = art.find(["h2", "h3", "h4"])
                img_tag = art.find("img")

                if not link_tag or not title_tag:
                    continue

                href = link_tag["href"]
                full_link = urljoin(BASE_DOMAIN, href)
                title = title_tag.get_text(strip=True)
                img_url = None
                if img_tag and img_tag.get("src"):
                    img_url = urljoin(BASE_DOMAIN, img_tag["src"])

                all_news.append({
                    "title": title,
                    "link": full_link,
                    "image": img_url,
                    "category": category
                })

            # 如果已达到最小总量，提前退出
            if len(all_news) >= MIN_TOTAL_NEWS:
                break

        except Exception as e:
            logger.error(f"  抓取 {category} 出错: {e}", exc_info=True)

    logger.info(f"✅ 共抓取 {len(all_news)} 条新闻")
    return all_news

def select_random_news(news_list, count=10):
    """
    从列表中随机选取 count 条新闻
    """
    import random
    return random.sample(news_list, min(count, len(news_list)))
