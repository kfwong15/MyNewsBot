import openai
import os
import logging
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ai_assistant')

# Configure OpenAI client
def get_ai_client():
    return openai.OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE', 'https://api.deepseek.com/v1')
    )

def ask_ai(question, model="deepseek-chat", max_tokens=1024):
    """Ask AI a question"""
    try:
        client = get_ai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional, friendly AI assistant. Respond in Chinese."},
                {"role": "user", "content": question}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI request failed: {e}", exc_info=True)
        return "⚠️ Unable to process your request, please try again later"

def summarize_webpage(url, model="deepseek-chat", max_tokens=512):
    """Summarize webpage content"""
    try:
        # Fetch webpage content
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract main content - adjust based on site structure
        content_elements = soup.select('article p')
        content = " ".join([p.text.strip() for p in content_elements[:20]])[:10000]  # Limit length
        
        # Create summary prompt
        prompt = f"请用中文总结以下文章的主要内容，不超过200字:\n{content}"
        
        # Get summary from AI
        client = get_ai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional editor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to summarize article: {e}", exc_info=True)
        return "⚠️ Unable to summarize this article"

def translate_text(text, target_language="Chinese", model="deepseek-chat"):
    """Translate text to target language"""
    try:
        client = get_ai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the following text to {target_language}."},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        return "⚠️ Translation failed"

if __name__ == "__main__":
    # Test AI functions
    question = "马来西亚今天有什么重要新闻？"
    print("Question:", question)
    print("Answer:", ask_ai(question))
    
    # Test summarization
    test_url = "https://www.thestar.com.my/news/nation"
    print("\nSummary:", summarize_webpage(test_url))
    
    # Test translation
    text = "Hello, how are you today?"
    print("\nTranslation:", translate_text(text))
