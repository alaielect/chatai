import telebot
import requests
import time
import os

# ----- تنظیمات اولیه -----
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')  # توکنی که از BotFather گرفتی رو اینجا بذار
RENDER_API_URL = "https://chatai-3-v2vk.onrender.com/chat"  # آدرس API که روی Render گذاشتی

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable not set!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# دیکشنری برای ذخیره وضعیت "در حال تایپ" هر کاربر
user_waiting_messages = {}

# ----- دستور start -----
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 *Welcome to the Smart Assistant Bot!*\n\n"
        "I'm an AI powered by the SmolLM model. You can ask me questions, and I'll try my best to help!\n\n"
        "✨ *Features:*\n"
        "• Answer questions\n"
        "• Help with tasks\n"
        "• Chat with a small but smart AI\n\n"
        "⚠️ *Important:*\n"
        "• Please communicate in *English* for the best results.\n"
        "• This bot is experimental, so responses might not always be perfect.\n\n"
        "Just send me a message to get started!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ----- دریافت پیام‌های معمولی -----
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    user_text = message.text

    # 1. ارسال پیام انیمیشن دار (نمایش "در حال تایپ")
    waiting_msg = bot.reply_to(message, "⏳ *Thinking...*", parse_mode='Markdown')
    user_waiting_messages[user_id] = waiting_msg.message_id

    # 2. ارسال درخواست به سرور Render
    try:
        payload = {
            "user_id": str(user_id),
            "message": user_text
        }
        response = requests.post(RENDER_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        bot_reply = response.json().get('reply', 'Sorry, I could not generate a response.')

    except requests.exceptions.RequestException as e:
        print(f"Error calling Render API: {e}")
        bot_reply = "⚠️ Sorry, my brain is not responding right now. Please try again later."

    # 3. پاک کردن پیام انتظار
    try:
        bot.delete_message(chat_id=user_id, message_id=user_waiting_messages[user_id])
    except:
        pass  # اگه پیام قبلاً پاک شده بود
    if user_id in user_waiting_messages:
        del user_waiting_messages[user_id]

    # 4. ارسال جواب نهایی
    bot.send_message(user_id, bot_reply, parse_mode='Markdown')

# ----- اجرای ربات -----
if __name__ == "__main__":
    print("Telegram bot is starting...")
    bot.infinity_polling()
