import re
from models import SessionLocal, Article

# 🎯 Локальный мини-словарь эмоциональных маркеров для русского языка
# Позволяет определять тональность мгновенно и без интернета
POSITIVE_WORDS = {'приветствовать', 'успех', 'развитие', 'победа', 'рост', 'выиграть', 'одобрить', 'согласие', 'сотрудничество', 'положительный', 'лидер', 'инновации', 'улучшить', 'открыть', 'создать', 'помощь'}
NEGATIVE_WORDS = {'ошибка', 'санкции', 'кризис', 'падение', 'запретить', 'блокировка', 'удар', 'атака', 'конфликт', 'ущерб', 'сбой', 'авария', 'проблема', 'отклонить', 'суд', 'арест', 'штраф', 'убыток', 'взрыв', 'ранен'}

print("⏳ Загрузка автономного текстового анализатора тональности...")
print("✅ Лингвистическая модель успешно инициализирована!")

def calculate_sentiment(text):
    # Приводим текст к нижнему регистру и разбиваем на отдельные слова
    words = re.findall(r'[а-яёa-z]+', text.lower())
    if not words:
        return 'neutral', 0.5
        
    pos_count = sum(1 for word in words if word in POSITIVE_WORDS)
    neg_count = sum(1 for word in words if word in NEGATIVE_WORDS)
    
    total = pos_count + neg_count
    if total == 0:
        return 'neutral', 0.5
        
    # Рассчитываем уверенность и метку
    score = max(pos_count, neg_count) / total
    if pos_count > neg_count:
        return 'positive', float(score)
    elif neg_count > pos_count:
        return 'negative', float(score)
    else:
        return 'neutral', 0.5

def analyze_sentiment():
    db = SessionLocal()
    
    # 1. Берем из базы статьи, которые еще НЕ проходили анализ тональности
    articles_to_analyze = db.query(Article).filter(Article.sentiment_label == None).all()
    
    if not articles_to_analyze:
        print("📝 Нет новых статей для анализа тональности.")
        db.close()
        return

    print(f"🕵️‍♂️ Начинаем локальный анализ настроения новостей. К обработке: {len(articles_to_analyze)}\n")
    
    updated_count = 0

    for article in articles_to_analyze:
        # Анализируем заголовок новости
        text = article.title
        
        try:
            label, score = calculate_sentiment(text)
            
            # Обновляем поля нашей ORM-модели статьи
            article.sentiment_label = label
            article.sentiment_score = score
            
            updated_count += 1
            print(f"📰 ID {article.id} [{article.source}] -> {label.upper()} (Уверенность: {score:.2f})")
            
        except Exception as err:
            print(f"⚠️ Ошибка обработки статьи ID {article.id}: {err}")

    # Фиксируем изменения в PostgreSQL на Linux Mint
    if updated_count > 0:
        try:
            db.commit()
            print(f"\n🎉 Анализ тональности завершен!")
            print(f"✅ Успешно размечено новостей: {updated_count}")
        except Exception as e:
            db.rollback()
            print(f"❌ Ошибка при сохранении результатов в БД: {e}")
    
    db.close()

if __name__ == "__main__":
    analyze_sentiment()
