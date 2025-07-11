# modules/news_crawler.py

import requests
from bs4 import BeautifulSoup      # ← 确保这样写
import logging
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

NEWS_CATEGORIES = [
    "latest", "nation", "metro", "business", "tech", "lifestyle", "world"
]

BASE_DOMAIN = "https://www.thestar.com.my"
BASE_PATH = "/news/"
MIN_TOTAL_NEWS = 10

def fetch_news():
    all_news = []
    for category in NEWS_CATEGORIES:
        url = urljoin(BASE_DOMAIN, BASE_PATH + category)
        logger.info(f"抓取分类 {category}: {url}")
        try:
            resp = requests.get(url, timeout=10)
            logger.info(f" 状态码: {resp.status_code}")
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            # 按顺序尝试几个选择器
            for sel in (".listing__content", ".main-content-list__item", "article"):
                items = soup.select(sel)
                if items:
                    logger.info(f"  使用 `{sel}` 找到 {len(items)} 篇文章")
                    break
            else:
                logger.warning("  未匹配到任何文章节点")
                continue

            for art in items:
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

            if len(all_news) >= MIN_TOTAL_NEWS:
                break

        except Exception as e:
            logger.error(f"分类 {category} 抓取失败: {e}", exc_info=True)

    logger.info(f"共抓取到 {len(all_news)} 条新闻")
    return all_news

def select_random_news(news_list, count=10):
    import random
    return random.sample(news_list, min(len(news_list), count))
