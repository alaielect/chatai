from flask import Flask, request, jsonify
from llama_cpp import Llama
import urllib.request
import os
import re
import requests
from bs4 import BeautifulSoup
import json
import time

app = Flask(__name__)

# ========== تنظیمات مدل ==========
# استفاده از Qwen2.5-0.5B (بسیار قوی‌تر از SmolLM)
MODEL_URL = "https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-IQ4_XS.gguf"
MODEL_PATH = "model.gguf"

# دانلود مدل (فقط یک بار)
if not os.path.exists(MODEL_PATH):
    print("📥 Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("✅ Model downloaded!")

# لود مدل
print("🔄 Loading model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=1024,         # افزایش context برای پاسخ‌های طولانی‌تر
    n_threads=2,
    verbose=False
)
print("✅ Model loaded!")

# ========== توابع جستجوی اینترنت ==========

def search_web(query, max_results=2):
    """جستجوی اینترنتی و برگرداندن نتایج"""
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=max_results):
            try:
                # استخراج متن از صفحه
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                # حذف تگ‌های غیرضروری
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()
                text = soup.get_text()
                # پاکسازی متن
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                # محدود کردن طول متن
                text = text[:500]
                results.append(f"🔍 از {url}:\n{text}")
            except:
                results.append(f"🔗 {url} (متن قابل استخراج نبود)")
        return "\n\n".join(results) if results else "نتیجه‌ای یافت نشد."
    except Exception as e:
        print(f"Search error: {e}")
        return None

def needs_web_search(prompt):
    """تشخیص اینکه آیا سوال نیاز به جستجوی اینترنت دارد"""
    keywords = ['خبر', 'امروز', 'الان', 'اخرین', 'جدید', 'قیمت', 
                'هوا', 'وضعیت', 'result', 'score', 'news', 'today', 
                'current', 'latest', 'weather', 'price', 'update']
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in keywords)

# ========== مدیریت تاریخچه ==========
user_histories = {}
MAX_HISTORY = 5

def get_system_prompt(web_context=None):
    base_prompt = """You are Qwen, a helpful AI assistant. 
- Answer in the same language as the user's question.
- Keep answers concise but informative.
- Be accurate and honest. Say "I don't know" if unsure.
- Don't make up information."""
    
    if web_context:
        base_prompt += f"\n\n🔍 SEARCH RESULTS:\n{web_context}\n\nUse this information to answer. If relevant, mention the source."
    
    return base_prompt

# ========== API اصلی ==========
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    user_message = data.get('message', '')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    print(f"📩 User {user_id}: {user_message}")

    # چک کردن نیاز به جستجوی اینترنت
    web_context = None
    if needs_web_search(user_message):
        print(f"🌐 Searching web for: {user_message}")
        web_context = search_web(user_message)
        if web_context:
            print("✅ Search completed")

    # مدیریت تاریخچه
    if user_id not in user_histories:
        user_histories[user_id] = []

    # اضافه کردن پیام جدید
    user_histories[user_id].append(f"User: {user_message}")
    
    # محدود کردن تاریخچه
    history = user_histories[user_id][-MAX_HISTORY:]
    
    # ساخت پرامپت
    prompt = get_system_prompt(web_context) + "\n" + "\n".join(history) + "\nAssistant:"

    # گرفتن پاسخ از مدل
    try:
        output = llm(
            prompt,
            max_tokens=200,
            temperature=0.7,
            stop=["User:", "\n\n", "Assistant:", "<|im_end|>"]
        )
        bot_reply = output['choices'][0]['text'].strip()
        
        # اگه جواب خالی بود یا خیلی کوتاه
        if not bot_reply or len(bot_reply) < 2:
            bot_reply = "I'm not sure how to answer that. Could you rephrase?"
        
        # اضافه کردن پاسخ به تاریخچه
        user_histories[user_id].append(f"Assistant: {bot_reply}")
        
        # پاکسازی تاریخچه کاربران قدیمی
        if len(user_histories) > 100:
            oldest = next(iter(user_histories))
            del user_histories[oldest]
        
        print(f"🤖 Response: {bot_reply[:100]}...")
        return jsonify({'reply': bot_reply})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'reply': 'Sorry, an error occurred. Please try again.'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': 'Qwen2.5-0.5B'})

@app.route('/reset', methods=['POST'])
def reset():
    """ریست کردن تاریخچه یک کاربر"""
    data = request.json
    user_id = data.get('user_id')
    if user_id and user_id in user_histories:
        del user_histories[user_id]
        return jsonify({'status': 'history cleared'})
    return jsonify({'status': 'no history found'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Server starting on port {port}")
    app.run(host='0.0.0.0', port=port)
