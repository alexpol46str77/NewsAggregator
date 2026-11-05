import feedparser

# Список ОФИЦИАЛЬНЫХ рабочих RSS-лент

# Базовый домен для всех ссылок
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

print("⏳ Запуск тестового парсинга новостных лент...\n")

for source_name, url in RSS_SOURCES.items():
    print(f"=== 📰 Получаем новости из источника: {source_name} ===")
    
    # Скачиваем и парсим RSS-ленту
    feed = feedparser.parse(url)
    
    # Берем топ-3 самых свежих новостей из ленты
    top_entries = feed.entries[:3]
    
    if not top_entries:
        print("❌ Не удалось получить новости или лента пуста.\n")
        continue
        
    for idx, entry in enumerate(top_entries, 1):
        title = entry.get("title", "Без заголовка")
        link = entry.get("link", "#")
        published = entry.get("published", "Время не указано")
        summary = entry.get("summary", "Описание отсутствует")
        
        print(f"{idx}. 📌 {title}")
        print(f"   📅 Дата: {published}")
        print(f"   📝 Кратко: {summary[:120]}...") 
        print(f"   🔗 Ссылка: {link}\n")
    
    print("-" * 50)
