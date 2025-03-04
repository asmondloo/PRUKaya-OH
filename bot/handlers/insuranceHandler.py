from telebot import types
from bot.utils.supabase_utils import insurance_providers, insurance_categories, insurance_products
from bot import telebot_bot

# Step 1: Show insurance providers first
@telebot_bot.message_handler(commands=['listallpolicies'])
def list_all_policies(message):
    markup = types.InlineKeyboardMarkup()
    for provider in insurance_providers:
        markup.add(types.InlineKeyboardButton(provider['name'], callback_data=f"provider_{provider['id']}"))
    telebot_bot.send_message(message.chat.id, "Select an insurance provider:", reply_markup=markup)

# Step 2: Handle selection of the insurance provider and show categories
@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('provider_'))
def show_categories(call):
    provider_id = int(call.data.split("provider_")[1])
    markup = types.InlineKeyboardMarkup()
    
    # Filter categories based on provider_id
    filtered_categories = [category for category in insurance_categories if category['id'] in [product['category_id'] for product in insurance_products if product['insurance_provider_id'] == provider_id]]
    
    for category in filtered_categories:
        markup.add(types.InlineKeyboardButton(category['category_name'], callback_data=f"category_{provider_id}_{category['id']}"))
    
    # Adding a "Back to Providers" button
    markup.add(types.InlineKeyboardButton("Back to Providers", callback_data="back_to_providers"))
    
    telebot_bot.edit_message_text(f"Select a category for this provider:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 3: Show products based on selected category and provider
@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def show_products(call):
    provider_id, category_id = map(int, call.data.split("category_")[1].split("_"))
    
    markup = types.InlineKeyboardMarkup()
    
    # Filter products based on both category_id and provider_id
    filtered_products = [product for product in insurance_products if product['category_id'] == category_id and product['insurance_provider_id'] == provider_id]
    
    for product in filtered_products:
        markup.add(types.InlineKeyboardButton(product['product_name'], callback_data=f"product_{product['id']}"))
    
    # Add "Back to Categories" and "Back to Providers" buttons
    markup.add(types.InlineKeyboardButton("Back to categories", callback_data=f"back_to_categories_{provider_id}"))
    markup.add(types.InlineKeyboardButton("Back to Providers", callback_data="back_to_providers"))
    
    telebot_bot.edit_message_text(f"Select a product in the category:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 4: Go back to categories
@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_categories_"))
def back_to_categories(call):
    provider_id = int(call.data.split("_")[3])
    markup = types.InlineKeyboardMarkup()
    
    # Filter categories based on provider_id
    filtered_categories = [category for category in insurance_categories if category['id'] in [product['category_id'] for product in insurance_products if product['insurance_provider_id'] == provider_id]]
    
    for category in filtered_categories:
        markup.add(types.InlineKeyboardButton(category['category_name'], callback_data=f"category_{provider_id}_{category['id']}"))
    
    # Add "Back to Providers" button
    markup.add(types.InlineKeyboardButton("Back to Providers", callback_data="back_to_providers"))
    
    telebot_bot.edit_message_text("Select a category:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 5: Go back to providers
@telebot_bot.callback_query_handler(func=lambda call: call.data == "back_to_providers")
def back_to_providers(call):
    markup = types.InlineKeyboardMarkup()
    for provider in insurance_providers:
        markup.add(types.InlineKeyboardButton(provider['name'], callback_data=f"provider_{provider['id']}"))
    telebot_bot.edit_message_text("Select an insurance provider:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 6: Display product details when selected
@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def product_selected(call):
    product_id = int(call.data.split("product_")[1])
    
    product = next((p for p in insurance_products if p['id'] == product_id), None)
    
    if product:
        summary = product.get('description', "No summary available.")
        markup = types.InlineKeyboardMarkup()
        telebot_bot.send_message(call.message.chat.id, f"Product: {product['product_name']}\n\nSummary:\n{summary}", reply_markup=markup)
