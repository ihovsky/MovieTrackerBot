import logging
import asyncio
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple, Union, Any

from telegram import Update, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from sqlalchemy.ext.asyncio import AsyncSession

import config
import tmdb_api
import keyboards
import utils
from database import (
    init_db, get_db, get_or_create_user, subscribe_to_series, 
    unsubscribe_from_series, get_user_subscriptions,
    create_notification, get_unsent_notifications, mark_notification_as_sent
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для машины состояний ConversationHandler
(
    MAIN_MENU,
    SEARCH_QUERY,
) = range(2)

# Словарь для хранения временных данных сессии пользователя
user_data_cache = {}

# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Инициализация/получение пользователя в БД
    async for session in get_db():
        await get_or_create_user(
            session, 
            user.id, 
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я бот MovieTracker, который поможет тебе отслеживать новинки кино и сериалов.\n\n"
        f"С моей помощью ты можешь:\n"
        f"• Узнать о трендовых новинках 🔥\n"
        f"• Подписаться на обновления любимых сериалов 📺\n"
        f"• Получать уведомления о выходе новых эпизодов ⏰\n\n"
        f"Используй меню ниже для навигации 👇",
        reply_markup=keyboards.get_main_menu_keyboard()
    )
    
    return MAIN_MENU

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🤖 *Справка по командам MovieTracker*\n\n"
        "*Основные команды:*\n"
        "/start - Запустить бота и вернуться в главное меню\n"
        "/help - Показать справку по командам\n"
        "/trending - Показать трендовые новинки\n"
        "/search - Поиск фильмов и сериалов\n"
        "/subscriptions - Управление подписками на сериалы\n"
        "/settings - Настройки бота\n\n"
        "*Навигация:*\n"
        "Используйте кнопки в меню для навигации по функциям бота.\n\n"
        "*Подписки:*\n"
        "Вы можете подписаться на уведомления о новых эпизодах ваших любимых сериалов.\n\n"
        "*Поиск:*\n"
        "Для поиска просто напишите название фильма или сериала после команды /search или выберите соответствующий пункт меню.",
        parse_mode="Markdown"
    )

async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /trending"""
    await update.message.reply_text(
        "Выберите категорию контента, для которого хотите увидеть тренды:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Фильмы", callback_data="trending_movie_menu")],
            [InlineKeyboardButton("📺 Сериалы", callback_data="trending_tv_menu")]
        ])
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /search"""
    await update.message.reply_text(
        "🔍 Введите название фильма или сериала для поиска:"
    )
    return SEARCH_QUERY

async def subscriptions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /subscriptions - показывает список подписок пользователя"""
    user_id = update.effective_user.id
    
    async for session in get_db():
        subscriptions = await get_user_subscriptions(session, user_id)
    
    if not subscriptions:
        await update.message.reply_text(
            "У вас пока нет подписок на сериалы. Чтобы подписаться, найдите интересующий вас сериал через поиск.",
            reply_markup=keyboards.get_subscriptions_keyboard([])
        )
    else:
        await update.message.reply_text(
            "📺 *Ваши подписки на сериалы:*",
            parse_mode="Markdown",
            reply_markup=keyboards.get_subscriptions_keyboard(subscriptions)
        )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /settings - показывает настройки пользователя"""
    user_id = update.effective_user.id
    
    # Получаем настройки пользователя из БД
    async for session in get_db():
        from sqlalchemy import select
        from database import User
        
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            notifications_enabled = user.notifications_enabled
        else:
            notifications_enabled = True
    
    await update.message.reply_text(
        "⚙️ *Настройки*\n\n"
        "Здесь вы можете управлять настройками бота:",
        parse_mode="Markdown",
        reply_markup=keyboards.get_settings_keyboard(notifications_enabled)
    )

