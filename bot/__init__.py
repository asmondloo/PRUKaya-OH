from .config import BOT_TOKEN
from telebot import TeleBot


telebot_bot = TeleBot(BOT_TOKEN, parse_mode=None, threaded=False)