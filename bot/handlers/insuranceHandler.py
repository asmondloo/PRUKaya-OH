# PruKaya/bot/handlers/insuranceHandler.py
from telebot import types
from bot.utils.supabase_utils import insurance_categories, insurance_products
from bot import telebot_bot

@telebot_bot.message_handler(commands=['listallpolicies'])
def list_all_policies(message):
    markup = types.InlineKeyboardMarkup()
    for category in insurance_categories:
        markup.add(types.InlineKeyboardButton(category['category_name'], callback_data=f"category_{category['id']}"))
    telebot_bot.send_message(message.chat.id, "Select a category:", reply_markup=markup)

@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def show_products(call):
    category_id = int(call.data.split("category_")[1])
    markup = types.InlineKeyboardMarkup()
    
    filtered_products = [product for product in insurance_products if product['category_id'] == category_id]
    
    for product in filtered_products:
        markup.add(types.InlineKeyboardButton(product['product_name'], callback_data=f"product_{product['id']}"))
    
    markup.add(types.InlineKeyboardButton("Back to categories", callback_data="back_to_categories"))
    telebot_bot.edit_message_text(f"Select a product in the category:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)


@telebot_bot.callback_query_handler(func=lambda call: call.data == "back_to_categories")
def back_to_categories(call):
    markup = types.InlineKeyboardMarkup()
    for category in insurance_categories:
        markup.add(types.InlineKeyboardButton(category['category_name'], callback_data=f"category_{category['id']}"))
    telebot_bot.edit_message_text("Select a category:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)


@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def product_selected(call):
    product_id = int(call.data.split("product_")[1])
    
    product = next((p for p in insurance_products if p['id'] == product_id), None)
    
    if product:
        summary = product.get('description', "No summary available.")
        markup = types.InlineKeyboardMarkup()
        telebot_bot.send_message(call.message.chat.id, f"Product: {product['product_name']}\n\nSummary:\n{summary}", reply_markup=markup)
