import requests
from bs4 import BeautifulSoup
import time

# 设置目标新闻网站的 URL
TARGET_URL = "https://www.bbc.com/news"

# 设置请求头，模拟浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def fetch_news(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[ERROR] 请求失败: {e}")
        return None

def parse_news(html):
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    # 根据 BBC 的结构提取新闻标题和链接
    for item in soup.select("a.gs-c-promo-heading"):
        title = item.get_text(strip=True)
        link = item.get("href")
        if link and not link.startswith("http"):
            link = "https://www.bbc.com" + link
        articles.append({"title": title, "link": link})
    
    return articles

def main():
    print("[INFO] 正在抓取新闻...")
    html = fetch_news(TARGET_URL)
    if html:
        news_list = parse_news(html)
        print(f"[INFO] 共抓取到 {len(news_list)} 条新闻：\n")
        for idx, news in enumerate(news_list, 1):
            print(f"{idx}. {news['title']}\n   链接: {news['link']}\n")
    else:
        print("[ERROR] 无法获取网页内容")

if __name__ == "__main__":
    while True:
        main()
        print("[INFO] 10分钟后再次抓取...\n")
        time.sleep(600)  # 每10分钟抓取一次
