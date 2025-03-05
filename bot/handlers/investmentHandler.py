from telebot import types
from bot.utils.supabase_utils import financial_categories, financial_products, banks
from bot import telebot_bot

# Step 1: Show financial product categories
@telebot_bot.message_handler(commands=['listallfinancialproducts'])
def list_all_financial_products(message):
    markup = types.InlineKeyboardMarkup()
    
    # Show financial product categories
    for category in financial_categories:
        markup.add(types.InlineKeyboardButton(category['category_name'], callback_data=f"financial_category_{category['id']}"))
    
    telebot_bot.send_message(message.chat.id, "Select a financial product category:", reply_markup=markup)

# Step 2: Handle selection of the financial category
@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('financial_category_'))
def handle_category_selection(call):
    category_id = int(call.data.split("financial_category_")[1])
    
    # Check if the category is government-backed (bank_id is null for all products in this category)
    is_government_backed = all(product['bank_id'] is None for product in financial_products if product['category_id'] == category_id)
    
    if is_government_backed:
        # Skip showing banks and directly show products
        show_government_backed_products(call, category_id)
    else:
        # Show banks for non-government-backed categories
        show_banks(call, category_id)

# Step 3: Show banks for non-government-backed categories
def show_banks(call, category_id):
    markup = types.InlineKeyboardMarkup()
    
    # Show banks for the selected category
    for bank in banks:
        markup.add(types.InlineKeyboardButton(bank['bank_name'], callback_data=f"financial_bank_{category_id}_{bank['id']}"))
    
    # Add "Back to Categories" button
    markup.add(types.InlineKeyboardButton("Back to Categories", callback_data="financial_back_to_categories"))
    
    telebot_bot.edit_message_text(f"Select a bank for this category:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 4: Show government-backed products directly
def show_government_backed_products(call, category_id):
    markup = types.InlineKeyboardMarkup()
    
    # Filter products for the selected category where bank_id is null
    filtered_products = [product for product in financial_products if product['category_id'] == category_id and product['bank_id'] is None]
    
    for product in filtered_products:
        markup.add(types.InlineKeyboardButton(product['product_name'], callback_data=f"financial_product_{product['id']}"))
    
    # Add "Back to Categories" button
    markup.add(types.InlineKeyboardButton("Back to Categories", callback_data="financial_back_to_categories"))
    
    telebot_bot.edit_message_text(f"Select a government-backed product:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 5: Show financial products based on selected bank and category
@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('financial_bank_'))
def show_financial_products(call):
    category_id, bank_id = map(int, call.data.split("financial_bank_")[1].split("_"))
    
    markup = types.InlineKeyboardMarkup()
    
    # Filter products based on both category_id and bank_id
    filtered_products = [product for product in financial_products if product['category_id'] == category_id and product['bank_id'] == bank_id]
    
    for product in filtered_products:
        markup.add(types.InlineKeyboardButton(product['product_name'], callback_data=f"financial_product_{product['id']}"))
    
    # Add "Back to Banks" and "Back to Categories" buttons
    markup.add(types.InlineKeyboardButton("Back to Banks", callback_data=f"financial_back_to_banks_{category_id}"))
    markup.add(types.InlineKeyboardButton("Back to Categories", callback_data="financial_back_to_categories"))
    
    telebot_bot.edit_message_text(f"Select a financial product for this bank:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 6: Go back to categories
@telebot_bot.callback_query_handler(func=lambda call: call.data == "financial_back_to_categories")
def back_to_categories(call):
    markup = types.InlineKeyboardMarkup()
    
    # Show financial product categories again
    for category in financial_categories:
        markup.add(types.InlineKeyboardButton(category['category_name'], callback_data=f"financial_category_{category['id']}"))
    
    telebot_bot.edit_message_text("Select a financial product category:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 7: Go back to banks
@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith("financial_back_to_banks_"))
def back_to_banks(call):
    category_id = int(call.data.split("_")[4])  # Adjusted index for the new prefix
    markup = types.InlineKeyboardMarkup()
    
    # Show banks for the selected category
    for bank in banks:
        markup.add(types.InlineKeyboardButton(bank['bank_name'], callback_data=f"financial_bank_{category_id}_{bank['id']}"))
    
    # Add "Back to Categories" button
    markup.add(types.InlineKeyboardButton("Back to Categories", callback_data="financial_back_to_categories"))
    
    telebot_bot.edit_message_text(f"Select a bank for this category:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# Step 8: Display financial product details when selected
@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('financial_product_'))
def financial_product_selected(call):
    product_id = int(call.data.split("financial_product_")[1])
    
    product = next((p for p in financial_products if p['id'] == product_id), None)
    
    if product:
        summary = product.get('description', "No summary available.")
        markup = types.InlineKeyboardMarkup()
        telebot_bot.send_message(call.message.chat.id, f"Financial Product: {product['product_name']}\n\nSummary:\n{summary}", reply_markup=markup)