from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# Главное меню
def get_main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [KeyboardButton("🔥 Новинки фильмов"), KeyboardButton("📺 Новинки сериалов")],
        [KeyboardButton("🔍 Поиск"), KeyboardButton("👤 Мои подписки")],
        [KeyboardButton("ℹ️ О боте"), KeyboardButton("⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Клавиатура для выбора временного периода трендов
def get_trending_period_keyboard(content_type):
    """Клавиатура для выбора периода трендов (сегодня/неделя)"""
    keyboard = [
        [
            InlineKeyboardButton("За сегодня", callback_data=f"trending_{content_type}_day"),
            InlineKeyboardButton("За неделю", callback_data=f"trending_{content_type}_week")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Пагинация для результатов
def get_pagination_keyboard(current_page, total_pages, callback_prefix):
    """Клавиатура для пагинации результатов"""
    keyboard = []
    
    # Кнопки навигации
    navigation = []
    
    # Кнопка "Назад"
    if current_page > 1:
        navigation.append(InlineKeyboardButton("◀️ Назад", callback_data=f"{callback_prefix}_{current_page-1}"))
    
    # Текущая страница и общее количество
    navigation.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info"))
    
    # Кнопка "Вперед"
    if current_page < total_pages:
        navigation.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"{callback_prefix}_{current_page+1}"))
    
    keyboard.append(navigation)
    
    # Кнопка возврата в главное меню
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для детальной информации о фильме
def get_movie_details_keyboard(movie_id):
    """Клавиатура для детальной информации о фильме"""
    keyboard = [
        [InlineKeyboardButton("🎬 Смотреть", url=f"https://hdrezka.ag/search/?do=search&subaction=search&q={movie_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для детальной информации о сериале
def get_tv_details_keyboard(tv_id, is_subscribed=False):
    """Клавиатура для детальной информации о сериале"""
    keyboard = [
        [InlineKeyboardButton("🎬 Смотреть", url=f"https://hdrezka.ag/search/?do=search&subaction=search&q={tv_id}")]
    ]
    
    # Кнопка подписки/отписки
    if is_subscribed:
        keyboard.append([InlineKeyboardButton("❌ Отписаться от обновлений", callback_data=f"unsubscribe_{tv_id}")])
    else:
        keyboard.append([InlineKeyboardButton("✅ Подписаться на обновления", callback_data=f"subscribe_{tv_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для результатов поиска
def get_search_results_keyboard(results, page=1, total_pages=1):
    """Клавиатура для результатов поиска"""
    keyboard = []
    
    for item in results:
        item_id = item.get("id")
        item_type = item.get("media_type")
        title = item.get("title") or item.get("name")
        
        if item_id and title and item_type in ["movie", "tv"]:
            keyboard.append([InlineKeyboardButton(f"{title}", callback_data=f"view_{item_type}_{item_id}")])
    
    # Добавляем пагинацию
    navigation = []
    
    if page > 1:
        navigation.append(InlineKeyboardButton("◀️ Назад", callback_data=f"search_page_{page-1}"))
    
    navigation.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="page_info"))
    
    if page < total_pages:
        navigation.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"search_page_{page+1}"))
    
    if navigation:
        keyboard.append(navigation)
    
    keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search")])
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для настроек
def get_settings_keyboard(notifications_enabled=True):
    """Клавиатура для настроек"""
    notification_status = "🔔 Уведомления включены" if notifications_enabled else "🔕 Уведомления выключены"
    keyboard = [
        [InlineKeyboardButton(notification_status, callback_data="toggle_notifications")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для списка подписок
def get_subscriptions_keyboard(subscriptions):
    """Клавиатура для списка подписок на сериалы"""
    keyboard = []
    
    if not subscriptions:
        keyboard.append([InlineKeyboardButton("🔍 Найти сериалы", callback_data="search_series")])
    else:
        for series in subscriptions:
            keyboard.append([InlineKeyboardButton(
                f"{series.title}", 
                callback_data=f"view_tv_{series.series_id}"
            )])
    
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для подтверждения действий
def get_confirmation_keyboard(action, item_id):
    """Клавиатура для подтверждения действий"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для рекомендаций
def get_recommendations_keyboard(content_type, content_id):
    """Клавиатура для рекомендаций"""
    keyboard = [
        [InlineKeyboardButton("👍 Показать похожие", callback_data=f"recommend_{content_type}_{content_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)