# Обработчики сообщений
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает текстовые сообщения"""
    text = update.message.text
    
    # Обработка пунктов главного меню
    if text == "🔥 Новинки фильмов":
        await show_trending_movies(update, context)
        return MAIN_MENU
    
    elif text == "📺 Новинки сериалов":
        await show_trending_tv(update, context)
        return MAIN_MENU
    
    elif text == "🔍 Поиск":
        await update.message.reply_text(
            "🔍 Введите название фильма или сериала для поиска:"
        )
        return SEARCH_QUERY
    
    elif text == "👤 Мои подписки":
        await subscriptions_command(update, context)
        return MAIN_MENU
    
    elif text == "ℹ️ О боте":
        await update.message.reply_text(
            "🤖 *О боте MovieTracker*\n\n"
            "MovieTracker - это Telegram бот для отслеживания новинок кино и сериалов.\n\n"
            "Основные функции бота:\n"
            "• Просмотр трендовых новинок 🔥\n"
            "• Поиск фильмов и сериалов 🔍\n"
            "• Подписка на обновления сериалов 📺\n"
            "• Уведомления о новых эпизодах ⏰\n\n"
            "Данные предоставляются API TMDB (The Movie Database).\n\n"
            "Используйте команду /help для получения списка доступных команд.",
            parse_mode="Markdown"
        )
        return MAIN_MENU
    
    elif text == "⚙️ Настройки":
        await settings_command(update, context)
        return MAIN_MENU
    
    # Для других текстовых сообщений предполагаем, что это поисковый запрос
    else:
        return await process_search_query(update, context)

async def process_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает поисковый запрос"""
    query = update.message.text.strip()
    
    if not query:
        await update.message.reply_text(
            "Поисковый запрос не может быть пустым. Пожалуйста, введите название фильма или сериала."
        )
        return SEARCH_QUERY
    
    await update.message.reply_text(f"🔍 Ищу '{query}'...")
    
    # Выполняем поиск через API TMDB
    search_results = tmdb_api.search_multi(query)
    
    if not search_results or not search_results.get("results"):
        await update.message.reply_text(
            "😔 По вашему запросу ничего не найдено. Попробуйте изменить запрос."
        )
        return SEARCH_QUERY
    
    # Фильтруем результаты: только фильмы и сериалы
    results = [item for item in search_results.get("results", []) 
              if item.get("media_type") in ["movie", "tv"]]
    
    if not results:
        await update.message.reply_text(
            "😔 По вашему запросу не найдено фильмов или сериалов. Попробуйте изменить запрос."
        )
        return SEARCH_QUERY
    
    # Cохраняем результаты в кэше пользователя
    user_id = update.effective_user.id
    if user_id not in user_data_cache:
        user_data_cache[user_id] = {}
    
    user_data_cache[user_id]["search_results"] = results
    user_data_cache[user_id]["search_query"] = query
    
    # Показываем первые 5 результатов
    page_results = results[:5]
    total_pages = (len(results) + 4) // 5  # Округление вверх
    
    await show_search_results(update, context, page_results, 1, total_pages)
    
    return MAIN_MENU

async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             results: List[Dict], page: int, total_pages: int) -> None:
    """Показывает результаты поиска"""
    if not results:
        if update.callback_query:
            await update.callback_query.message.edit_text(
                "😔 По вашему запросу ничего не найдено."
            )
        else:
            await update.message.reply_text(
                "😔 По вашему запросу ничего не найдено."
            )
        return
    
    message_text = f"🔍 *Результаты поиска:*\n\n"
    
    for i, item in enumerate(results, 1):
        message_text += f"{i}. {utils.format_search_result(item)}\n"
    
    message_text += f"\nСтраница {page} из {total_pages}"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=keyboards.get_search_results_keyboard(results, page, total_pages)
        )
    else:
        await update.message.reply_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=keyboards.get_search_results_keyboard(results, page, total_pages)
        )

# Обработчики трендовых фильмов и сериалов
async def show_trending_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает трендовые фильмы"""
    await update.message.reply_text(
        "Выберите период для трендовых фильмов:",
        reply_markup=keyboards.get_trending_period_keyboard("movie")
    )

async def show_trending_tv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает трендовые сериалы"""
    await update.message.reply_text(
        "Выберите период для трендовых сериалов:",
        reply_markup=keyboards.get_trending_period_keyboard("tv")
    )

