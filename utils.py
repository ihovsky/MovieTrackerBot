import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import html

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_date(date_str: Optional[str]) -> str:
    """
    Форматирование даты в читаемый вид
    
    Args:
        date_str: Строка с датой в формате YYYY-MM-DD
        
    Returns:
        str: Отформатированная дата в формате DD.MM.YYYY
    """
    if not date_str:
        return "Нет данных"
        
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return "Неверный формат даты"

def escape_markdown(text: str) -> str:
    """
    Экранирование специальных символов для Markdown
    
    Args:
        text: Исходный текст
        
    Returns:
        str: Экранированный текст для Markdown
    """
    if not text:
        return ""
        
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def escape_html(text: str) -> str:
    """
    Экранирование специальных символов для HTML
    
    Args:
        text: Исходный текст
        
    Returns:
        str: Экранированный текст для HTML
    """
    if not text:
        return ""
    
    return html.escape(text)

def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Обрезает текст до указанной длины с добавлением многоточия
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина текста
        
    Returns:
        str: Обрезанный текст
    """
    if not text:
        return ""
        
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def format_runtime(minutes: int) -> str:
    """
    Форматирует продолжительность из минут в часы и минуты
    
    Args:
        minutes: Продолжительность в минутах
        
    Returns:
        str: Отформатированная продолжительность
    """
    if not minutes or minutes <= 0:
        return "Нет данных"
        
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours > 0:
        return f"{hours} ч {remaining_minutes} мин"
    else:
        return f"{minutes} мин"

def format_rating(rating: float) -> str:
    """
    Форматирует рейтинг с добавлением звездочек
    
    Args:
        rating: Рейтинг от 0 до 10
        
    Returns:
        str: Отформатированный рейтинг со звездочками
    """
    if not rating or rating < 0:
        return "Нет оценки"
        
    # Нормализуем рейтинг от 0 до 5 звезд
    stars = min(5, round(rating / 2))
    return f"{rating}/10 {'⭐' * stars}"

def get_genres_string(genres: List[Dict[str, Any]]) -> str:
    """
    Преобразует список жанров в строку
    
    Args:
        genres: Список словарей с жанрами
        
    Returns:
        str: Строка с жанрами через запятую
    """
    if not genres:
        return "Нет данных"
        
    return ", ".join(genre.get("name", "") for genre in genres)

def format_movie_info(movie: Dict[str, Any]) -> str:
    """
    Форматирует информацию о фильме для отображения
    
    Args:
        movie: Словарь с информацией о фильме
        
    Returns:
        str: Отформатированная информация о фильме
    """
    title = movie.get("title", "Название неизвестно")
    original_title = movie.get("original_title", "")
    release_date = format_date(movie.get("release_date", ""))
    overview = movie.get("overview", "Описание отсутствует")
    genres = get_genres_string(movie.get("genres", []))
    rating = format_rating(movie.get("vote_average", 0))
    runtime = format_runtime(movie.get("runtime", 0))
    
    # Создаем сообщение с информацией о фильме
    message = f"🎬 *{escape_markdown(title)}*"
    
    if original_title and original_title != title:
        message += f"\n📝 *Оригинальное название:* {escape_markdown(original_title)}"
    
    message += f"\n📅 *Дата выхода:* {release_date}"
    message += f"\n⏱ *Продолжительность:* {runtime}"
    message += f"\n🏆 *Рейтинг:* {rating}"
    message += f"\n🎭 *Жанры:* {escape_markdown(genres)}"
    message += f"\n\n📖 *Описание:*\n{escape_markdown(truncate_text(overview, 700))}"
    
    return message

def format_tv_info(tv: Dict[str, Any], last_episode_date=None, next_episode_date=None) -> str:
    """
    Форматирует информацию о сериале для отображения
    
    Args:
        tv: Словарь с информацией о сериале
        last_episode_date: Дата последнего эпизода
        next_episode_date: Дата следующего эпизода
        
    Returns:
        str: Отформатированная информация о сериале
    """
    title = tv.get("name", "Название неизвестно")
    original_title = tv.get("original_name", "")
    first_air_date = format_date(tv.get("first_air_date", ""))
    overview = tv.get("overview", "Описание отсутствует")
    genres = get_genres_string(tv.get("genres", []))
    rating = format_rating(tv.get("vote_average", 0))
    seasons_count = tv.get("number_of_seasons", 0)
    episodes_count = tv.get("number_of_episodes", 0)
    
    # Создаем сообщение с информацией о сериале
    message = f"📺 *{escape_markdown(title)}*"
    
    if original_title and original_title != title:
        message += f"\n📝 *Оригинальное название:* {escape_markdown(original_title)}"
    
    message += f"\n📅 *Дата выхода:* {first_air_date}"
    message += f"\n🔢 *Сезонов:* {seasons_count}"
    message += f"\n📊 *Эпизодов:* {episodes_count}"
    message += f"\n🏆 *Рейтинг:* {rating}"
    message += f"\n🎭 *Жанры:* {escape_markdown(genres)}"
    
    if last_episode_date:
        if isinstance(last_episode_date, datetime):
            formatted_date = last_episode_date.strftime("%d.%m.%Y")
        else:
            formatted_date = format_date(str(last_episode_date))
        message += f"\n📆 *Последний эпизод:* {formatted_date}"
    
    if next_episode_date:
        if isinstance(next_episode_date, datetime):
            formatted_date = next_episode_date.strftime("%d.%m.%Y")
        else:
            formatted_date = format_date(str(next_episode_date))
        message += f"\n⏰ *Следующий эпизод:* {formatted_date}"
    
    message += f"\n\n📖 *Описание:*\n{escape_markdown(truncate_text(overview, 700))}"
    
    return message

def format_search_result(item: Dict[str, Any]) -> str:
    """
    Форматирует результат поиска для отображения в списке
    
    Args:
        item: Словарь с информацией о найденном объекте
        
    Returns:
        str: Отформатированная строка с информацией
    """
    media_type = item.get("media_type", "")
    
    if media_type == "movie":
        title = item.get("title", "Название неизвестно")
        year = item.get("release_date", "")[:4] if item.get("release_date") else "N/A"
        return f"🎬 {escape_markdown(title)} ({year})"
    
    elif media_type == "tv":
        title = item.get("name", "Название неизвестно")
        year = item.get("first_air_date", "")[:4] if item.get("first_air_date") else "N/A"
        return f"📺 {escape_markdown(title)} ({year})"
    
    else:
        return "Неизвестный тип контента"

def format_trending_item(item: Dict[str, Any]) -> str:
    """
    Форматирует элемент из списка трендов для отображения
    
    Args:
        item: Словарь с информацией о трендовом объекте
        
    Returns:
        str: Отформатированная строка с информацией
    """
    media_type = item.get("media_type", "")
    
    if media_type == "movie" or "title" in item:
        title = item.get("title", "Название неизвестно")
        year = item.get("release_date", "")[:4] if item.get("release_date") else "N/A"
        rating = item.get("vote_average", 0)
        stars = min(5, round(rating / 2)) if rating else 0
        
        return f"🎬 *{escape_markdown(title)}* ({year}) {rating}/10 {'⭐' * stars}"
    
    elif media_type == "tv" or "name" in item:
        title = item.get("name", "Название неизвестно")
        year = item.get("first_air_date", "")[:4] if item.get("first_air_date") else "N/A"
        rating = item.get("vote_average", 0)
        stars = min(5, round(rating / 2)) if rating else 0
        
        return f"📺 *{escape_markdown(title)}* ({year}) {rating}/10 {'⭐' * stars}"
    
    else:
        return "Неизвестный тип контента"

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Разбивает список на подсписки заданного размера
    
    Args:
        lst: Исходный список
        chunk_size: Размер подсписка
        
    Returns:
        List[List[Any]]: Список подсписков
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]