import os
import requests
import urllib3
from dotenv import load_dotenv
from models import SessionLocal, Article, Entity

# Отключаем SSL-проверку только при необходимости
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
BASE_API_URL = "https://platform-api2.max.ru"

if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось прочитать токен из файла .env!")
    exit(1)

def send_news_digest(chat_id):
    """Отправляет дайджест новостей по заданному чат-ID."""
    from models import SessionLocal, Article, Entity  # Импортируем здесь, чтобы не было циклических зависимостей

    with SessionLocal() as db:
        latest_articles = (
            db.query(Article).order_by(Article.id.desc()).limit(3).all()
        )
    
    if not latest_articles:
        return "📋 В базе данных пока нет новостей."

    message_text = "🎉 ЕЖЕДНЕВНЫЙ ИИ-ДАЙДЖЕСТ НОВОСТЕЙ 🎉\n\n"

    for idx, article in enumerate(latest_articles, start=1):
        mood_emoji = "😊" if article.sentiment_label == 'positive' else "😡" if article.sentiment_label == 'negative' else "😐"
        
        message_text += f"{idx}. {mood_emoji} *{article.title}* ({article.source})\n"
        
        entities = [ent.entity_text.replace(' ', '_') for ent in 
                   db.query(Entity).filter(Entity.article_id == article.id).limit(4)]
        
        tags = f"#{' #'.join(entities)}" if entities else ""
        message_text += f"🔗 Ссылка: {article.link}\n🏷️ Теги: {tags}\n\n"

    headers = {"Authorization": f"Bearer {BOT_TOKEN}"}
    payload = {
        "recipient": chat_id,
        "text": message_text,
        "parse_mode": "markdown",  # Для форматирования жирным/курсивом
    }

    response = requests.post(
        url=f"{BASE_API_URL}/bot/messages",
        json=payload,
        headers=headers,
        verify=False
    )

    if response.status_code != 200:
        raise Exception(f"Ошибка отправки: Код {response.status_code}, Ответ: {response.text}")
    
    return "🚀 Дайджест успешно отправлен!"

def get_chat_id():
    """
    Ждёт первое сообщение от пользователя и возвращает его chat_id.
    Это необходимо, так как бот не может сам инициировать диалог.
    """
    headers = {"Authorization": f"Bearer {BOT_TOKEN}"}

    while True:
        try:
            updates = requests.get(
                url=f"{BASE_API_URL}/getUpdates?timeout=60&offset=-1",
                headers=headers,
                timeout=75,
                verify=False
            ).json()
            
            if updates["result"]:
                first_update = updates["result"][-1]
                chat_id = first_update["message"]["chat"]["id"]
                print(f"✅ Получено обновление! Chat_ID: {chat_id}")
                return chat_id
                
            print("⏳ Бот ждёт вашего сообщения... Напишите что-нибудь в приложении MAX.")

        except KeyboardInterrupt:
            print("\nРабота бота прервана пользователем.")
            break
        except Exception as e:
            print(f"\uD83D\uDEAB Критическая ошибка получения обновлений: {e}")

if __name__ == "__main__":
    print("🛠 Запуск скрипта...")

    # Шаг 1: Ждём, когда пользователь напишет боту
    chat_id = get_chat_id()

    # Шаг 2: Отправляем дайджест
    if chat_id:
        result = send_news_digest(chat_id)
        print(result)

        print(f"Ответ от сервера: {response.text}")