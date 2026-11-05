@echo off
chcp 65001 > nul
echo ⏳ [1/4] Проверка и инициализация базы данных SQLite...
python -c "from models import Base, engine; Base.metadata.create_all(engine); print('✅ База данных SQLite готова.')"

echo ⏳ [2/4] Запуск парсера RSS-потоков...
python load_news.py

echo ⏳ [3/4] Запуск ИИ-анализаторов (spaCy NER & Sentiment)...
python nlp_anzer.py
python sent_lyzer.py

echo 🚀 [4/4] Запуск аналитического дашборда Streamlit...
streamlit run app.py
pause
