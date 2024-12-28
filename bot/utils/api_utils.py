from dotenv import load_dotenv
import os
import requests
import re

from .logger_utils import setup_logger

load_dotenv(verbose=False)

logger = setup_logger()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

user_conversations = {}  

def clean_output(text):
    cleaned_text = re.sub(r'[*#]', '', text)
    return cleaned_text.strip()

def call_openai_api(prompt, user_id):
    if not prompt:
        return "No prompt provided."

    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append({"role": "human", "content": prompt})

    try:
        API_URL = "http://localhost:5000/query"
        payload = {
            "query": prompt,
            "chat_history": user_conversations[user_id]
        }

        response = requests.post(API_URL, json=payload)
        response.raise_for_status()

        response_data = response.json()
        ai_response = response_data.get("response", "No response received.")
        cleaned_output = clean_output(ai_response)

        user_conversations[user_id].append({"role": "assistant", "content": cleaned_output})
        if "I can't answer that" in cleaned_output:
            logger.warning(f"Flagged response for user {user_id}: {prompt}")
        return cleaned_output

    except Exception as e:
        logger.error(f"Error occurred while processing user query: {e}")
        return "PRUKaya is not available now, please try again later."
