import os
import requests
import feedparser
import random
from datetime import datetime
import google.generativeai as genai

# Получаем настройки из переменных окружения (секретов GitHub)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Проверяем, что все ключи загружены (если нет – выводим ошибку)
if not TELEGRAM_TOKEN or not CHANNEL_ID:
    raise ValueError("❌ TELEGRAM_TOKEN или CHANNEL_ID не заданы!")

# Инициализация Gemini (если ключ есть)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
    print("⚠️ GEMINI_API_KEY не задан, посты генерироваться не будут.")

def get_news():
    """Собирает заголовки новостей из международных RSS-лент"""
    sources = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "https://feeds.npr.org/1001/rss.xml"
    ]
    
    all_entries = []
    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:  # Берём по 5 из каждого
                all_entries.append(f"- {entry.title}")
        except:
            continue
    
    # Перемешиваем и берём 10 случайных
    random.shuffle(all_entries)
    return "\n".join(all_entries[:10])

def generate_post(news_text):
    """Генерирует пост через Gemini в стиле Алёны"""
    if not model:
        return "Новости дня:\n" + news_text + "\n\n#news"
    
    prompt = f"""Ты — Алёна Ветлугина, 18-летняя девушка из Вологды, ведёшь интернациональный блог.
    
Вот главные новости мира сегодня:
{news_text}

Напиши пост для Telegram на английском языке в дружелюбном стиле:
- Заголовок жирным шрифтом (используй <b>теги</b>)
- 2-3 абзаца с комментариями
- Добавь 3-5 хештегов в конце
- Тон: лёгкий, но информативный
"""
    response = model.generate_content(prompt)
    return response.text

def send_to_telegram(text):
    """Отправляет сообщение в Telegram-канал"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Telegram ограничивает длину сообщения 4096 символами
    if len(text) > 4000:
        text = text[:4000] + "..."
    
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    response = requests.post(url, data=data)
    return response.json()

def main():
    print(f"🤖 Запуск {datetime.now()}")
    
    # 1. Собираем новости
    news = get_news()
    print(f"📰 Собрано новостей: {len(news)}")
    
    # 2. Генерируем пост (или используем заглушку, если нет Gemini)
    if model:
        post = generate_post(news)
        print("✨ Пост сгенерирован через Gemini")
    else:
        post = "📰 Новости дня:\n" + news + "\n\n#news"
        print("📝 Использован резервный формат (без Gemini)")
    
    # 3. Отправляем в Telegram
    result = send_to_telegram(post)
    print(f"📨 Результат отправки: {result}")

if __name__ == "__main__":
    main()
