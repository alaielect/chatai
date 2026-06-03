from flask import Flask, request, jsonify
from llama_cpp import Llama
import urllib.request
import os
import json
from duckduckgo_search import DDGS  # <-- اضافه شده

app = Flask(__name__)

# ---------- تنظیمات مدل ----------
# استفاده از مدل سبک IQ4_XS که قبلا جواب داده
MODEL_URL = "https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-IQ4_XS.gguf"
MODEL_PATH = "model.gguf"

# دانلود مدل اگر نباشد
if not os.path.exists(MODEL_PATH):
    print("📥 Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("✅ Model downloaded!")

# لود مدل با تنظیمات بهینه (رم کمتر)
print("🔄 Loading model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=512,           # کاهش حافظه مصرفی
    n_threads=1,         # کاهش تردها
    verbose=False
)
print("✅ Model loaded!")

# ---------- تابع جستجوی اینترنت (DuckDuckGo) ----------
def search_web(query):
    """
    جستجو در اینترنت با DuckDuckGo و برگرداندن نتایج
    """
    try:
        print(f"🌐 Searching DuckDuckGo for: {query}")
        with DDGS() as ddgs:
            # گرفتن 2 نتیجه برتر
            results = list(ddgs.text(query, max_results=2))
            
            if not results:
                return None
            
            # ساخت متن جستجو برای ارسال به مدل
            search_context = "Here is the latest information from the web:\n\n"
            for i, r in enumerate(results, 1):
                title = r.get('title', 'No title')
                body = r.get('body', 'No content')
                href = r.get('href', '#')
                search_context += f"{i}. **{title}**\n   {body}\n   Source: {href}\n\n"
            
            return search_context
    except Exception as e:
        print(f"Search error: {e}")
        return None

def needs_web_search(prompt):
    """
    تشخیص نیاز به جستجو بر اساس کلمات کلیدی
    """
    keywords = ['خبر', 'امروز', 'الان', 'جدید', 'قیمت', 'هوا', 'وضعیت',
                'news', 'today', 'current', 'latest', 'weather', 'price', 
                'score', 'result', 'update', 'breaking', 'now']
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in keywords)

# ---------- مدیریت حافظه چت ----------
user_histories = {}
MAX_HISTORY = 3

# ---------- API اصلی ----------
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    user_message = data.get('message', '')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    print(f"📩 User {user_id}: {user_message}")
    
    # --- مرحله 1: جستجوی اینترنت اگر نیاز باشد ---
    web_context = None
    if needs_web_search(user_message):
        web_context = search_web(user_message)
    
    # --- مرحله 2: مدیریت تاریخچه ---
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    # اضافه کردن پیام کاربر
    user_histories[user_id].append(f"User: {user_message}")
    
    # --- مرحله 3: ساخت پرامپت (با یا بدون نتیجه جستجو) ---
    history = user_histories[user_id][-MAX_HISTORY:]
    
    # پرامپت پایه
    system_prompt = """You are a helpful AI assistant. 
Answer in the same language as the user.
Be concise and accurate.
"""
    
    # اضافه کردن نتایج جستجو اگر وجود داشته باشد
    if web_context:
        system_prompt += f"\n\n{web_context}\nUse the above search results to answer. Be accurate and mention sources if relevant.\n"
    
    prompt = system_prompt + "\n" + "\n".join(history) + "\nAssistant:"
    
    # --- مرحله 4: گرفتن پاسخ از مدل ---
    try:
        output = llm(
            prompt,
            max_tokens=200,
            temperature=0.7,
            stop=["User:", "\n\n", "Assistant:", "<|im_end|>"]
        )
        bot_reply = output['choices'][0]['text'].strip()
        
        # اگر جواب خالی بود
        if not bot_reply:
            bot_reply = "I'm not sure how to answer that. Could you rephrase?"
        
        # اضافه کردن پاسخ به تاریخچه
        user_histories[user_id].append(f"Assistant: {bot_reply}")
        
        # محدود کردن تاریخچه
        if len(user_histories[user_id]) > MAX_HISTORY * 2:
            user_histories[user_id] = user_histories[user_id][-MAX_HISTORY * 2:]
        
        # پاکسازی کاربران قدیمی
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
    return jsonify({'status': 'ok', 'model': 'Qwen2.5-0.5B', 'web_search': 'DuckDuckGo'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Server starting on port {port}")
    app.run(host='0.0.0.0', port=port)
