import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Float, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from dotenv import load_dotenv

# 1. Загружаем доступы из .env (используем тот же файл с секретами, что и в прошлый раз!)
load_dotenv()

# Переключаемся на встроенную базу данных SQLite для Windows
DATABASE_URL = "sqlite:///news_ai.db"

# 2. Инициализируем движок SQLAlchemy и фабрику сессий
# Флаг check_same_thread нужен строго для SQLite, чтобы Streamlit мог безопасно читать базу из разных потоков
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. КЛАСС-МОДЕЛЬ ДЛЯ НОВОСТЕЙ
class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    link = Column(String, unique=True, nullable=False)
    published_at = Column(String)
    category = Column(String(50), default="Разное")
    sentiment_label = Column(String(20))
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь "один-ко-многим" с таблицей сущностей ( spaCy теги)
    entities = relationship("Entity", back_populates="article", cascade="all, delete-orphan")

# 4. КЛАСС-МОДЕЛЬ ДЛЯ СУЩНОСТЕЙ
class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"))
    entity_text = Column(String(255), nullable=False)
    entity_label = Column(String(50), nullable=False)

    article = relationship("Article", back_populates="entities")
