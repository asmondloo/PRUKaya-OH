import telebot
from bot import telebot_bot
from bot.utils.supabase_utils import all_users

def send_notification_to_all_users():
    try:
        if not all_users:
            print("No users found in the database.")
            return
        
        # Prompt admin for a message
        message_text = input("Enter the message to send: ").strip()
        
        if not message_text:
            print("Message cannot be empty.")
            return

        for user in all_users:
            user_id = user["user_id"]
            try:
                telebot_bot.send_message(user_id, message_text)
                print(f"✅ Message sent to user {user_id}")
            except Exception as e:
                print(f"❌ Failed to send message to {user_id}: {e}")

    except Exception as e:
        print(f"Error fetching users: {e}")

# Run the function when script is executed
if __name__ == "__main__":
    send_notification_to_all_users()
