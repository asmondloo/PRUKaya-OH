import json
from bot import telebot_bot
from telebot import types
import time
import random
import os

# Paths for JSON files
mod = os.path.join(os.path.dirname(__file__), 'learningModules.json')
quiz = os.path.join(os.path.dirname(__file__), 'quizQuestions.json')

# Load the JSON files
with open(mod, 'r') as file:
    learningModules = json.load(file)

with open(quiz, 'r') as file:
    quizQuestions = json.load(file)

# User inputs and progress tracking
user_inputs = {}
userProgress = {}

# Command to start a game
@telebot_bot.message_handler(commands=['playgame'])
def play_game(message):
    chat_id = message.chat.id
    welcome_message = "Test your knowledge about Prudential's insurance products with a KayaTee Mini Game! Use /gamestart to start the quiz and see how much you know! 🧠"
    telebot_bot.send_message(chat_id, text=welcome_message)

# Command to start the quiz
@telebot_bot.message_handler(commands=['gamestart'])
def start_quiz(message):
    chat_id = message.chat.id
    userProgress[chat_id] = {'currentQuestion': 0, 'score': 0}
    send_quiz_question(chat_id)

# Function to send the next quiz question
def send_quiz_question(chat_id):
    user_state = userProgress[chat_id]
    question = quizQuestions[user_state['currentQuestion']]
    
    options = question['options']
    keyboard = types.InlineKeyboardMarkup()
    for option in options:
        button = types.InlineKeyboardButton(text=option, callback_data=option[0])  # Option 'A', 'B', 'C', or 'D'
        keyboard.add(button)
    
    telebot_bot.send_message(chat_id=chat_id, text=f"Question {user_state['currentQuestion'] + 1}: {question['question']}", reply_markup=keyboard)

# Function to handle quiz answers
@telebot_bot.callback_query_handler(func=lambda call: call.data in ['A', 'B', 'C', 'D'])
def handle_quiz_answer(call):
    chat_id = call.message.chat.id

    # Check if chat_id exists in userProgress, if not, initialize it
    if chat_id not in userProgress:
        userProgress[chat_id] = {'currentQuestion': 0, 'score': 0}

    user_state = userProgress[chat_id]

    selected_answer = call.data
    question = quizQuestions[user_state['currentQuestion']]

    if selected_answer == question['correctAnswer']:
        user_state['score'] += 1
        feedback = "Correct! 🎉"
    else:
        feedback = f"Incorrect. The correct answer was {question['correctAnswer']}."

    telebot_bot.answer_callback_query(call.id, text=feedback)
    user_state['currentQuestion'] += 1

    if user_state['currentQuestion'] < len(quizQuestions):
        time.sleep(0.5)  # 0.5 second delay before sending the next question
        send_quiz_question(chat_id)
    else:
        final_message = f"Quiz finished! Your score is {user_state['score']} out of {len(quizQuestions)}. Thank you for participating! 🎉"
        telebot_bot.send_message(chat_id=chat_id, text=final_message)
        del userProgress[chat_id]

# Handle '/learn' command to show learning modules
@telebot_bot.message_handler(commands=['learn'])
def show_modules(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for module in learningModules['modules']:  # Access the 'modules' list in the JSON
        markup.add(types.KeyboardButton(text="Learn " + module['title']))  # Prefix with 'Learn'
    telebot_bot.send_message(message.chat.id, "Select a module to learn:", reply_markup=markup)

# Handle user's selection of a learning module
@telebot_bot.message_handler(func=lambda message: message.text.startswith('Learn '))
def module_details(message):
    module_title = message.text[len('Learn '):]  # Remove the prefix 'Learn '
    module = next((m for m in learningModules['modules'] if m['title'] == module_title), None)  # Find the module
    if module:
        response = "\n\n".join([f"{sub['title']}: {sub['content']}" for sub in module['submodules']])
        telebot_bot.send_message(message.chat.id, response)
        telebot_bot.send_message(message.chat.id, "Type /quiz to take a quiz or /learn to learn another module.")

# Handle '/quiz' command to show quiz modules
@telebot_bot.message_handler(commands=['quiz'])
def quiz_intro(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for title in quizQuestions.keys():
        markup.add(types.KeyboardButton(text="Quiz - " + title))  # Prefix with 'Quiz -'
    telebot_bot.send_message(message.chat.id, "Select a module to take the quiz on:", reply_markup=markup)

# Handle user's selection of a quiz module
@telebot_bot.message_handler(func=lambda message: message.text.startswith('Quiz -'))
def start_quiz(message):
    module_title = message.text[len('Quiz - '):].strip()  # Remove the prefix 'Quiz -' and strip any extra spaces
    if module_title in quizQuestions:
        chat_id = message.chat.id
        userProgress[chat_id] = {
            'currentQuestion': 0,
            'score': 0,
            'questions': random.sample(quizQuestions[module_title], min(len(quizQuestions[module_title]), 4))  # Safely handle fewer questions
        }
        send_quiz_question(chat_id)
    else:
        telebot_bot.send_message(message.chat.id, f"No questions available for the module: {module_title}. Please select a different module.")

# Send a quiz question to the user
def send_quiz_question(chat_id):
    user_state = userProgress[chat_id]
    question = user_state['questions'][user_state['currentQuestion']]
    
    options = question['options']
    keyboard = types.InlineKeyboardMarkup()
    for idx, option in enumerate(options):
        button = types.InlineKeyboardButton(text=option, callback_data=str(idx))
        keyboard.add(button)
    
    telebot_bot.send_message(chat_id=chat_id, text=f"Question {user_state['currentQuestion'] + 1}: {question['question']}", reply_markup=keyboard)

# Handle user's answer to the quiz question
@telebot_bot.callback_query_handler(func=lambda call: call.data.isdigit())
def handle_quiz_answer(call):
    chat_id = call.message.chat.id
    user_state = userProgress[chat_id]

    selected_index = int(call.data)  # Get index of selected option
    question = user_state['questions'][user_state['currentQuestion']]
    correct_answer_index = ord(question['correctAnswer']) - ord('A')  # Convert 'A', 'B', 'C', 'D' to 0, 1, 2, 3

    if selected_index == correct_answer_index:
        user_state['score'] += 1
        feedback = "Correct! 🎉"
    else:
        correct_option = question['options'][correct_answer_index]
        feedback = f"Incorrect. The correct answer was {correct_option}."

    telebot_bot.answer_callback_query(call.id, text=feedback)
    user_state['currentQuestion'] += 1

    if user_state['currentQuestion'] < len(user_state['questions']):
        time.sleep(0.5)  # Short delay before sending the next question
        send_quiz_question(chat_id)
    else:
        final_message = f"Quiz finished! Your score is {user_state['score']} out of {len(user_state['questions'])}. Thank you for participating! 🎉"
        telebot_bot.send_message(chat_id, text=final_message)
        del userProgress[chat_id]
