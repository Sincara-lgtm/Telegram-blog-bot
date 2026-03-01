import os
import requests
import feedparser
import random
from datetime import datetime
import google.generativeai as genai

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not CHANNEL_ID:
    raise ValueError("TELEGRAM_TOKEN или CHANNEL_ID не заданы!")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

sources = [
    "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "http://feeds.bbci.co.uk/news/rss.xml",
]

def get_news():
    all_entries = []
    for url in sources:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:5]:
                all_entries.append(f"- {entry.title}")
        except Exception:
            continue
    random.shuffle(all_entries)
    result = "\n".join(all_entries[:10])
    return result if result else "Сегодня новостей нет."

def generate_post(news_text):
    if not model:
        return "📰 Новости дня:\n" + news_text + "\n\n#news"
    prompt = f"""Ты — Алёна Ветлугина, 18-летняя девушка из Вологды, ведёшь интернациональный блог.

Вот главные новости мира сегодня:
{news_text}

Напиши пост для Telegram на английском языке в дружелюбном стиле:
- Заголовок жирным шрифтом (используй <b>теги</b>)
- 2-3 абзаца с комментариями
- Добавь 3-5 хештегов в конце
- Тон: лёгкий, но информативный
"""
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        else:
            return "📰 Новости дня:\n" + news_text + "\n\n#news"
    except Exception:
        return "📰 Новости дня:\n" + news_text + "\n\n#news"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(text) > 4000:
        text = text[:4000] + "..."
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=data, timeout=15)
    return response.json()

def main():
    print(f"Запуск {datetime.now()}")
    news = get_news()
    print(f"Собрано новостей: {len(news)}")
    if model:
        post = generate_post(news)
        print("Пост сгенерирован через Gemini")
    else:
        post = "📄 Новости дня:\n" + news + "\n\n#news"
        print("Использован резервный формат")
    result = send_to_telegram(post)
    print(f"Результат отправки: {result}")

if __name__ == "__main__":
    main()