async def handle_trending_content(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                content_type: str, time_window: str, page: int = 1) -> None:
    """Общий обработчик для отображения трендового контента"""
    query = update.callback_query
    
    if content_type == "movie":
        trending_data = tmdb_api.get_trending_movies(time_window, page)
        content_name = "фильмов"
    else:  # tv
        trending_data = tmdb_api.get_trending_tv(time_window, page)
        content_name = "сериалов"
    
    period_name = "сегодня" if time_window == "day" else "за неделю"
    
    results = trending_data.get("results", [])
    total_pages = trending_data.get("total_pages", 1)
    
    if not results:
        await query.message.edit_text(
            f"😔 Не удалось получить список трендовых {content_name} {period_name}."
        )
        return
    
    # Формируем сообщение с результатами
    message_text = f"🔥 *Трендовые {content_name} {period_name}:*\n\n"
    
    for i, item in enumerate(results[:10], 1):
        message_text += f"{i}. {utils.format_trending_item(item)}\n"
    
    message_text += f"\nСтраница {page} из {total_pages}"
    
    # Сохраняем данные в кэше пользователя для пагинации
    user_id = update.effective_user.id
    if user_id not in user_data_cache:
        user_data_cache[user_id] = {}
    
    user_data_cache[user_id]["trending_type"] = content_type
    user_data_cache[user_id]["trending_window"] = time_window
    user_data_cache[user_id]["trending_results"] = results
    
    callback_prefix = f"trending_{content_type}_{time_window}"
    
    await query.message.edit_text(
        message_text,
        parse_mode="Markdown",
        reply_markup=keyboards.get_pagination_keyboard(page, total_pages, callback_prefix)
    )

# Обработчики информации о фильме/сериале
async def show_movie_details(update: Update, context: ContextTypes.DEFAULT_TYPE, movie_id: int) -> None:
    """Показывает детальную информацию о фильме"""
    query = update.callback_query
    
    # Получаем детали фильма
    movie_details = tmdb_api.get_movie_details(movie_id)
    
    if not movie_details or not movie_details.get("id"):
        await query.message.edit_text(
            "😔 Не удалось получить информацию о фильме. Попробуйте позже."
        )
        return
    
    # Формируем сообщение с информацией
    message_text = utils.format_movie_info(movie_details)
    
    # Получаем URL постера, если есть
    poster_path = movie_details.get("poster_path")
    
    if poster_path:
        poster_url = tmdb_api.get_poster_url(poster_path)
        
        # Отправляем сообщение с постером
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=poster_url,
            caption=message_text,
            parse_mode="Markdown",
            reply_markup=keyboards.get_movie_details_keyboard(movie_id)
        )
    else:
        # Отправляем сообщение без постера
        await query.message.edit_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=keyboards.get_movie_details_keyboard(movie_id)
        )

