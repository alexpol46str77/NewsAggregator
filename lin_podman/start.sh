#!/bin/bash
echo "⏳ 1. Запуск полной ИИ-инициализации и сбора новостей внутри контейнера..."
podman run --rm --net=host -v /home/alexpol/projects/NewsAggregatorApp/.env:/app/.env news_ai_app:latest python3 init_db.py

echo "⏳ 2. Перезапуск фонового контейнера веб-панели Streamlit..."
podman rm -f news_streamlit_app 2>/dev/null || true
podman run -d --name news_streamlit_app --net=host -v /home/alexpol/projects/NewsAggregatorApp/.env:/app/.env news_ai_app:latest

echo "🎉 Панель успешно запущена! Переходи по адресу http://127.0.0.1:8501"
