from telebot import types
from bot.utils.supabase_utils import agents, getAgentPicture
from bot import telebot_bot

@telebot_bot.message_handler(commands=['findfa'])
def list_all_agents(message):
    markup = types.InlineKeyboardMarkup()
    for agent in agents:
        markup.add(types.InlineKeyboardButton(
            f"{agent['firstName']} {agent['lastName']}", 
            callback_data=f"agent_{agent['id']}")
        )
    telebot_bot.send_message(message.chat.id, "Select an agent:", reply_markup=markup)

@telebot_bot.callback_query_handler(func=lambda call: call.data.startswith('agent_'))
def show_agent_details(call):
    agent_id = int(call.data.split("_")[1])
    agent = next((a for a in agents if a['id'] == agent_id), None)
    
    if agent:
        pic_name = agent['pictureName']
        pic_url = getAgentPicture(pic_name)
        print(f"Generated URL: {pic_url}")

        if pic_url:
            caption = f"Name: {agent['firstName']} {agent['lastName']}\n" \
                      f"Bio: {agent['bio']}\n" \
                      f"Years of Experience: {agent['yoe']}" 
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"Contact {agent['firstName']} on Telegram", url=f"https://t.me/{agent['telegram']}"))
            telebot_bot.send_photo(call.message.chat.id, pic_url, caption=caption, reply_markup=markup)
        else:
            telebot_bot.send_message(call.message.chat.id, "Sorry, the agent's picture could not be retrieved.")
    else:
        telebot_bot.send_message(call.message.chat.id, "Agent not found.")


