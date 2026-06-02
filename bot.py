from flask import Flask, request, jsonify
from llama_cpp import Llama
import urllib.request
import os
import re

app = Flask(__name__)

# 1. دانلود مدل (فقط یک بار)
MODEL_URL = "https://huggingface.co/common-archive/SmolLM-135M-Instruct-Q8_0-gguf/resolve/main/SmolLM-135M-Instruct_Q8_0.gguf"
MODEL_PATH = "model.gguf"

if not os.path.exists(MODEL_PATH):
    print("Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Model downloaded!")

# 2. لود مدل با llama.cpp
print("Loading model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=512,          # طول تاریخچه (حافظه)
    n_threads=2,
    verbose=False
)
print("Model loaded!")

# 3. ذخیره‌ی ساده‌ی تاریخچه (با محدودیت)
user_histories = {}
MAX_HISTORY = 3  # حداکثر 3 پیام آخر رو نگه دار تا از ترکیدن سرور جلوگیری بشه

def get_system_prompt():
    return """You are a helpful AI assistant. Answer concisely and accurately in the same language as the user's question. Keep responses short (maximum 50 tokens)."""

def truncate_history(history):
    """محدود کردن تعداد پیام‌ها برای جلوگیری از مصرف زیاد توکن"""
    return history[-MAX_HISTORY:] if len(history) > MAX_HISTORY else history

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    user_message = data.get('message', '')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    # گرفتن تاریخچه یا ساختن یه تاریخچه جدید
    if user_id not in user_histories:
        user_histories[user_id] = []

    # اضافه کردن پیام جدید کاربر به تاریخچه
    user_histories[user_id].append(f"User: {user_message}")

    # محدود کردن تاریخچه
    history = truncate_history(user_histories[user_id])
    prompt = get_system_prompt() + "\n" + "\n".join(history) + "\nAssistant:"

    # گرفتن جواب از مدل
    output = llm(
        prompt,
        max_tokens=100,
        temperature=0.7,
        stop=["User:", "\n\n", "Assistant:"]
    )
    bot_reply = output['choices'][0]['text'].strip()

    # اضافه کردن جواب ربات به تاریخچه
    user_histories[user_id].append(f"Assistant: {bot_reply}")
    user_histories[user_id] = truncate_history(user_histories[user_id])

    # پاکسازی تاریخچه‌های قدیمی (اختیاری، برای جلوگیری از انباشت)
    if len(user_histories) > 100:
        # حذف قدیمی‌ترین کاربر
        oldest_user = next(iter(user_histories))
        del user_histories[oldest_user]

    return jsonify({'reply': bot_reply})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
