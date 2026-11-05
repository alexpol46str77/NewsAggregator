import feedparser
from models import SessionLocal, Article

# Наш хитрый обход фильтров для ссылок
HTTP = "https://"

RSS_SOURCES = {
    "ТАСС": "http://tass.ru/rss/v2.xml",
    "РИА Новости": "http://ria.ru/export/rss2/index.xml",
    "Интерфакс": "http://www.interfax.ru/rss.asp",
    "Коммерсантъ": "http://www.kommersant.ru/RSS/news.xml",
    "Ведомости": "http://www.vedomosti.ru/rss/news.xml",
    "Российская газета": "http://rg.ru/xml/index.xml",
    "РБК": "http://gspace.rbc.ru/rbc/gspace/news_all.rss",
    "Лента.Ру": "http://lenta.ru/rss",
    "Фонтанка": "http://www.fontanka.ru/fontanka.rss",
    "Правительство РФ": "http://government.ru"
}

def fetch_and_save_news():
    # Открываем сессию подключения к PostgreSQL
    db = SessionLocal()
    
    print("⏳ Начинаем сбор новостей и сохранение в базу данных...\n")
    
    saved_count = 0
    skipped_count = 0
    
    for source_name, url in RSS_SOURCES.items():
        print(f"📡 Сканируем {source_name}...")
        feed = feedparser.parse(url)
        
        # Забираем топ-5 самых свежих новостей из каждого источника
        for entry in feed.entries[:5]:
            title = entry.get("title", "Без заголовка")
            link = entry.get("link", "#")
            published = entry.get("published", "Время не указано")
            summary = entry.get("summary", "Описание отсутствует")
            
            # Проверяем, нет ли уже такой ссылки в нашей базе данных
            exists = db.query(Article).filter(Article.link == link).first()
            if exists:
                skipped_count += 1
                continue  # Пропускаем, чтобы не плодить дубликаты!
            
            # Создаем объект нашей ORM-модели
            new_article = Article(
                source=source_name,
                title=title,
                summary=summary,
                link=link,
                published_at=published
            )
            
            # Добавляем в очередь на сохранение
            db.add(new_article)
            saved_count += 1
            
    # Фиксируем изменения в базе данных одной транзакцией
    try:
        db.commit()
        print(f"\n🎉 Сбор завершен успешно!")
        print(f"✅ Сохранено новых новостей в базу: {saved_count}")
        print(f"⏭️ Пропущено дубликатов (уже были в базе): {skipped_count}")
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при сохранении в БД: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fetch_and_save_news()
