# modules/news_crawler.py

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

# 你想要抓取的分类
NEWS_CATEGORIES = [
    "latest", "nation", "metro", "business", "tech", "lifestyle", "world"
]

# 站点基础地址
BASE_DOMAIN = "https://www.thestar.com.my"
BASE_PATH = "/news/"

# 每个分类至少尝试抓取多少条新闻
MIN_NEWS_PER_CATEGORY = 10

def fetch_news():
    all_news = []

    for category in NEWS_CATEGORIES:
        url = urljoin(BASE_DOMAIN, BASE_PATH + category)
        logger.info(f"开始抓取分类 {category}: {url}")

        try:
            resp = requests.get(url, timeout=10)
            logger.info(f" → 状态码: {resp.status_code}")
            if resp.status_code != 200:
                continue

            # 如果页面内容突然为空，可打印前 500 字符查看结构
            html = resp.text
            if len(html) < 1000:
                logger.warning(f"页面内容可能不完整（长度 {len(html)}），请手动检查")

            soup = BeautifulSoup(html, 'html.parser')

            # 尝试一系列选择器，直到匹配到文章列表
            selectors = [
                ".listing__content",           # 旧版
                ".main-content-list__item",    # 常见新版
                ".section-content__item",
                "article",                     # 通用 article 标签
                ".teaser-item",                # 可能的 teaser
            ]
            articles = []
            for sel in selectors:
                found = soup.select(sel)
                if found:
                    articles = found
                    logger.info(f" 使用选择器 “{sel}” 找到 {len(found)} 篇文章")
                    break

            if not articles:
                logger.warning(f" 未找到任何文章，请检查选择器或页面结构")
                continue

            # 遍历文章节点，抽取 title/link/img
            for art in articles:
                # 找第一个 <a>、<h2> 或 <h3>
                link_tag = art.find("a", href=True)
                title_tag = art.find(["h2", "h3", "h4"])
                img_tag = art.find("img")

                if not link_tag or not title_tag:
                    continue

                href = link_tag["href"]
                full_link = urljoin(BASE_DOMAIN, href)
                title = title_tag.get_text(strip=True)
                img_url = img_tag["src"] if img_tag and img_tag.get("src") else None
                if img_url:
                    img_url = urljoin(BASE_DOMAIN, img_url)

                all_news.append({
                    "title": title,
                    "link": full_link,
                    "image": img_url,
                    "category": category
                })

            logger.info(f" 分类 {category} 抓取到 {len(articles)} 篇文章，解析后有效新闻 {len(all_news)} 条")

            # 早停：如果当前分类已抓到足够多新闻，可跳到下一个
            if len(all_news) >= MIN_NEWS_PER_CATEGORY * len(NEWS_CATEGORIES):
                logger.info("已达到理想抓取数量，停止继续抓取")
                break

        except Exception as e:
            logger.error(f" 抓取分类 {category} 出错: {e}", exc_info=True)

    logger.info(f"共抓取到 {len(all_news)} 条新闻")
    return all_news

def select_random_news(news_list, count=10):
    """从抓到的新闻中随机挑选 count 条"""
    import random
    if not news_list:
        return []
    return random.sample(news_list, min(count, len(news_list)))
