from flask import Flask, request, jsonify
from llama_cpp import Llama
import urllib.request
import os
import json
from search import web_search, needs_web_search

app = Flask(__name__)

# ---------- تنظیمات مدل ----------
MODEL_URL = "https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-IQ4_XS.gguf"
MODEL_PATH = "model.gguf"

# دانلود مدل اگر نباشد
if not os.path.exists(MODEL_PATH):
    print("📥 Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("✅ Model downloaded!")

# لود مدل
print("🔄 Loading model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=512,
    n_threads=1,
    verbose=False
)
print("✅ Model loaded!")

# ---------- مدیریت تاریخچه ----------
user_histories = {}
MAX_HISTORY = 3

def get_system_prompt(web_context=None):
    """ساخت پرامپت سیستم با یا بدون نتیجه جستجو"""
    base_prompt = """You are a helpful AI assistant. 
Answer in the same language as the user.
Keep answers concise and accurate.
If you don't know something, say so honestly.
"""
    
    if web_context:
        base_prompt += f"""
🔍 **WEB SEARCH RESULTS (use this information):**
{web_context}

Use the above search results to answer the user's question.
If the search results are relevant, use them.
If not, use your own knowledge.
Always mention your sources if you use search results.
"""
    else:
        base_prompt += """
If the user asks for latest news, weather, or current information, 
you can suggest them to ask more specifically or use web search.
"""
    
    return base_prompt

# ---------- API اصلی ----------
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    user_message = data.get('message', '')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    print(f"📩 User {user_id}: {user_message}")
    
    # ---------- مرحله 1: چک کردن نیاز به جستجو ----------
    web_context = None
    if needs_web_search(user_message):
        print(f"🌐 Searching web for: {user_message}")
        web_context = web_search(user_message)
        if web_context:
            print("✅ Search results found")
        else:
            print("⚠️ No search results")
    
    # ---------- مرحله 2: مدیریت تاریخچه ----------
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    # محدود کردن تاریخچه
    if len(user_histories[user_id]) > MAX_HISTORY * 2:
        user_histories[user_id] = user_histories[user_id][-MAX_HISTORY * 2:]
    
    # ---------- مرحله 3: ساخت پرامپت ----------
    system_prompt = get_system_prompt(web_context)
    
    # ساخت تاریخچه مکالمه
    conversation = []
    for msg in user_histories[user_id]:
        conversation.append(msg)
    
    conversation.append(f"User: {user_message}")
    prompt = system_prompt + "\n" + "\n".join(conversation[-MAX_HISTORY:]) + "\nAssistant:"
    
    # ---------- مرحله 4: دریافت پاسخ از مدل ----------
    try:
        output = llm(
            prompt,
            max_tokens=200,
            temperature=0.7,
            stop=["User:", "\n\n", "Assistant:", "<|im_end|>"]
        )
        bot_reply = output['choices'][0]['text'].strip()
        
        if not bot_reply or len(bot_reply) < 2:
            bot_reply = "I'm not sure how to answer that. Could you rephrase?"
        
        # اضافه کردن به تاریخچه
        user_histories[user_id].append(f"User: {user_message}")
        user_histories[user_id].append(f"Assistant: {bot_reply}")
        
        print(f"🤖 Response: {bot_reply[:100]}...")
        return jsonify({'reply': bot_reply})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'reply': 'Sorry, an error occurred. Please try again.'})

# ---------- مسیرهای کمکی ----------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': 'Qwen2.5-0.5B', 'search': 'SearXNG'})

@app.route('/reset', methods=['POST'])
def reset():
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
