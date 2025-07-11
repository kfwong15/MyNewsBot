import os, sys, logging
from dotenv import load_dotenv

# 将项目根目录加入路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules import news_crawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_crawler')

def test_category(cat):
    logger.info(f"=== 测试分类: {cat} ===")
    news_crawler.NEWS_CATEGORIES = [cat]
    items = news_crawler.fetch_news()
    logger.info(f"抓取到 {len(items)} 条")
    for i, n in enumerate(items[:5], 1):
        logger.info(f"{i}. {n['title']} ({n['link']})")

if __name__ == "__main__":
    load_dotenv()
    for c in news_crawler.NEWS_CATEGORIES:
        test_category(c)
