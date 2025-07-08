import os
import sys
import logging
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import news_crawler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_crawler')

def test_category(category):
    """测试单个分类的抓取"""
    logger.info(f"\n{'='*50}")
    logger.info(f"测试分类: {category}")
    logger.info(f"{'='*50}")
    
    # 修改 NEWS_CATEGORIES 只包含测试的分类
    news_crawler.NEWS_CATEGORIES = {category: news_crawler.NEWS_CATEGORIES[category]}
    
    # 执行抓取
    results = news_crawler.fetch_news()
    
    logger.info(f"抓取结果: {len(results)} 条新闻")
    for i, news in enumerate(results[:3], 1):
        logger.info(f"\n--- 新闻 {i} ---")
        logger.info(f"标题: {news['title']}")
        logger.info(f"分类: {news['category']}")
        logger.info(f"链接: {news['link']}")

def main():
    load_dotenv()
    
    # 测试所有分类
    for category in news_crawler.NEWS_CATEGORIES.keys():
        test_category(category)
    
    # 特别测试政治分类
    logger.info("\n额外测试政治分类...")
    test_category('politics')

if __name__ == "__main__":
    main()
