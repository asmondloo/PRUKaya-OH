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
    
import aiohttp  # For async HTTP requests
import asyncio

async def call_generate_report_api(user_profile):
    """
    Calls the generate_report API to get a personalized financial report.
    
    Args:
        user_profile (dict): A dictionary containing user data (age, gender, monthly_income, expenses, savings_goal).
    
    Returns:
        str: The generated report text or an error message.
    """
    try:
        # Define the API URL
        API_URL = "http://localhost:5000/generate_report"
        
        # Prepare the payload
        payload = {
            "age": user_profile.get("age"),
            "gender": user_profile.get("gender"),
            "monthly_income": user_profile.get("monthly_income"),
            "expenses": user_profile.get("expenses"),
            "savings_goal": user_profile.get("savings_goal")
        }

        # Make the asynchronous POST request to the API
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload) as response:
                if response.status == 200:
                    response_data = await response.text()  # Assuming the API returns plain text
                    return response_data.strip()
                else:
                    logger.error(f"API returned status code {response.status}")
                    return "Failed to generate the report. Please try again later."

    except Exception as e:
        logger.error(f"Error occurred while generating report: {e}")
        return "Failed to generate the report. Please try again later."


def clear_conversation_history(user_id):
        if user_id in user_conversations:
            del user_conversations[user_id]
            logger.info(f"Conversation history cleared for user {user_id}.")
        else:
            logger.info(f"No conversation history found for user {user_id}.")