async def show_tv_details(update: Update, context: ContextTypes.DEFAULT_TYPE, tv_id: int) -> None:
    """Показывает детальную информацию о сериале"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Проверяем, подписан ли пользователь на этот сериал
    is_subscribed = False
    
    async for session in get_db():
        # Получаем подписки пользователя
        subscriptions = await get_user_subscriptions(session, user_id)
        
        # Проверяем, есть ли сериал в подписках
        is_subscribed = any(s.series_id == tv_id for s in subscriptions)
    
    # Получаем детали сериала
    tv_details = tmdb_api.get_tv_details(tv_id)
    
    if not tv_details or not tv_details.get("id"):
        await query.message.edit_text(
            "😔 Не удалось получить информацию о сериале. Попробуйте позже."
        )
        return
    
    # Получаем даты последнего и следующего эпизодов
    last_episode_date, next_episode_date = tmdb_api.get_latest_episodes(tv_id)
    
    # Формируем сообщение с информацией
    message_text = utils.format_tv_info(tv_details, last_episode_date, next_episode_date)
    
    # Получаем URL постера, если есть
    poster_path = tv_details.get("poster_path")
    
    if poster_path:
        poster_url = tmdb_api.get_poster_url(poster_path)
        
        # Отправляем сообщение с постером
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=poster_url,
            caption=message_text,
            parse_mode="Markdown",
            reply_markup=keyboards.get_tv_details_keyboard(tv_id, is_subscribed)
        )
    else:
        # Отправляем сообщение без постера
        await query.message.edit_text(
            message_text,
            parse_mode="Markdown",
            reply_markup=keyboards.get_tv_details_keyboard(tv_id, is_subscribed)
        )

# Обработчики подписки/отписки
async def subscribe_to_tv_series(update: Update, context: ContextTypes.DEFAULT_TYPE, tv_id: int) -> None:
    """Обработчик подписки на сериал"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Получаем информацию о сериале
    tv_details = tmdb_api.get_tv_details(tv_id)
    
    if not tv_details or not tv_details.get("id"):
        await query.answer("Не удалось получить информацию о сериале")
        return
    
    series_title = tv_details.get("name", "")
    poster_path = tv_details.get("poster_path")
    
    # Добавляем подписку
    async for session in get_db():
        success = await subscribe_to_series(
            session, user_id, tv_id, series_title, poster_path
        )
    
    if success:
        await query.answer("Вы успешно подписались на обновления сериала!")
        
        # Обновляем клавиатуру
        keyboard = keyboards.get_tv_details_keyboard(tv_id, True)
        
        if query.message.photo:
            await query.message.edit_reply_markup(reply_markup=keyboard)
        else:
            await query.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await query.answer("Вы уже подписаны на этот сериал")

