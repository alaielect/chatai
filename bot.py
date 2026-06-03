from flask import Flask, request, jsonify
from llama_cpp import Llama
import urllib.request
import os
import json

app = Flask(__name__)

# ---------- تنظیمات مدل ----------
MODEL_URL = "https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-IQ4_XS.gguf"
MODEL_PATH = "model.gguf"

# دانلود مدل اگر نباشد
if not os.path.exists(MODEL_PATH):
    print("📥 Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("✅ Model downloaded!")

# لود مدل با تنظیمات بهینه
print("🔄 Loading model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=512,          # محدود کردن حافظه
    n_threads=1,        # کاهش مصرف CPU
    verbose=False
)
print("✅ Model loaded!")

# ---------- مدیریت توکن و تاریخچه ----------
user_histories = {}
MAX_HISTORY = 3           # فقط 3 پیام آخر رو نگه دار
MAX_RESPONSE_TOKENS = 150  # جواب طولانی نشه

def get_system_prompt():
    return """You are a helpful AI assistant. 
Answer concisely and directly. Keep responses short (max 2-3 sentences).
Answer in the same language as the user.
If you don't know, say "I don't know".
Don't make up information."""

def truncate_history(history):
    """محدود کردن تعداد پیام‌ها برای جلوگیری از مصرف زیاد توکن"""
    if len(history) > MAX_HISTORY * 2:
        return history[-MAX_HISTORY * 2:]
    return history

# ---------- API اصلی ----------
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    user_message = data.get('message', '')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    print(f"📩 User {user_id}: {user_message}")
    
    # مدیریت تاریخچه
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    # محدود کردن تاریخچه
    user_histories[user_id] = truncate_history(user_histories[user_id])
    
    # ساخت پرامپت با تاریخچه
    system_prompt = get_system_prompt()
    conversation = user_histories[user_id].copy()
    conversation.append(f"User: {user_message}")
    prompt = system_prompt + "\n" + "\n".join(conversation[-MAX_HISTORY:]) + "\nAssistant:"
    
    # گرفتن پاسخ از مدل
    try:
        output = llm(
            prompt,
            max_tokens=MAX_RESPONSE_TOKENS,
            temperature=0.7,
            stop=["User:", "\n\n", "Assistant:", "<|im_end|>"]
        )
        bot_reply = output['choices'][0]['text'].strip()
        
        # اگه جواب خالی بود یا خیلی کوتاه
        if not bot_reply or len(bot_reply) < 2:
            bot_reply = "I'm not sure how to answer that. Could you rephrase?"
        
        # به روز رسانی تاریخچه
        user_histories[user_id].append(f"User: {user_message}")
        user_histories[user_id].append(f"Assistant: {bot_reply}")
        user_histories[user_id] = truncate_history(user_histories[user_id])
        
        # پاکسازی کاربران قدیمی برای جلوگیری از مصرف بیش از حد حافظه
        if len(user_histories) > 50:
            oldest = next(iter(user_histories))
            del user_histories[oldest]
        
        print(f"🤖 Response: {bot_reply[:100]}...")
        return jsonify({'reply': bot_reply})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'reply': 'Sorry, an error occurred. Please try again.'})

# ---------- مسیرهای کمکی ----------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok', 
        'model': 'Qwen2.5-0.5B',
        'active_users': len(user_histories)
    })

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
