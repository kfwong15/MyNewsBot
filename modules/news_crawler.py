import re
import json
import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger('news_crawler')

BASE_DOMAIN     = "https://www.thestar.com.my"
LISTING_PAGE    = urljoin(BASE_DOMAIN, "/news/latest/")
OFFICIAL_RSS    = "https://www.thestar.com.my/rss/latest.rss"
GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/"
    "search?q=site:thestar.com.my/news/latest&hl=en-MY&gl=MY&ceid=MY:en"
)
MIN_COUNT       = 10
ARTICLE_REGEX   = re.compile(
    r'href="(/news/[^"]+?/\d{4}/\d{2}/\d{2}/[^"]+)"'
)


def fetch_rss(feed_url: str) -> list:
    items = []
    seen = set()
    try:
        resp = requests.get(feed_url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.warning(f"RSS 请求/解析失败: {feed_url} – {e}")
        return items

    for item in root.findall('.//item'):
        title = item.findtext('title', '').strip()
        link  = item.findtext('link',  '').strip()
        if not title or not link or link in seen:
            continue

        img = None
        desc = item.findtext('description', '')
        if desc:
            soup = BeautifulSoup(desc, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                img = img_tag['src']

        enc = item.find('enclosure')
        if not img and enc is not None and 'url' in enc.attrib:
            img = enc.attrib['url']
        else:
            m = item.find('{http://search.yahoo.com/mrss/}content')
            if not img and m is not None and 'url' in m.attrib:
                img = m.attrib['url']

        items.append({"title": title, "link": link, "image": img})
        seen.add(link)
        if len(items) >= MIN_COUNT:
            break

    logger.info(f"✅ RSS 抓到 {len(items)} 条 ({feed_url})")
    return items


def fetch_jsonld() -> list:
    out = []
    try:
        resp = requests.get(LISTING_PAGE, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        logger.warning(f"JSON-LD 页面请求失败: {e}")
        return out

    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or '')
        except:
            continue
        if isinstance(data, dict) and data.get('@type') == 'ItemList':
            for ele in data.get('itemListElement', [])[:MIN_COUNT]:
                it    = ele.get('item', {})
                title = it.get('headline','').strip()
                link  = it.get('url','').strip()
                if not title or not link:
                    continue
                raw = it.get('image')
                img = raw.get('url') if isinstance(raw, dict) else raw
                out.append({"title": title, "link": link, "image": img})
            logger.info(f"✅ JSON-LD 抓到 {len(out)} 条")
            return out

    logger.info("⚠️ 未找到 JSON-LD ItemList")
    return out


def fetch_by_regex() -> list:
    out = []
    try:
        resp = requests.get(LISTING_PAGE, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"列表页请求失败: {e}")
        return out

    paths = ARTICLE_REGEX.findall(resp.text)
    seen = []
    for p in paths:
        if p not in seen:
            seen.append(p)
        if len(seen) >= MIN_COUNT:
            break

    for path in seen:
        url = urljoin(BASE_DOMAIN, path)
        try:
            r2 = requests.get(url, timeout=10)
            r2.raise_for_status()
            sp = BeautifulSoup(r2.text, 'html.parser')
        except Exception:
            continue

        tag_t = sp.find('meta', property='og:title')
        title = (tag_t['content'].strip() if tag_t and tag_t.get('content') 
                 else sp.find('h1').get_text(strip=True) if sp.find('h1') 
                 else '')
        tag_i = sp.find('meta', property='og:image')
        img = tag_i['content'].strip() if tag_i and tag_i.get('content') else None

        if title and url:
            out.append({"title": title, "link": url, "image": img})

    logger.info(f"✅ 正则+详情抓到 {len(out)} 条")
    return out


def get_og_image(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        tag = soup.find('meta', property='og:image')
        if tag and tag.get('content'):
            return tag['content']
    except Exception as e:
        logger.warning(f"获取 og:image 失败: {url} – {e}")
    return None


def get_article_content(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup.find_all('p'):
            text = tag.get_text(strip=True)
            if text and len(text) > 50:
                return text
    except Exception as e:
        logger.warning(f"获取正文失败: {url} – {e}")
    return None


def fetch_news() -> list:
    out = fetch_rss(OFFICIAL_RSS)
    if len(out) < MIN_COUNT:
        more = fetch_rss(GOOGLE_NEWS_RSS)
        links = {n['link'] for n in out}
        for m in more:
            if len(out) >= MIN_COUNT:
                break
            if m['link'] not in links:
                out.append(m)

    if len(out) < MIN_COUNT:
        more = fetch_jsonld()
        links = {n['link'] for n in out}
        for m in more:
            if len(out) >= MIN_COUNT:
                break
            if m['link'] not in links:
                out.append(m)

    if len(out) < MIN_COUNT:
        more = fetch_by_regex()
        links = {n['link'] for n in out}
        for m in more:
            if len(out) >= MIN_COUNT:
                break
            if m['link'] not in links:
                out.append(m)

    for item in out:
        if not item.get('image'):
            item['image'] = get_og_image(item['link'])
        item['content'] = get_article_content(item['link'])

    logger.info(
        f"🔚 最终共抓到 {len(out)} 条新闻，带图 {sum(1 for i in out if i.get('image'))} 条"
    )
    return out


def select_random_news(news_list: list, count: int = 10) -> list:
    import random
    return random.sample(news_list, min(len(news_list), count))
