import openai
import os
import logging
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ai_assistant')

# 配置DeepSeek客户端
def get_ai_client():
    return openai.OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE', 'https://api.deepseek.com/v1')
    )

def ask_ai(question, model="deepseek-chat", max_tokens=1024):
    """向DeepSeek AI提问"""
    try:
        client = get_ai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业、友好的中文AI助手，专门回答马来西亚相关新闻和问题。"},
                {"role": "user", "content": question}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI请求失败: {e}", exc_info=True)
        return "⚠️ 暂时无法处理您的请求，请稍后再试"

def summarize_webpage(url, model="deepseek-chat", max_tokens=512):
    """总结网页内容"""
    try:
        # 获取网页内容
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 提取主要内容 - 根据网站结构调整
        content_elements = soup.select('article p, .article-body p, .story-content p')
        content = " ".join([p.text.strip() for p in content_elements[:20]])[:10000]  # 限制长度
        
        # 创建总结提示
        prompt = f"请用中文总结以下文章的主要内容，不超过200字:\n{content}"
        
        # 获取AI总结
        client = get_ai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业编辑，擅长总结新闻内容。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"总结文章失败: {e}", exc_info=True)
        return "⚠️ 无法总结此文章内容"

def translate_text(text, target_language="中文", model="deepseek-chat"):
    """翻译文本到目标语言"""
    try:
        client = get_ai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"你是一个专业翻译，将以下文本翻译成{target_language}，保持专业术语准确。"},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"翻译失败: {e}", exc_info=True)
        return "⚠️ 翻译时出错"

if __name__ == "__main__":
    # 测试AI功能
    question = "马来西亚今天有什么重要新闻？"
    print("提问:", question)
    print("回答:", ask_ai(question))
    
    # 测试文章总结
    test_url = "https://www.thestar.com.my/news/nation"
    print("\n总结:", summarize_webpage(test_url))
    
    # 测试翻译
    text = "Good morning, how are you today?"
    print("\n翻译:", translate_text(text))
