import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token="7678148639:AAERgt-8Y3n1ViVzFUNCqGaQj2ppXnqT7XU")
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для новинок с hdrezka.ag. Используй /news для новинок или /subscribe для подписки на сериалы.")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)