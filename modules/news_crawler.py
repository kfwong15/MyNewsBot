import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
import json
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

BASE_DOMAIN = "https://www.thestar.com.my"
LATEST_PAGE = urljoin(BASE_DOMAIN, "/news/latest/")
MIN_COUNT = 10


def fetch_rss_feed_url() -> str:
    """
    先从最新页面 <link rel="alternate" type="application/rss+xml"> 提取 RSS 地址，
    如果提取失败，返回默认 RSS 源。
    """
    try:
        resp = requests.get(LATEST_PAGE, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        link_tag = soup.find('link', rel='alternate', type='application/rss+xml')
        if link_tag and link_tag.get('href'):
            feed_url = urljoin(BASE_DOMAIN, link_tag['href'])
            logger.info(f"找到 RSS 源: {feed_url}")
            return feed_url
    except Exception as e:
        logger.warning(f"RSS 源获取失败: {e}")
    # 备用 RSS（可能随时失效，请手动检查）
    default = "https://www.thestar.com.my/rss/news/latest.rss"
    logger.info(f"使用默认 RSS 源: {default}")
    return default


def parse_rss(feed_url: str) -> list:
    """
    抓取并解析 RSS，返回最多 MIN_COUNT 条新闻项。
    """
    try:
        resp = requests.get(feed_url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.error(f"RSS 请求或解析失败: {e}", exc_info=True)
        return []

    news = []
    seen = set()
    for item in root.findall('.//item'):
        title = item.findtext('title', '').strip()
        link = item.findtext('link', '').strip()
        if not title or not link or link in seen:
            continue

        # 尝试 <enclosure> 和 media:content
        img = None
        enc = item.find('enclosure')
        if enc is not None and 'url' in enc.attrib:
            img = urljoin(BASE_DOMAIN, enc.attrib['url'])
        else:
            m = item.find('{http://search.yahoo.com/mrss/}content')
            if m is not None and 'url' in m.attrib:
                img = urljoin(BASE_DOMAIN, m.attrib['url'])

        news.append({"title": title, "link": link, "image": img})
        seen.add(link)
        if len(news) >= MIN_COUNT:
            break

    logger.info(f"从 RSS 获得 {len(news)} 条新闻")
    return news


def parse_jsonld() -> list:
    """
    解析页面中的 JSON-LD ItemList，作为 RSS 失败的后备。
    """
    try:
        resp = requests.get(LATEST_PAGE, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        logger.error(f"页面请求失败: {e}", exc_info=True)
        return []

    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '')
        except:
            continue

        # 寻找 ItemList
        if isinstance(data, dict) and data.get('@type') == 'ItemList':
            news = []
            for elem in data.get('itemListElement', [])[:MIN_COUNT]:
                it = elem.get('item', {})
                title = it.get('headline', '').strip()
                link  = it.get('url', '').strip()
                img   = None
                im    = it.get('image')
                if isinstance(im, dict):
                    img = im.get('url')
                elif isinstance(im, str):
                    img = im

                if title and link:
                    news.append({"title": title, "link": link, "image": img})
            logger.info(f"从 JSON-LD 获得 {len(news)} 条新闻")
            return news

    logger.warning("未在页面找到 JSON-LD ItemList")
    return []


def fetch_news() -> list:
    """
    主逻辑：先尝试 RSS，若不足 MIN_COUNT，再用 JSON-LD 后备。
    """
    feed = fetch_rss_feed_url()
    news = parse_rss(feed)
    if len(news) < MIN_COUNT:
        logger.info("RSS 条数不足，尝试 JSON-LD 后备")
        _json = parse_jsonld()
        # 合并去重
        exists = {n['link'] for n in news}
        for j in _json:
            if len(news) >= MIN_COUNT:
                break
            if j['link'] not in exists:
                news.append(j)
    return news


def select_random_news(news_list: list, count: int = 10) -> list:
    import random
    return random.sample(news_list, min(len(news_list), count))
