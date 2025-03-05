import os
import json
from telebot import types
from bot import telebot_bot

# Get the absolute path of the JSON file in the handlers directory
HANDLERS_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.join(HANDLERS_DIR, "resource_data.json")

# Load JSON data
def load_resources():
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

government_resources = load_resources()

@telebot_bot.message_handler(commands=['listresources'])
def list_resources(message):
    markup = types.InlineKeyboardMarkup()
    for category in government_resources:
        markup.add(types.InlineKeyboardButton(category['name'], callback_data=f"cat_{category['id']}"))
    telebot_bot.send_message(message.chat.id, "Select a resource category:", reply_markup=markup)

@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def show_resource_links(call):
    cat_id = int(call.data.split("cat_")[1])
    category = next((cat for cat in government_resources if cat['id'] == cat_id), None)
    
    if category:
        markup = types.InlineKeyboardMarkup()
        for link in category.get('links', []):
            markup.add(types.InlineKeyboardButton(link['name'], callback_data=f"link_{link['id']}"))
        markup.add(types.InlineKeyboardButton("Back to categories", callback_data="back_to_cats"))
        telebot_bot.edit_message_text(
            "Select a link for the resource:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
    else:
        telebot_bot.answer_callback_query(call.id, "Category not found.")

@telebot_bot.callback_query_handler(func=lambda call: call.data == "back_to_cats")
def back_to_categories(call):
    markup = types.InlineKeyboardMarkup()
    for category in government_resources:
        markup.add(types.InlineKeyboardButton(category['name'], callback_data=f"cat_{category['id']}"))
    telebot_bot.edit_message_text(
        "Select a resource category:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('link_'))
def send_resource_guide(call):
    link_id = int(call.data.split("link_")[1])
    selected_link = None
    for category in government_resources:
        for link in category.get('links', []):
            if link['id'] == link_id:
                selected_link = link
                break
        if selected_link:
            break

    if selected_link:
        message_text = f"🔗 *{selected_link['name']}*\n\n📌 {selected_link['description']}\n\n[Click here to visit]({selected_link['url']})"
        telebot_bot.send_message(call.message.chat.id, message_text, parse_mode="Markdown")
    else:
        telebot_bot.answer_callback_query(call.id, "Link not found.")
