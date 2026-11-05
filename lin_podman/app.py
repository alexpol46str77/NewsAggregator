import streamlit as st
import pandas as pd
import smtplib
import os
from sqlalchemy import text
from models import engine
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib3

st.set_page_config(page_title="ИИ-Агрегатор Новостей PRO", layout="wide")
st.title("📰 Умный ИИ-Агрегатор Новостей")
st.caption("Анализ тональности, извлечение именованных сущностей (spaCy) и фильтрация в реальном времени")

# --- 📊 ФУНКЦИЯ ЗАГРУЗКИ ДАННЫХ ИЗ POSTGRESQL ---
@st.cache_data(ttl=60) # Кэшируем данные на 1 минуту, чтобы не спамить базу при каждом клике
def load_dashboard_data():
    with engine.connect() as conn:
        # Загружаем все статьи
        df_articles = pd.read_sql("SELECT * FROM articles ORDER BY id DESC", conn)
        # Загружаем все сущности для фильтра
        df_entities = pd.read_sql("SELECT * FROM entities", conn)
    return df_articles, df_entities

try:
    df_articles, df_entities = load_dashboard_data()
except Exception as e:
    st.error(f"❌ Не удалось подключиться к PostgreSQL на Linux Mint: {e}")
    st.stop()

# --- 📈 БЛОК МЕТРИК СТАТИСТИКИ ---
st.write("---")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Всего новостей в БД", len(df_articles))
with col_m2:
    st.metric("Извлечено ИИ-сущностей", len(df_entities))
with col_m3:
    pos_count = len(df_articles[df_articles['sentiment_label'] == 'positive'])
    st.metric("😊 Позитивных новостей", pos_count)
with col_m4:
    neg_count = len(df_articles[df_articles['sentiment_label'] == 'negative'])
    st.metric("😡 Негативных новостей", neg_count)

# --- 🎛️ ПАНЕЛЬ ФИЛЬТРОВ В БОКОВОЙ ПАНЕЛИ ---
st.sidebar.header("🎯 Фильтрация новостей")

# 1. Фильтр по источникам
all_sources = ["Все источники"] + list(df_articles["source"].unique())
selected_source = st.sidebar.selectbox("Выбрать СМИ:", all_sources)

# 2. Фильтр по тональности
all_sentiments = ["Все настроения", "positive", "neutral", "negative"]
selected_sentiment = st.sidebar.selectbox("Тональность (ИИ):", all_sentiments)

# 3. Фильтр по именованным сущностям (spaCy PER, LOC, ORG)
# Собираем красивый список для селектора: "Имя (Тип)"
df_entities["display_name"] = df_entities["entity_text"] + " (" + df_entities["entity_label"] + ")"
all_entities = ["Все сущности"] + sorted(list(df_entities["display_name"].unique()))
selected_entity = st.sidebar.selectbox("Фильтр по персонам/брендам/локациям:", all_entities)

# --- 🧠 ЛОГИКА ФИЛЬТРАЦИИ DATAFRAME ---
filtered_df = df_articles.copy()

if selected_source != "Все источники":
    filtered_df = filtered_df[filtered_df["source"] == selected_source]

if selected_sentiment != "Все настроения":
    filtered_df = filtered_df[filtered_df["sentiment_label"] == selected_sentiment]

if selected_entity != "Все сущности":
    # Вытаскиваем чистый текст сущности из строки "Путин (PER)"
    pure_entity_text = selected_entity.split(" (")[0]
    # Находим ID всех статей, где упоминается эта сущность
    allowed_article_ids = df_entities[df_entities["entity_text"] == pure_entity_text]["article_id"].unique()
    # Фильтруем основной датафрейм новостей по этим ID
    filtered_df = filtered_df[filtered_df["id"].isin(allowed_article_ids)]

# --- 📰 ВЫВОД ЛЕНТЫ НОВОСТЕЙ ---
st.subheader(f"📋 Результаты фильтрации (Найдено статей: {len(filtered_df)})")

if filtered_df.empty:
    st.info("По вашему запросу новостей не найдено. Попробуйте сбросить фильтры.")
else:
    for idx, row in filtered_df.iterrows():
        # Подбираем эмодзи под настроение новости
        sent = row['sentiment_label']
        mood_emoji = "😊" if sent == 'positive' else "😡" if sent == 'negative' else "😐"
        
        # Рендерим красивую карточку новости
        with st.container():
            col_feed1, col_feed2 = st.columns([6, 1])
            with col_feed1:
                st.markdown(f"### {row['title']}")
                st.write(f"**Источник:** {row['source']} | **Дата RSS:** {row['published_at']}")
                if row['summary'] and row['summary'] != "Описание отсутствует":
                    st.write(row['summary'])
                st.markdown(f"[🔗 Читать первоисточник]({row['link']})")
                
                # Показываем, какие сущности ИИ нашел именно в этой новости
                this_article_entities = df_entities[df_entities["article_id"] == row["id"]]
                if not this_article_entities.empty:
                    tags = [f"`{r['entity_text']} ({r['entity_label']})`" for i, r in this_article_entities.iterrows()]
                    st.markdown("Теги сущностей: " + " ".join(tags))
            
            with col_feed2:
                # Выводим плашку тональности
                st.markdown(f"<h2 style='text-align: center;'>{mood_emoji}</h2>", unsafe_allow_html=True)
                st.caption(f"<p style='text-align: center;'>{sent.upper()}<br>({row['sentiment_score']:.2f})</p>", unsafe_allow_html=True)
            
            st.write("---")

