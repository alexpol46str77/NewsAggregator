from models import Base, engine
import load_news
import nlp_anzer
import sent_lyzer

print("⏳ Шаг 1: Создаем структуру таблиц в PostgreSQL...")
Base.metadata.create_all(engine)
print("✅ Таблицы успешно созданы!")

print("\n⏳ Шаг 2: Запускаем парсер RSS-лент ТАСС, РИА и РБК...")
if hasattr(load_news, "fetch_and_save_news"):
    load_news.fetch_and_save_news()
elif hasattr(load_news, "load_news"):
    load_news.load_news()

print("\n⏳ Шаг 3: Запускаем ИИ-анализатор сущностей spaCy...")
# 🎯 Исправили имя модуля на nlp_anzer!
if hasattr(nlp_anzer, "analyze_stored_articles"):
    nlp_anzer.analyze_stored_articles()

print("\n⏳ Шаг 4: Запускаем текстовый анализатор тональности...")
if hasattr(sent_lyzer, "analyze_sentiment"):
    sent_lyzer.analyze_sentiment()

print("\n🎉 Все таблицы созданы, и данные ИИ успешно загружены в Postgres!")
