from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import config
import datetime

# Создаем асинхронный движок SQLAlchemy
async_engine = create_async_engine(
    config.DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///'),
    echo=True
)

# Создаем фабрику асинхронных сессий
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Таблица связи многие-ко-многим для подписок пользователя на сериалы
user_series_subscriptions = Table(
    'user_series_subscriptions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id')),
    Column('series_id', Integer, ForeignKey('series.series_id'))
)

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_active = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношение к сериалам, на которые подписан пользователь
    subscribed_series = relationship(
        "Series",
        secondary=user_series_subscriptions,
        back_populates="subscribers"
    )

class Series(Base):
    """Модель сериала"""
    __tablename__ = 'series'
    
    series_id = Column(Integer, primary_key=True)  # ID сериала из TMDB
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)
    poster_path = Column(String, nullable=True)
    last_episode_date = Column(DateTime, nullable=True)  # Дата выхода последнего эпизода
    next_episode_date = Column(DateTime, nullable=True)  # Ожидаемая дата следующего эпизода
    last_check = Column(DateTime, default=func.now())    # Когда последний раз проверяли инфо о сериале
    
    # Отношение к пользователям, подписанным на сериал
    subscribers = relationship(
        "User",
        secondary=user_series_subscriptions,
        back_populates="subscribed_series"
    )

class Movie(Base):
    """Модель фильма"""
    __tablename__ = 'movies'
    
    movie_id = Column(Integer, primary_key=True)  # ID фильма из TMDB
    title = Column(String, nullable=False)
    original_title = Column(String, nullable=True)
    poster_path = Column(String, nullable=True)
    release_date = Column(DateTime, nullable=True)
    added_at = Column(DateTime, default=func.now())

class Notification(Base):
    """Модель уведомления"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    content_id = Column(Integer, nullable=False)  # ID сериала или фильма
    content_type = Column(String, nullable=False)  # 'movie' или 'series'
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    sent = Column(Boolean, default=False)

async def init_db():
    """Инициализация базы данных"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Получение асинхронной сессии базы данных"""
    async with AsyncSessionLocal() as session:
        yield session

# Операции с пользователями
async def get_or_create_user(session, user_id, username=None, first_name=None, last_name=None):
    """Получить пользователя или создать нового, если не существует"""
    from sqlalchemy import select
    from sqlalchemy.exc import NoResultFound
    
    try:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one()
        # Обновляем информацию о пользователе
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.last_active = datetime.datetime.now()
        await session.commit()
        return user
    except NoResultFound:
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        await session.commit()
        return user

# Операции с подписками на сериалы
async def subscribe_to_series(session, user_id, series_id, series_title, poster_path=None):
    """Подписать пользователя на сериал"""
    from sqlalchemy import select
    
    # Получаем пользователя
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one()
    
    # Проверяем, существует ли сериал
    result = await session.execute(select(Series).where(Series.series_id == series_id))
    series = result.scalar_one_or_none()
    
    if not series:
        # Создаем новый сериал, если его нет
        series = Series(
            series_id=series_id,
            title=series_title,
            poster_path=poster_path
        )
        session.add(series)
    
    # Проверяем, подписан ли уже пользователь
    if series not in user.subscribed_series:
        user.subscribed_series.append(series)
        await session.commit()
        return True
    return False

async def unsubscribe_from_series(session, user_id, series_id):
    """Отписать пользователя от сериала"""
    from sqlalchemy import select
    
    # Получаем пользователя
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one()
    
    # Получаем сериал
    result = await session.execute(select(Series).where(Series.series_id == series_id))
    series = result.scalar_one_or_none()
    
    if series and series in user.subscribed_series:
        user.subscribed_series.remove(series)
        await session.commit()
        return True
    return False

async def get_user_subscriptions(session, user_id):
    """Получить все подписки пользователя на сериалы"""
    from sqlalchemy import select
    
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        return user.subscribed_series
    return []

# Операции с уведомлениями
async def create_notification(session, user_id, content_id, content_type, message):
    """Создать уведомление для пользователя"""
    notification = Notification(
        user_id=user_id,
        content_id=content_id,
        content_type=content_type,
        message=message
    )
    session.add(notification)
    await session.commit()
    return notification

async def get_unsent_notifications(session):
    """Получить все неотправленные уведомления"""
    from sqlalchemy import select
    
    result = await session.execute(
        select(Notification).where(Notification.sent == False)
    )
    return result.scalars().all()

async def mark_notification_as_sent(session, notification_id):
    """Отметить уведомление как отправленное"""
    from sqlalchemy import select
    
    result = await session.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    
    if notification:
        notification.sent = True
        await session.commit()
        return True
    return False