# --- ✨ ЕЖЕДНЕВНЫЙ ИИ-ДАЙДЖЕСТ (ТОП-3 СВЕЖИХ НОВОСТЕЙ) ---
st.write("---")
with st.expander("✨ Открыть Ежедневный ИИ-Дайджест Новостей (ТОП-3)", expanded=True):
    # Берем первые 3 самые свежие статьи из нашего датафрейма
    top_3_articles = df_articles.head(3)
    
    if top_3_articles.empty:
        st.info("В базе данных пока нет новостей для формирования дайджеста.")
    else:
        col_d1, col_d2, col_d3 = st.columns(3)
        top_cols = [col_d1, col_d2, col_d3]
        
        for idx, (_, row) in enumerate(top_3_articles.iterrows()):
            with top_cols[idx]:
                mood = "😊 ПОЗИТИВ" if row['sentiment_label'] == 'positive' else "😡 НЕГАТИВ" if row['sentiment_label'] == 'negative' else "😐 НЕЙТРАЛЬНО"
                st.markdown(f"### 📌 {row['title']}")
                st.caption(f"📰 Источник: {row['source']} | Тональность: **{mood}**")
                
                # Извлекаем связанные теги сущностей из df_entities
                this_article_entities = df_entities[df_entities["article_id"] == row["id"]]
                if not this_article_entities.empty:
                    tags = [f"#{r['entity_text'].replace(' ', '_')}" for i, r in this_article_entities.iterrows()]
                    st.markdown(f"🏷️ **Теги:** {' '.join(tags[:4])}")
                
                st.markdown(f"[🔗 Перейти к первоисточнику]({row['link']})")

# Глушим варнинги SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 📬 ИНТЕГРАЦИЯ EMAIL-МОДУЛЯ В ВЕБ-ИНТЕРФЕЙС ---
st.sidebar.write("---")
st.sidebar.subheader("📬 Рассылка дайджеста")

# Поля настройки почты берутся из .env, но их можно переопределить прямо в браузере!
email_user = os.getenv("EMAIL_USER", "alex_polenov@mail.ru")
email_password = os.getenv("EMAIL_PASSWORD", "")

if st.sidebar.button("📧 Отправить ТОП-3 на Email"):
    # Вытаскиваем 3 самые свежие статьи из нашего датафрейма для письма
    top_articles = df_articles.head(3)
    
    if top_articles.empty:
        st.sidebar.error("❌ Нет новостей для отправки!")
    elif not email_password:
        st.sidebar.error("❌ Введите пароль приложений в .env!")
    else:
        with st.spinner("📨 Отправка письма на Gmail..."):
            try:
                # Генерируем красивую HTML-вёрстку дайджеста
                html_text = """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">📰 Ваш ИИ-Дайджест Новостей (Streamlit Web)</h2>
                """
                
                for _, row in top_articles.iterrows():
                    mood = "😊 ПОЗИТИВ" if row['sentiment_label'] == 'positive' else "😡 НЕГАТИВ" if row['sentiment_label'] == 'negative' else "😐 НЕЙТРАЛЬНО"
                    html_text += f"""
                    <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #1a73e8; margin-bottom: 15px; border-radius: 4px;">
                        <h3 style="margin-top: 0; color: #111;">📌 {row['title']}</h3>
                        <p style="margin: 5px 0;"><b>📰 Источник:</b> {row['source']} | <b>🧠 Настроение ИИ:</b> {mood}</p>
                        <p style="margin: 5px 0;"><a href="{row['link']}" style="color: #1a73e8; text-decoration: none; font-weight: bold;">Читать первоисточник →</a></p>
                    </div>
                    """
                html_text += "</body></html>"
                
                # Собираем почтовый пакет
                msg = MIMEMultipart()
                msg['From'] = email_user
                msg['To'] = email_user
                msg['Subject'] = "📰 Утренний ИИ-Дайджест со Streamlit-Панели"
                msg.attach(MIMEText(html_text, 'html', 'utf-8'))
                
                # 🎯 Защищённое подключение к Gmail SMTP с local_hostname для обхода сброса соединения
                with smtplib.SMTP_SSL("smtp.mail.ru", 465) as server:
                     server.login(email_user, email_password)
                     server.sendmail(email_user, email_user, msg.as_string())    
                st.sidebar.success("🚀 Дайджест успешно отправлен на вашу почту")
            except Exception as e:
                st.sidebar.error(f"❌ Ошибка отправки: {e}")
