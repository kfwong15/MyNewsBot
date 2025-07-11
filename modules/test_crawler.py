import os
import sys
import logging
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import news_crawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_crawler')

def test_category(category):
    logger.info(f"\n{'='*50}")
    logger.info(f"测试分类: {category}")
    logger.info(f"{'='*50}")

    news_crawler.NEWS_CATEGORIES = [category]
    results = news_crawler.fetch_news()

    logger.info(f"抓取结果: {len(results)} 条新闻")
    for i, news in enumerate(results[:5], 1):
        logger.info(f"\n--- 新闻 {i} ---")
        logger.info(f"标题: {news['title']}")
        logger.info(f"分类: {news['category']}")
        logger.info(f"链接: {news['link']}")

def main():
    load_dotenv()
    for category in news_crawler.NEWS_CATEGORIES:
        test_category(category)

if __name__ == "__main__":
    main()
