# modules/news_crawler.py

import asyncio
import logging
from urllib.parse import urljoin

from playwright.async_api import async_playwright

logger = logging.getLogger('news_crawler')

BASE_URL    = "https://www.thestar.com.my/news/latest"
BASE_DOMAIN = "https://www.thestar.com.my"
MIN_COUNT   = 10

async def _fetch():
    news = []
    async with async_playwright() as p:
        # 避免沙箱问题并增加稳定性
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await browser.new_page()

        # 改为 DOMContentLoaded，延长超时
        await page.goto(BASE_URL, timeout=60000, wait_until='domcontentloaded')
        # 滚动触发懒加载
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        # 等待 article 元素出现
        await page.wait_for_selector('article', timeout=15000)
        items = await page.query_selector_all('article')

        for art in items[:MIN_COUNT]:
            # 标题
            title_el = await art.query_selector('h1, h2, h3')
            title = (await title_el.inner_text()).strip() if title_el else ""

            # 链接
            a_el = await art.query_selector('a[href]')
            href = (await a_el.get_attribute('href')).strip() if a_el else ""
            link = href if href.startswith('http') else urljoin(BASE_DOMAIN, href)

            # 图片
            img_el = await art.query_selector('img')
            img = (await img_el.get_attribute('src')).strip() if img_el else None

            # 内容摘要
            p_el = await art.query_selector('p')
            content = (await p_el.inner_text()).strip() if p_el else ""

            if title and link:
                news.append({
                    "title": title,
                    "link": link,
                    "image": img,
                    "content": content
                })

        await browser.close()

    logger.info(f"✅ Playwright 抓取到 {len(news)} 条新闻")
    return news

async def fetch_news() -> list[dict]:
    return await _fetch()

def select_random_news(news_list: list[dict], count: int = 10) -> list[dict]:
    import random
    return random.sample(news_list, min(count, len(news_list)))
