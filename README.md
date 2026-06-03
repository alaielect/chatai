# AI API with Web Search

یک API هوش مصنوعی با قابلیت جستجوی اینترنت، مبتنی بر مدل Qwen2.5-0.5B.

## امکانات

- 🤖 پاسخگویی هوشمند با Qwen2.5-0.5B
- 🌐 جستجوی خودکار اینترنت برای سوالات خبری و به‌روز
- 💾 حفظ تاریخچه مکالمه
- 🚀 سبک و قابل اجرا روی Render با 512MB رم

## راه‌اندازی در Render

1. Create new Web Service
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python bot.py`
4. Instance Type: Free

## API Endpoints

### POST /chat
```json
{
  "user_id": "user123",
  "message": "What is the weather today?"
}
