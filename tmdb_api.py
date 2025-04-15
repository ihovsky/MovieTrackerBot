import requests
import logging
from datetime import datetime
import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Базовый URL API TMDB
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Заголовки для запросов к API
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {config.TMDB_ACCESS_TOKEN}"
}

def get_trending_movies(time_window="week", page=1, language="ru-RU"):
    """
    Получить список трендовых фильмов
    
    Args:
        time_window (str): "day" или "week"
        page (int): номер страницы результатов
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Результаты запроса с трендовыми фильмами
    """
    url = f"{BASE_URL}/trending/movie/{time_window}"
    params = {
        "language": language,
        "page": page
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении трендовых фильмов: {e}")
        return {"results": []}

def get_trending_tv(time_window="week", page=1, language="ru-RU"):
    """
    Получить список трендовых сериалов
    
    Args:
        time_window (str): "day" или "week"
        page (int): номер страницы результатов
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Результаты запроса с трендовыми сериалами
    """
    url = f"{BASE_URL}/trending/tv/{time_window}"
    params = {
        "language": language,
        "page": page
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении трендовых сериалов: {e}")
        return {"results": []}

def get_movie_details(movie_id, language="ru-RU"):
    """
    Получить детальную информацию о фильме
    
    Args:
        movie_id (int): ID фильма в TMDB
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Детальная информация о фильме
    """
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"language": language}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении деталей фильма {movie_id}: {e}")
        return {}

def get_tv_details(tv_id, language="ru-RU"):
    """
    Получить детальную информацию о сериале
    
    Args:
        tv_id (int): ID сериала в TMDB
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Детальная информация о сериале
    """
    url = f"{BASE_URL}/tv/{tv_id}"
    params = {"language": language}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении деталей сериала {tv_id}: {e}")
        return {}

def get_tv_season_details(tv_id, season_number, language="ru-RU"):
    """
    Получить детальную информацию о сезоне сериала
    
    Args:
        tv_id (int): ID сериала в TMDB
        season_number (int): номер сезона
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Детальная информация о сезоне
    """
    url = f"{BASE_URL}/tv/{tv_id}/season/{season_number}"
    params = {"language": language}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении деталей сезона {season_number} сериала {tv_id}: {e}")
        return {}

def search_multi(query, page=1, language="ru-RU"):
    """
    Выполнить поиск фильмов, сериалов и людей
    
    Args:
        query (str): поисковый запрос
        page (int): номер страницы результатов
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Результаты поиска
    """
    url = f"{BASE_URL}/search/multi"
    params = {
        "query": query,
        "language": language,
        "page": page,
        "include_adult": "false"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при поиске '{query}': {e}")
        return {"results": []}

def get_tv_episode_details(tv_id, season_number, episode_number, language="ru-RU"):
    """
    Получить детальную информацию о эпизоде сериала
    
    Args:
        tv_id (int): ID сериала в TMDB
        season_number (int): номер сезона
        episode_number (int): номер эпизода
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Детальная информация о эпизоде
    """
    url = f"{BASE_URL}/tv/{tv_id}/season/{season_number}/episode/{episode_number}"
    params = {"language": language}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении деталей эпизода {episode_number} сезона {season_number} сериала {tv_id}: {e}")
        return {}

def get_latest_episodes(tv_id, language="ru-RU"):
    """
    Получить информацию о последних эпизодах сериала
    
    Args:
        tv_id (int): ID сериала в TMDB
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        tuple: (last_episode_date, next_episode_date)
    """
    # Получаем детали сериала
    tv_details = get_tv_details(tv_id, language)
    
    if not tv_details or 'seasons' not in tv_details:
        return None, None
    
    # Получаем последний сезон с эпизодами
    seasons = sorted([s for s in tv_details['seasons'] if s.get('episode_count', 0) > 0], 
                    key=lambda x: x.get('season_number', 0), 
                    reverse=True)
    
    if not seasons:
        return None, None
    
    latest_season = seasons[0]
    season_number = latest_season.get('season_number')
    
    # Получаем информацию о последнем сезоне
    season_details = get_tv_season_details(tv_id, season_number, language)
    
    if not season_details or 'episodes' not in season_details:
        return None, None
    
    # Сортируем эпизоды по дате выхода
    episodes = sorted([e for e in season_details['episodes'] if e.get('air_date')], 
                     key=lambda x: x.get('air_date', ''), 
                     reverse=True)
    
    if not episodes:
        return None, None
    
    # Определяем дату последнего вышедшего эпизода
    today = datetime.now().date()
    last_episode = None
    next_episode = None
    
    for episode in episodes:
        if 'air_date' in episode and episode['air_date']:
            air_date = datetime.strptime(episode['air_date'], '%Y-%m-%d').date()
            
            if air_date <= today and (last_episode is None or air_date > last_episode[0]):
                last_episode = (air_date, episode)
            elif air_date > today and (next_episode is None or air_date < next_episode[0]):
                next_episode = (air_date, episode)
    
    last_episode_date = last_episode[0] if last_episode else None
    next_episode_date = next_episode[0] if next_episode else None
    
    return last_episode_date, next_episode_date

def get_poster_url(poster_path):
    """
    Получить полный URL для постера
    
    Args:
        poster_path (str): путь к постеру из API TMDB
        
    Returns:
        str: полный URL к изображению
    """
    if not poster_path:
        return None
    return f"{IMAGE_BASE_URL}{poster_path}"

def get_popular_movies(page=1, language="ru-RU"):
    """
    Получить список популярных фильмов
    
    Args:
        page (int): номер страницы результатов
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Результаты запроса с популярными фильмами
    """
    url = f"{BASE_URL}/movie/popular"
    params = {
        "language": language,
        "page": page
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении популярных фильмов: {e}")
        return {"results": []}

def get_popular_tv(page=1, language="ru-RU"):
    """
    Получить список популярных сериалов
    
    Args:
        page (int): номер страницы результатов
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Результаты запроса с популярными сериалами
    """
    url = f"{BASE_URL}/tv/popular"
    params = {
        "language": language,
        "page": page
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении популярных сериалов: {e}")
        return {"results": []}

def get_recommendations(content_type, content_id, page=1, language="ru-RU"):
    """
    Получить рекомендации похожих фильмов или сериалов
    
    Args:
        content_type (str): тип контента ("movie" или "tv")
        content_id (int): ID контента в TMDB
        page (int): номер страницы результатов
        language (str): язык результатов (например, "ru-RU")
        
    Returns:
        dict: Результаты запроса с рекомендациями
    """
    url = f"{BASE_URL}/{content_type}/{content_id}/recommendations"
    params = {
        "language": language,
        "page": page
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении рекомендаций для {content_type} {content_id}: {e}")
        return {"results": []}