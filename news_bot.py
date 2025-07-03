import os
import time
import re
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import random

# ====== 配置 ======
# 从环境变量获取 Telegram 信息
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 验证环境变量是否设置
if not TG_BOT_TOKEN or not TG_CHAT_ID:
    print("❌ 错误：请设置 TG_BOT_TOKEN 和 TG_CHAT_ID 环境变量")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

# ✅ 设置 Selenium 浏览器
def setup_browser():
    try:
        # 配置 Chrome 选项
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
        
        # 移除自动化特征
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置 WebDriver
        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 执行 JavaScript 来隐藏自动化特征
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"❌ 浏览器初始化失败: {str(e)}")
        return None

# ✅ 使用浏览器抓取页面
def fetch_with_browser(url, driver):
    try:
        # 模拟人类浏览行为
        driver.get(url)
        
        # 随机滚动页面
        for _ in range(random.randint(2, 5)):
            scroll_height = random.randint(300, 1000)
            driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            time.sleep(random.uniform(0.5, 2.0))
        
        # 随机移动鼠标
        action = webdriver.ActionChains(driver)
        action.move_by_offset(random.randint(10, 100), random.randint(10, 100)).perform()
        time.sleep(random.uniform(0.3, 1.5))
        
        # 等待页面加载
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 获取页面源码
        page_source = driver.page_source
        return page_source
    except Exception as e:
        print(f"❌ 浏览器抓取失败: {str(e)}")
        return None

# ✅ 中国报新闻抓取
def fetch_chinapress(driver):
    try:
        url = "https://www.chinapress.com.my/"
        page_source = fetch_with_browser(url, driver)
        
        if not page_source:
            return ["❌ 中国报抓取失败：无法获取网页内容"]
        
        soup = BeautifulSoup(page_source, 'html.parser')
        news_items = []
        
        # 查找头条新闻
        top_news = soup.select_one('div.top-story')
        if top_news:
            title_tag = top_news.find('h1', class_='post-title')
            if title_tag and title_tag.a:
                title = title_tag.get_text(strip=True)
                link = title_tag.a['href']
                news_items.append(f"📰 <b>中国报头条</b>\n📌 {title}\n🔗 {link}")
        
        # 查找其他新闻
        for article in soup.select('div.post-box:not(.top-story)'):
            if len(news_items) >= 3:  # 最多3条
                break
                
            title_tag = article.find('h3', class_='post-title')
            if title_tag and title_tag.a:
                title = title_tag.get_text(strip=True)
                link = title_tag.a['href']
                news_items.append(f"📰 <b>中国报</b>\n📌 {title}\n🔗 {link}")
                
        return news_items if news_items else ["❌ 中国报抓取失败：未找到新闻内容"]
        
    except Exception as e:
        return [f"❌ 中国报抓取失败：{str(e)}"]

# ✅ 东方日报新闻抓取
def fetch_oriental(driver):
    try:
        url = "https://www.orientaldaily.com.my"
        page_source = fetch_with_browser(url, driver)
        
        if not page_source:
            # 尝试备用RSS源
            rss_url = "https://www.orientaldaily.com.my/rss"
            response = requests.get(rss_url, timeout=10)
            if response.status_code == 200:
                return parse_rss(response.text, "东方日报")
            else:
                return ["❌ 东方日报抓取失败：无法获取网页内容"]
        
        soup = BeautifulSoup(page_source, 'html.parser')
        news_items = []
        
        # 查找头条新闻
        top_news = soup.select_one('div.top-news')
        if top_news:
            title_tag = top_news.find('h1')
            if title_tag and title_tag.a:
                title = title_tag.get_text(strip=True)
                link = title_tag.a['href']
                if not link.startswith('http'):
                    link = f"https://www.orientaldaily.com.my{link}"
                news_items.append(f"📰 <b>东方日报头条</b>\n📌 {title}\n🔗 {link}")
        
        # 查找其他新闻
        for article in soup.select('div.news-list'):
            if len(news_items) >= 3:  # 最多3条
                break
                
            title_tag = article.find('h2')
            if title_tag and title_tag.a:
                title = title_tag.get_text(strip=True)
                link = title_tag.a['href']
                if not link.startswith('http'):
                    link = f"https://www.orientaldaily.com.my{link}"
                news_items.append(f"📰 <b>东方日报</b>\n📌 {title}\n🔗 {link}")
                
        return news_items if news_items else ["❌ 东方日报抓取失败：未找到新闻内容"]
        
    except Exception as e:
        return [f"❌ 东方日报抓取失败：{str(e)}"]

# ✅ RSS解析备用方案
def parse_rss(xml_content, source_name):
    try:
        from xml.etree import ElementTree as ET
        
        root = ET.fromstring(xml_content)
        news_items = []
        
        # 解析RSS/XML
        for item in root.findall('.//item'):
            if len(news_items) >= 3:  # 最多3条
                break
                
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            
            if title and link:
                news_items.append(f"📰 <b>{source_name}</b>\n📌 {title}\n🔗 {link}")
        
        return news_items if news_items else [f"❌ {source_name} RSS解析失败：无有效内容"]
    
    except Exception as e:
        return [f"❌ {source_name} RSS解析失败：{str(e)}"]

# ✅ Telegram消息发送
def send_telegram(message):
    try:
        # 清理消息中的无效字符
        clean_msg = re.sub(r'[^\x20-\x7E\u4E00-\u9FFF]', '', message)
        
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": clean_msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(API_URL, json=payload, timeout=25)
        response.raise_for_status()
        
        print(f"✅ 消息发送成功: {clean_msg[:50]}...")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram API请求失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 发送消息时发生未知错误: {str(e)}")
        return False

# ✅ 主函数
def main():
    print("="*50)
    print("开始新闻推送任务")
    print("="*50)
    
    # 初始化浏览器
    print("\n初始化浏览器...")
    driver = setup_browser()
    if not driver:
        print("❌ 无法初始化浏览器，退出程序")
        sys.exit(1)
    
    try:
        # 获取新闻
        print("\n抓取中国报新闻...")
        chinapress_news = fetch_chinapress(driver)
        print(f"找到 {len([n for n in chinapress_news if '❌' not in n])} 条中国报新闻")
        
        print("\n抓取东方日报新闻...")
        oriental_news = fetch_oriental(driver)
        print(f"找到 {len([n for n in oriental_news if '❌' not in n])} 条东方日报新闻")
        
        all_news = chinapress_news + oriental_news
        
        # 发送新闻
        success_count = 0
        for news in all_news:
            if "❌" not in news:  # 只发送成功抓取的新闻
                max_retries = 3
                for attempt in range(max_retries):
                    if send_telegram(news):
                        success_count += 1
                        time.sleep(random.uniform(1, 3))  # 随机消息间隔
                        break
                    elif attempt < max_retries - 1:
                        wait_time = 3 + attempt * 2
                        print(f"等待{wait_time}秒后重试 ({attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
        
        print("\n" + "="*50)
        print(f"新闻推送完成! 成功发送 {success_count}/{len(all_news)} 条新闻")
        print("="*50)
        
        # 如果有任何失败，非零退出码
        if success_count < len(all_news):
            sys.exit(1)
            
    finally:
        # 确保浏览器关闭
        driver.quit()
        print("\n浏览器已关闭")

if __name__ == "__main__":
    main()
