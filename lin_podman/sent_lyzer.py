import spacy
import re
from models import SessionLocal, Article

# Загружаем модель русского языка
nlp = spacy.load("ru_core_news_sm")

# Расширенные списки ключевых корней в начальной форме
POSITIVE_WORDS = {"прорыв", "успех", "выиграть", "победа", "рост", "увеличить", "награда", "достижение", "спасти", "положительный", "радость", "открыть"}
NEGATIVE_WORDS = {"пожар", "взрыв", "уничтожить", "смерть", "погибнуть", "афера", "суд", "виновный", "миллион", "обогащение", "кража", "задержать", "кризис", "упасть"}

def calculate_sentiment(text):
    if not text:
        return 'neutral', 0.5
        
    doc = nlp(text.lower())
    pos_count = 0
    neg_count = 0
    
    for token in doc:
        if token.lemma_ in POSITIVE_WORDS:
            pos_count += 1
        if token.lemma_ in NEGATIVE_WORDS:
            neg_count += 1
            
    total = pos_count + neg_count
    if total == 0:
        return 'neutral', 0.5
        
    score = max(pos_count, neg_count) / total
    
    if pos_count > neg_count:
        return 'positive', float(score)
    elif neg_count > pos_count:
        return 'negative', float(score)
    else:
        return 'neutral', 0.5

def analyze_sentiment():
    db = SessionLocal()
    
    # Берем из базы статьи, которые еще НЕ проходили анализ или у которых сброшена тональность (None)
    articles_to_analyze = db.query(Article).filter(
        (Article.sentiment_label == None) | (Article.sentiment_label == 'neutral')
    ).all()
    
    if not articles_to_analyze:
        print("📝 Нет новых статей для анализа тональности.")
        db.close()
        return

    print(f"🧠 Начинаем лингвистический анализ настроения новостей. К обработке: {len(articles_to_analyze)} статей...\n")
    updated_count = 0

    for article in articles_to_analyze:
        text = article.title
        try:
            label, score = calculate_sentiment(text)
            
            # Обновляем поля нашей ORM-модели статьи
            article.sentiment_label = label
            article.sentiment_score = score
            updated_count += 1
            
            print(f"📌 ID {article.id} [{article.source}] -> {label.upper()} (Уверенность: {score:.2f})")
        except Exception as e:
            print(f"❌ Ошибка при анализе статьи ID {article.id}: {e}")
            
    db.commit()
    db.close()
    print(f"\n🎉 Переразметка успешно завершена! Обновлено статей: {updated_count}")

if __name__ == "__main__":
    analyze_sentiment()
