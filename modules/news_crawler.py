# modules/news_crawler.py

import re
import json
import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

BASE_DOMAIN    = "https://www.thestar.com.my"
LISTING_PAGE   = urljoin(BASE_DOMAIN, "/news/latest/")
OFFICIAL_RSS   = "https://www.thestar.com.my/rss/latest.rss"
GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/"
    "search?q=site:thestar.com.my/news/latest&hl=en-MY&gl=MY&ceid=MY:en"
)
MIN_COUNT      = 10
ARTICLE_REGEX  = re.compile(
    r'href="(/news/[^"]+?/\d{4}/\d{2}/\d{2}/[^"]+)"'
)


def fetch_rss(feed_url: str) -> list:
    """尝试抓官方 RSS / Google News RSS"""
    try:
        resp = requests.get(feed_url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.warning(f"RSS 请求或解析失败: {feed_url} － {e}")
        return []

    items = []
    seen = set()
    # 官方和 Google RSS 都用 <item>
    for item in root.findall('.//item'):
        title = item.findtext('title', default='').strip()
        link  = item.findtext('link',  default='').strip()
        if not title or not link or link in seen:
            continue

        # 尝试从 <description> 中提取图片（Google RSS）
        img = None
        desc = item.findtext('description', default='')
        if desc:
            soup = BeautifulSoup(desc, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                img = img_tag['src']

        # 尝试 <enclosure> 或 media:content（官方 RSS）
        if not img:
            enc = item.find('enclosure')
            if enc is not None and 'url' in enc.attrib:
                img = enc.attrib['url']
            else:
                m = item.find('{http://search.yahoo.com/mrss/}content')
                if m is not None and 'url' in m.attrib:
                    img = m.attrib['url']

        items.append({"title": title, "link": link, "image": img})
        seen.add(link)
        if len(items) >= MIN_COUNT:
            break

    logger.info(f"✅ RSS 抓到 {len(items)} 条 ({feed_url})")
    return items


def fetch_jsonld() -> list:
    """从 listing 页面里找 JSON-LD ItemList（后备）"""
    try:
        resp = requests.get(LISTING_PAGE, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        logger.warning(f"JSON-LD 页面请求失败: {e}")
        return []

    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or '')
        except:
            continue
        if data.get('@type') == 'ItemList':
            out = []
            for ele in data.get('itemListElement', [])[:MIN_COUNT]:
                it    = ele.get('item', {})
                title = it.get('headline','').strip()
                link  = it.get('url','').strip()
                if not title or not link:
                    continue
                # image 有时是 str 有时是 dict
                raw = it.get('image')
                img = raw.get('url') if isinstance(raw, dict) else raw
                out.append({"title": title, "link": link, "image": img})
            logger.info(f"✅ JSON-LD 抓到 {len(out)} 条")
            return out
    logger.info("⚠️ 未找到 JSON-LD ItemList")
    return []


def fetch_by_regex() -> list:
    """正则抽取 listing 页面所有文章 URL，再请求详情页抓 og:meta"""
    try:
        resp = requests.get(LISTING_PAGE, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"详情页列表请求失败: {e}")
        return []

    found = ARTICLE_REGEX.findall(resp.text)
    seen = []
    for p in found:
        if p not in seen:
            seen.append(p)
        if len(seen) >= MIN_COUNT:
            break

    out = []
    for path in seen:
        url = urljoin(BASE_DOMAIN, path)
        try:
            r2 = requests.get(url, timeout=10)
            r2.raise_for_status()
            sp = BeautifulSoup(r2.text, 'html.parser')
        except:
            continue

        # 抓标题
        title_tag = sp.find('meta', property='og:title')
        title = title_tag['content'].strip() if title_tag else (
            sp.find('h1').get_text(strip=True) if sp.find('h1') else ''
        )
        # 抓图片
        img_tag = sp.find('meta', property='og:image')
        img = img_tag['content'].strip() if img_tag else None

        if title and url:
            out.append({"title": title, "link": url, "image": img})

    logger.info(f"✅ 正则+详情页 抓到 {len(out)} 条")
    return out


def fetch_news() -> list:
    """
    抓新闻主流程：依次尝试
    1. 官方 RSS
    2. Google News RSS
    3. JSON-LD
    4. 正则+详情页
    """
    # 1) 官网 RSS
    out = fetch_rss(OFFICIAL_RSS)
    if len(out) < MIN_COUNT:
        # 2) Google News RSS
        more = fetch_rss(GOOGLE_NEWS_RSS)
        # 合并去重
        links = {n['link'] for n in out}
        for m in more:
            if len(out) >= MIN_COUNT:
                break
            if m['link'] not in links:
                out.append(m)

    if len(out) < MIN_COUNT:
        # 3) JSON-LD
        more = fetch_jsonld()
        links = {n['link'] for n in out}
        for m in more:
            if len(out) >= MIN_COUNT:
                break
            if m['link'] not in links:
                out.append(m)

    if len(out) < MIN_COUNT:
        # 4) 正则+详情页
        more = fetch_by_regex()
        links = {n['link'] for n in out}
        for m in more:
            if len(out) >= MIN_COUNT:
                break
            if m['link'] not in links:
                out.append(m)

    logger.info(f"🔚 最终共抓到 {len(out)} 条新闻")
    return out


def select_random_news(news_list: list, count: int = 10) -> list:
    import random
    return random.sample(news_list, min(len(news_list), count))
