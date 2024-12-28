from datetime import datetime
from termcolor import colored
from typing import List

from better_profanity import profanity

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot import telebot_bot
from bot.utils.api_utils import call_openai_api
from bot.utils.logger_utils import setup_logger
from bot.handlers import insuranceHandler, agent_handler, modules_handlers

from session_manager import SessionManager


logger = setup_logger()

def contains_inappropriate_content(message):
    profanity.load_censor_words()
    return profanity.contains_profanity(message)

def main():
    logger.info("PruKaya bot is now running.")
    session_manager = SessionManager(timeout_minutes=5)

    @telebot_bot.message_handler(commands=['buyinsurance'])
    def send_welcome(message):
        user_id = message.chat.id
        username = message.chat.username or "Unknown User"
        session = session_manager.get_or_create_session(user_id, username)
        web_app_url = 'https://profound-gingersnap-339331.netlify.app/' 
        markup = InlineKeyboardMarkup()
        web_app_button = InlineKeyboardButton("Shop for Microinsurance", web_app=WebAppInfo(url=web_app_url))
        markup.add(web_app_button)
        telebot_bot.send_message(user_id, "Click the button below to start shopping for microinsurance.", reply_markup=markup)
        logger.info(f"[COMMAND] Session {session.session_id}: User {username} triggered /buyinsurance command.")

    @telebot_bot.message_handler(func=lambda message: True)
    def handle_message(message):
        if message.text.startswith('/'):
            return
        user_id = message.chat.id
        username = message.chat.username or "Unknown User"
        user_message = message.text

        session = session_manager.get_or_create_session(user_id, username)
        
        if session.processing:
            telebot_bot.send_message(user_id, "Please wait until your previous query is processed.")
            return

        if contains_inappropriate_content(user_message):
            telebot_bot.send_message(user_id, "Your message contains inappropriate content and cannot be processed.")
            logger.warning(colored(f"[INAPPROPRIATE] Session {session.session_id}: @{username} - {user_message}", "red"))
            session = session_manager.get_or_create_session(user_id, username)
            return

        logger.info(f"[QUERY] Session {session.session_id}: @{username} - {user_message}")
        telebot_bot.send_chat_action(user_id, 'typing')

        try:
            session.processing = True
            response = call_openai_api(user_message, user_id)
            
            if response == "I'm sorry, I can't answer that as it is against my guidelines":
                logger.warning(colored(f"[FLAGGED] Session {session.session_id}: @{username} - {user_message}", "red"))
                session = session_manager.get_or_create_session(user_id, username)
            
            telebot_bot.send_message(user_id, response)
            
            session_manager.add_to_chat_history(user_id, "user", user_message)
            session_manager.add_to_chat_history(user_id, "assistant", response)
            
        finally:
            session.processing = False

    telebot_bot.polling(none_stop=True, timeout=120)

if __name__ == "__main__":
    main()