async def unsubscribe_from_tv_series(update: Update, context: ContextTypes.DEFAULT_TYPE, tv_id: int) -> None:
    """Обработчик отписки от сериала"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Отменяем подписку
    async for session in get_db():
        success = await unsubscribe_from_series(session, user_id, tv_id)
    
    if success:
        await query.answer("Вы отписались от обновлений сериала")
        
        # Обновляем клавиатуру
        keyboard = keyboards.get_tv_details_keyboard(tv_id, False)
        
        if query.message.photo:
            await query.message.edit_reply_markup(reply_markup=keyboard)
        else:
            await query.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await query.answer("Вы не были подписаны на этот сериал")

# Обработчики настроек
async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Включает/выключает уведомления для пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    async for session in get_db():
        from sqlalchemy import select
        from database import User
        
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            # Инвертируем текущее состояние
            user.notifications_enabled = not user.notifications_enabled
            await session.commit()
            
            # Обновляем клавиатуру
            keyboard = keyboards.get_settings_keyboard(user.notifications_enabled)
            await query.message.edit_reply_markup(reply_markup=keyboard)
            
            status = "включены" if user.notifications_enabled else "выключены"
            await query.answer(f"Уведомления {status}")
        else:
            await query.answer("Ошибка при обновлении настроек")

# Обработчик рекомендаций
async def show_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str, content_id: int) -> None:
    """Показывает рекомендации похожих фильмов или сериалов"""
    query = update.callback_query
    
    # Получаем рекомендации
    recommendations = tmdb_api.get_recommendations(content_type, content_id)
    
    if not recommendations or not recommendations.get("results"):
        await query.answer("Не удалось получить рекомендации")
        return
    
    results = recommendations.get("results", [])[:10]  # Ограничиваем до 10 результатов
    
    # Формируем сообщение с рекомендациями
    content_name = "фильмов" if content_type == "movie" else "сериалов"
    message_text = f"👍 *Рекомендации похожих {content_name}:*\n\n"
    
    for i, item in enumerate(results, 1):
        title = item.get("title") if content_type == "movie" else item.get("name")
        year = item.get("release_date", "")[:4] if content_type == "movie" else item.get("first_air_date", "")[:4]
        year = year if year else "N/A"
        rating = item.get("vote_average", 0)
        stars = min(5, round(rating / 2)) if rating else 0
        
        message_text += f"{i}. *{utils.escape_markdown(title)}* ({year}) {rating}/10 {'⭐' * stars}\n"
    
    # Создаем клавиатуру для просмотра деталей рекомендаций
    keyboard = []
    for item in results:
        item_id = item.get("id")
        title = item.get("title") if content_type == "movie" else item.get("name")
        if item_id and title:
            keyboard.append([InlineKeyboardButton(
                f"{title}", 
                callback_data=f"view_{content_type}_{item_id}"
            )])
    
    # Добавляем кнопку возврата
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])
    
    await query.message.edit_text(
        message_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обработчик callback запросов
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает callback запросы от inline клавиатур"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Проверяем наличие пользователя в кэше
    if user_id not in user_data_cache:
        user_data_cache[user_id] = {}
    
    # Получаем данные callback
    data = query.data
    
    # Логируем callback для отладки
    logger.info(f"Callback query: {data} from user {user_id}")
    
    # Обработка различных типов callback запросов
    
    # Возврат в главное меню
    if data == "main_menu":
        await query.message.edit_text(
            "Главное меню. Выберите действие:",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
    
    # Показ меню трендов
    elif data.startswith("trending_") and data.endswith("_menu"):
        content_type = data.split("_")[1]  # movie или tv
        content_name = "фильмов" if content_type == "movie" else "сериалов"
        
        await query.message.edit_text(
            f"Выберите период для трендовых {content_name}:",
            reply_markup=keyboards.get_trending_period_keyboard(content_type)
        )
    
    # Показ трендов по выбранному периоду
    elif data.startswith("trending_") and (data.endswith("_day") or data.endswith("_week")):
        parts = data.split("_")
        content_type = parts[1]  # movie или tv
        time_window = parts[2]  # day или week
        
        await handle_trending_content(update, context, content_type, time_window)
    
    # Пагинация для трендов
    elif data.startswith("trending_") and "_" in data:
        parts = data.split("_")
        if len(parts) >= 4 and parts[3].isdigit():
            content_type = parts[1]  # movie или tv
            time_window = parts[2]  # day или week
            page = int(parts[3])
            
            await handle_trending_content(update, context, content_type, time_window, page)
    
    # Просмотр деталей фильма/сериала
    elif data.startswith("view_"):
        parts = data.split("_")
        if len(parts) >= 3:
            content_type = parts[1]  # movie или tv
            content_id = int(parts[2])
            
            if content_type == "movie":
                await show_movie_details(update, context, content_id)
            elif content_type == "tv":
                await show_tv_details(update, context, content_id)
    
    # Подписка на сериал
    elif data.startswith("subscribe_"):
        tv_id = int(data.split("_")[1])
        await subscribe_to_tv_series(update, context, tv_id)
    
    # Отписка от сериала
    elif data.startswith("unsubscribe_"):
        tv_id = int(data.split("_")[1])
        await unsubscribe_from_tv_series(update, context, tv_id)
    
    # Переключение настроек уведомлений
    elif data == "toggle_notifications":
        await toggle_notifications(update, context)
    
    # Показ рекомендаций
    elif data.startswith("recommend_"):
        parts = data.split("_")
        if len(parts) >= 3:
            content_type = parts[1]  # movie или tv
            content_id = int(parts[2])
            
            await show_recommendations(update, context, content_type, content_id)
    
    # Пагинация для результатов поиска
    elif data.startswith("search_page_"):
        page = int(data.split("_")[2])
        
        # Получаем кэшированные результаты поиска
        results = user_data_cache.get(user_id, {}).get("search_results", [])
        
        if results:
            total_pages = (len(results) + 4) // 5  # Округление вверх
            start_idx = (page - 1) * 5
            end_idx = start_idx + 5
            page_results = results[start_idx:end_idx]
            
            await show_search_results(update, context, page_results, page, total_pages)
    
    # Новый поиск
    elif data == "new_search":
        await query.message.edit_text(
            "🔍 Введите название фильма или сериала для поиска:"
        )
        return SEARCH_QUERY
    
    # Кнопка "Назад"
    elif data == "back":
        # Логика возврата зависит от контекста
        # Пока просто возвращаем в главное меню
        await query.message.edit_text(
            "Выберите действие:",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
    
    # Обработка других callback запросов
    else:
        await query.answer("Неизвестная команда")

# Функция для периодической проверки обновлений сериалов
async def check_series_updates():
    """Периодически проверяет обновления сериалов и отправляет уведомления"""
    logger.info("Запуск проверки обновлений сериалов")
    
    async for session in get_db():
        from sqlalchemy import select
        from database import Series, User
        
        # Получаем все сериалы с подписками
        result = await session.execute(
            select(Series).where(Series.subscribers.any())
        )
        series_list = result.scalars().all()
        
        for series in series_list:
            # Получаем информацию о последних эпизодах
            last_episode_date, next_episode_date = tmdb_api.get_latest_episodes(series.series_id)
            
            # Проверяем, есть ли обновления
            if last_episode_date and (
                series.last_episode_date is None or 
                (isinstance(last_episode_date, datetime) and last_episode_date > series.last_episode_date)
            ):
                # Обновляем информацию о сериале
                series.last_episode_date = last_episode_date
                series.next_episode_date = next_episode_date
                series.last_check = datetime.now()
                await session.commit()
                
                # Получаем подписчиков сериала
                result = await session.execute(
                    select(User).where(User.subscribed_series.any(Series.series_id == series.series_id))
                )
                subscribers = result.scalars().all()
                
                # Создаем уведомления для подписчиков
                for user in subscribers:
                    if user.notifications_enabled:
                        message = f"🔔 Вышел новый эпизод сериала \"{series.title}\"!"
                        await create_notification(
                            session, user.user_id, series.series_id, "tv", message
                        )
            else:
                # Обновляем только дату проверки
                series.last_check = datetime.now()
                if next_episode_date:
                    series.next_episode_date = next_episode_date
                await session.commit()

# Функция для отправки накопленных уведомлений
async def send_notifications(application: Application):
    """Отправляет накопленные уведомления пользователям"""
    logger.info("Запуск отправки уведомлений")
    
    async for session in get_db():
        # Получаем все неотправленные уведомления
        notifications = await get_unsent_notifications(session)
        
        for notification in notifications:
            try:
                # Получаем информацию о контенте
                if notification.content_type == "tv":
                    content_details = tmdb_api.get_tv_details(notification.content_id)
                    title = content_details.get("name", "")
                    poster_path = content_details.get("poster_path")
                else:  # movie
                    content_details = tmdb_api.get_movie_details(notification.content_id)
                    title = content_details.get("title", "")
                    poster_path = content_details.get("poster_path")
                
                # Формируем сообщение
                message_text = notification.message
                
                if title:
                    message_text += f"\nНазвание: {title}"
                
                # Отправляем уведомление
                if poster_path:
                    poster_url = tmdb_api.get_poster_url(poster_path)
                    
                    # С постером
                    await application.bot.send_photo(
                        chat_id=notification.user_id,
                        photo=poster_url,
                        caption=message_text
                    )
                else:
                    # Без постера
                    await application.bot.send_message(
                        chat_id=notification.user_id,
                        text=message_text
                    )
                
                # Отмечаем уведомление как отправленное
                await mark_notification_as_sent(session, notification.id)
                
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления {notification.id}: {e}")

# Функция для периодического запуска задач
async def scheduled_tasks(application: Application):
    """Запускает периодические задачи"""
    while True:
        try:
            # Проверка обновлений сериалов
            await check_series_updates()
            
            # Отправка уведомлений
            await send_notifications(application)
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении периодических задач: {e}")
            
        # Ждем NOTIFICATION_INTERVAL часов до следующей проверки
        await asyncio.sleep(config.NOTIFICATION_INTERVAL * 3600)

# Основная функция запуска бота
async def main() -> None:
    """Точка входа для запуска бота"""
    # Инициализируем базу данных
    await init_db()
    
    # Создаем экземпляр бота
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # Определяем обработчик разговоров
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CommandHandler("search", search_command),
        ],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message),
            ],
            SEARCH_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_search_query),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("trending", trending_command))
    application.add_handler(CommandHandler("subscriptions", subscriptions_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Запускаем периодические задачи в отдельном потоке
    application.job_queue.run_once(
        lambda context: asyncio.create_task(scheduled_tasks(application)),
        when=1
    )
    
    # Запускаем бота
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())