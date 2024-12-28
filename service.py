import uuid
from termcolor import colored
from datetime import datetime, timedelta

from better_profanity import profanity

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot import telebot_bot
from bot.utils.api_utils import call_openai_api
from bot.utils.logger_utils import setup_logger
from bot.handlers import insuranceHandler, agent_handler, modules_handlers

logger = setup_logger()
user_sessions = {}
SESSION_TIMEOUT = timedelta(minutes=5)

def clear_expired_sessions():
    now = datetime.now()
    expired_users = [
        user_id for user_id, session in user_sessions.items()
        if now - session['last_active'] > SESSION_TIMEOUT
    ]
    for user_id in expired_users:
        session_id = user_sessions[user_id]['session_id']
        logger.info(f"Session {session_id}: Cleared due to inactivity.")
        del user_sessions[user_id]

def update_session(user_id, username):
    now = datetime.now()
    if user_id not in user_sessions:
        session_id = str(uuid.uuid4())
        user_sessions[user_id] = {'session_id': session_id, 'last_active': now, 'context': []}
        logger.info(f"Session {session_id}: Created for {username}.")
    else:
        session_id = user_sessions[user_id]['session_id']
        user_sessions[user_id]['last_active'] = now
        logger.info(f"Session {session_id}: Refreshed for {username}.")

def contains_inappropriate_content(message):
    profanity.load_censor_words()
    return profanity.contains_profanity(message)

def main():
    logger.info("PruKaya bot is now running.")

    @telebot_bot.message_handler(commands=['buyinsurance'])
    def send_welcome(message):
        user_id = message.chat.id
        username = message.chat.username or "Unknown User"
        update_session(user_id, username)
        web_app_url = 'https://profound-gingersnap-339331.netlify.app/' 
        markup = InlineKeyboardMarkup()
        web_app_button = InlineKeyboardButton("Shop for Microinsurance", web_app=WebAppInfo(url=web_app_url))
        markup.add(web_app_button)
        telebot_bot.send_message(user_id, "Click the button below to start shopping for microinsurance.", reply_markup=markup)
        session_id = user_sessions[user_id]['session_id']
        logger.info(f"Session {session_id}: User {username} triggered /buyinsurance command.")

    @telebot_bot.message_handler(func=lambda message: True)
    def handle_message(message):
        clear_expired_sessions()
        user_id = message.chat.id
        username = message.chat.username or "Unknown User"
        user_message = message.text

        update_session(user_id, username)
        session_id = user_sessions[user_id]['session_id']

        if contains_inappropriate_content(user_message):
            telebot_bot.send_message(user_id, "Your message contains inappropriate content and cannot be processed.")
            logger.warning(colored(f"Session {session_id}: Inappropriate message received from @{username} - {user_message}", "red"))
            return

        logger.info(f"Session {session_id}: Query from @{username} - {user_message}")
        user_sessions[user_id]['context'].append(user_message)
        telebot_bot.send_chat_action(user_id, 'typing')

        response = call_openai_api(user_message, user_id)
        
        if response == "I'm sorry, I can't answer that as it is against my guidelines":
            logger.warning(colored(f"Session {session_id}: Flagged response for @{username} - {user_message}", "red"))

        telebot_bot.send_message(user_id, response)
        user_sessions[user_id]['context'] = []

    telebot_bot.polling(none_stop=True, timeout=120)

if __name__ == "__main__":
    main()
