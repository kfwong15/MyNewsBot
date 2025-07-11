import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

# 列表页地址
LISTING_URL = "https://www.thestar.com.my/news/latest"
# 文章 URL 正则：/news/<category>/YYYY/MM/DD/<slug>
ARTICLE_REGEX = re.compile(r'href="(/news/[^"]+?/\d{4}/\d{2}/\d{2}/[^"]+)"')
# 最少需要抓取的文章数
MIN_COUNT = 10
# 域名拼接
BASE_DOMAIN = "https://www.thestar.com.my"

def fetch_news():
    try:
        resp = requests.get(LISTING_URL, timeout=10)
        resp.raise_for_status()
        logger.info(f"列表页请求成功: {LISTING_URL}")
    except Exception as e:
        logger.error(f"列表页请求失败: {e}", exc_info=True)
        return []

    html = resp.text
    # 正则提取所有文章路径
    paths = ARTICLE_REGEX.findall(html)
    # 去重并只保留前 MIN_COUNT 条
    seen = []
    for p in paths:
        if p not in seen:
            seen.append(p)
        if len(seen) >= MIN_COUNT:
            break

    news = []
    for path in seen:
        full_url = urljoin(BASE_DOMAIN, path)
        try:
            art = requests.get(full_url, timeout=10)
            art.raise_for_status()
            soup = BeautifulSoup(art.text, 'html.parser')

            # 标题优先用 OpenGraph 元
            og_title = soup.find('meta', property='og:title')
            title = og_title['content'].strip() if og_title and og_title.get('content') else ""
            if not title:
                # 回退到 <h1>
                h1 = soup.find('h1')
                title = h1.get_text(strip=True) if h1 else "（无法获取标题）"

            # 图片优先用 OpenGraph 元
            og_img = soup.find('meta', property='og:image')
            image = og_img['content'].strip() if og_img and og_img.get('content') else None

            news.append({
                "title": title,
                "link": full_url,
                "image": image
            })
            logger.info(f"抓取详情：{title}")

        except Exception as e:
            logger.warning(f"详情页请求失败 {full_url}: {e}")

    logger.info(f"✅ 共抓取到 {len(news)} 条新闻（预期 {MIN_COUNT}）")
    return news

def select_random_news(news_list, count=10):
    import random
    return random.sample(news_list, min(len(news_list), count))
