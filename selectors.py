# Селекторы для парсинга hdrezka.ag

# Селектор для поиска фильма/сериала на странице поиска
HDREZKA_SEARCH_SELECTOR = ".b-search__section a"

# Селектор для поиска ссылки на конкретный эпизод сериала
# Используется .format(season=season, episode=episode) для подстановки значений
HDREZKA_EPISODE_SELECTOR = "a[data-season='{season}'][data-episode='{episode}']"