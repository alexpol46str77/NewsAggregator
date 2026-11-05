import spacy
from models import SessionLocal, Article, Entity

print("⏳ Загрузка ИИ-модели русского языка ru_core_news_sm...")
# Загружаем скачанную нейросетевую модель
nlp = spacy.load("ru_core_news_sm")
print("✅ ИИ-модель успешно загружена!")

def analyze_stored_articles():
    db = SessionLocal()
    
    # 1. Вытаскиваем из базы статьи, для которых мы ЕЩЕ НЕ извлекали сущности
    # Проверяем это по отсутствию записей в таблице entities для данной статьи
    articles_to_analyze = db.query(Article).all()
    
    if not articles_to_analyze:
        print("📝 Нет новых статей для анализа.")
        db.close()
        return

    print(f"🕵️‍♂️ Начинаем лингвистический анализ статей. Всего к обработке: {len(articles_to_analyze)}\n")
    
    entities_saved = 0

    for article in articles_to_analyze:
        # Проверяем, не анализировали ли мы эту статью раньше
        existing_entities = db.query(Entity).filter(Entity.article_id == article.id).first()
        if existing_entities:
            continue # Пропускаем уже обработанную статью
            
        # Объединяем заголовок и краткое описание для максимальной точности ИИ
        text_to_analyze = f"{article.title}. {article.summary or ''}"
        
        # Прогоняем текст через нейросеть spaCy
        doc = nlp(text_to_analyze)
        
        # Множество для исключения дубликатов сущностей в рамках одной статьи
        seen_entities = set()
        
        # Перебираем найденные сущности (имена, бренды, локации)
        for ent in doc.ents:
            # Нам интересны только 3 ключевых типа:
            # PER - Персоны (Путин, Кличко...)
            # LOC - Локации (Финляндия, Брянск, Москва...)
            # ORG - Организации (МИД, Apple, Google, Сбербанк...)
            if ent.label_ in ["PER", "LOC", "ORG"]:
                entity_key = (ent.text.strip(), ent.label_)
                
                if entity_key not in seen_entities:
                    seen_entities.add(entity_key)
                    
                    # Создаем запись для нашей второй SQL-таблицы entities
                    new_entity = Entity(
                        article_id=article.id,
                        entity_text=ent.text.strip(),
                        entity_label=ent.label_
                    )
                    db.add(new_entity)
                    entities_saved += 1
                    
        print(f"📈 Статья ID {article.id} [{article.source}]: Найдено сущностей: {len(seen_entities)}")

    # Сохраняем все найденные сущности в базу данных
    try:
        db.commit()
        print(f"\n🎉 Анализ завершен!")
        print(f"✅ Успешно извлечено и записано в базу сущностей: {entities_saved}")
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при сохранении сущностей в БД: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze_stored_articles()
