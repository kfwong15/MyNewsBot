import logging
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

logger = logging.getLogger('news_crawler')

# Google 新闻（中文）RSS，包含马来西亚新闻
RSS_FEED = "https://news.google.com/rss/search?q=马来西亚&hl=zh-CN&gl=MY&ceid=MY:zh-Hans"
MIN_COUNT = 10
CHINAPRESS_FEED = "https://www.chinapress.com.my/feed/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "DNT": "1",
}

def fetch_news() -> list[dict]:
    """
    抓取 Google 新闻 RSS（中文），返回清晰标题、干净内容、图片、链接。
    """
    try:
        resp = requests.get(RSS_FEED, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.error(f"RSS 请求失败 ({RSS_FEED}): {e}", exc_info=True)
        return []

    news = []
    seen = set()
    ns = {'media': 'http://search.yahoo.com/mrss/'}

    for item in root.findall('.//item'):
        title = item.findtext('title', '').strip()
        link  = item.findtext('link', '').strip()
        if not title or not link or link in seen:
            continue

        # 图片
        img = None
        thumb = item.find('media:thumbnail', ns)
        if thumb is not None and thumb.attrib.get('url'):
            img = thumb.attrib['url']
        else:
            mcont = item.find('media:content', ns)
            if mcont is not None and mcont.attrib.get('url'):
                img = mcont.attrib['url']

        # 内容清洗
        raw_desc = item.findtext('description', '').strip()
        soup = BeautifulSoup(raw_desc, 'html.parser')
        content = soup.get_text(separator=' ', strip=True)
        content = ''.join(c for c in content if c.isalnum() or c.isspace())

        news.append({
            "title":   ''.join(c for c in title if c.isalnum() or c.isspace()),
            "link":    link,
            "image":   img,
            "content": content
        })
        seen.add(link)
        if len(news) >= MIN_COUNT:
            break

    logger.info(f"✅ Google 中文新闻抓到 {len(news)} 条")
    return news

def select_random_news(news_list: list[dict], count: int = 10) -> list[dict]:
    import random
    return random.sample(news_list, min(len(news_list), count))


def fetch_chinapress_news(max_items: int = 30) -> list[dict]:
    """
    抓取中国报（Chinapress）RSS，尽量提取标题、链接、图片、简介。
    """
    def parse_from_feed() -> list[dict]:
        try:
            resp = requests.get(CHINAPRESS_FEED, headers=HEADERS, timeout=12)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as e:
            logger.error(f"RSS 请求失败 ({CHINAPRESS_FEED}): {e}", exc_info=True)
            return []

        results: list[dict] = []
        seen = set()
        ns = {
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'media': 'http://search.yahoo.com/mrss/'
        }

        for item in root.findall('.//item'):
            raw_title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            if not raw_title or not link or link in seen:
                continue

            raw_desc = item.findtext('description', '') or ''
            content_encoded = None
            content_node = item.find('content:encoded', ns)
            if content_node is not None and content_node.text:
                content_encoded = content_node.text

            html_block = content_encoded or raw_desc
            soup = BeautifulSoup(html_block, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            text_content = ''.join(c for c in text_content if c.isalnum() or c.isspace())

            image_url = None
            img = soup.find('img')
            if img and img.has_attr('src'):
                image_url = img['src']
            if not image_url:
                m_cont = item.find('media:content', ns)
                if m_cont is not None and m_cont.attrib.get('url'):
                    image_url = m_cont.attrib['url']
                else:
                    m_thumb = item.find('media:thumbnail', ns)
                    if m_thumb is not None and m_thumb.attrib.get('url'):
                        image_url = m_thumb.attrib['url']

            title = ''.join(c for c in raw_title if c.isalnum() or c.isspace())

            results.append({
                'title': title,
                'link': link,
                'image': image_url,
                'content': text_content
            })

            seen.add(link)
            if len(results) >= max(MIN_COUNT, max_items):
                break

        return results

    def parse_from_homepage() -> list[dict]:
        url = "https://www.chinapress.com.my/"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"首页请求失败 ({url}): {e}", exc_info=True)
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        results: list[dict] = []
        seen = set()

        # 宽松遍历所有 <a>，过滤域名与标题长度
        for a in soup.select('a'):
            href = (a.get('href') or '').strip()
            title = a.get_text(strip=True)
            if not href or not title:
                continue
            # 统一转绝对链接
            if href.startswith('/'):
                href = 'https://www.chinapress.com.my' + href
            if not href.startswith('http'):
                continue
            if 'chinapress.com.my' not in href:
                continue
            if len(title) < 6:
                continue
            if href in seen:
                continue
            seen.add(href)
            results.append({
                'title': ''.join(c for c in title if c.isalnum() or c.isspace()),
                'link': href,
                'image': None,
                'content': ''
            })
            if len(results) >= max_items:
                break

        return results

    # 先尝试 RSS，再回退首页 HTML 解析
    rss_results = parse_from_feed()
    if rss_results:
        logger.info(f"✅ 中国报抓到 {len(rss_results)} 条（RSS）")
        return rss_results
    html_results = parse_from_homepage()
    logger.info(f"✅ 中国报抓到 {len(html_results)} 条（HTML）")
    return html_results
