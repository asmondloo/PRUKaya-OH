from telebot import types
from bot import telebot_bot
from fpdf import FPDF
import os
import requests
from rag_pipeline import SavingGoals  # Import the Pydantic model

# Dictionary to store user data temporarily
user_data = {}

# Step 1: Ask for age when /start or /generate_report command is issued
@telebot_bot.message_handler(commands=['generate_report'])
def ask_age(message):
    user_id = message.chat.id
    user_data[user_id] = {}  # Initialize user data for this chat
    telebot_bot.send_message(user_id, "Please enter your age.")
    telebot_bot.register_next_step_handler(message, ask_gender)

# Step 2: Ask for gender after receiving age
def ask_gender(message):
    user_id = message.chat.id
    try:
        user_data[user_id]['age'] = int(message.text)  # Convert age to integer
    except ValueError:
        telebot_bot.send_message(user_id, "Invalid input. Please enter a valid number for your age.")
        return
    telebot_bot.send_message(user_id, "Please enter your gender (Male/Female/Other).")
    telebot_bot.register_next_step_handler(message, ask_monthly_income)

# Step 3: Ask for monthly income after receiving gender
def ask_monthly_income(message):
    user_id = message.chat.id
    user_data[user_id]['gender'] = message.text
    telebot_bot.send_message(user_id, "Please enter your monthly income.")
    telebot_bot.register_next_step_handler(message, ask_expenses)

# Step 4: Ask for expenses after receiving monthly income
def ask_expenses(message):
    user_id = message.chat.id
    try:
        user_data[user_id]['monthly_income'] = float(message.text)  # Convert income to float
    except ValueError:
        telebot_bot.send_message(user_id, "Invalid input. Please enter a valid number for your monthly income.")
        return
    telebot_bot.send_message(user_id, "Please enter your monthly expenses.")
    telebot_bot.register_next_step_handler(message, ask_savings_goal)

# Step 5: Ask for savings goal after receiving expenses
def ask_savings_goal(message):
    user_id = message.chat.id
    try:
        user_data[user_id]['expenses'] = float(message.text)  # Convert expenses to float
    except ValueError:
        telebot_bot.send_message(user_id, "Invalid input. Please enter a valid number for your monthly expenses.")
        return
    telebot_bot.send_message(user_id, "Please enter your savings goal.")
    telebot_bot.register_next_step_handler(message, generate_report)

# Step 6: Generate the report and send PDF
def generate_report(message):
    user_id = message.chat.id
    user_data[user_id]['savings_goal'] = message.text

    # Validate all required fields are provided
    if not all(user_data[user_id].values()):
        telebot_bot.send_message(user_id, "Insufficient information to generate a report.")
        return

    # Create a SavingGoals object for validation
    try:
        saving_goals = SavingGoals(
            age=user_data[user_id]['age'],
            gender=user_data[user_id]['gender'],
            monthly_income=user_data[user_id]['monthly_income'],
            expenses=user_data[user_id]['expenses'],
            savings_goal=user_data[user_id]['savings_goal']
        )
    except ValueError as e:
        telebot_bot.send_message(user_id, f"Invalid input: {str(e)}")
        return

    # Send a "Please wait" message
    wait_message = telebot_bot.send_message(user_id, "Please wait while the report is generating...")

    # Call the generate_report API
    API_URL = "http://localhost:5000/generate_report"
    payload = saving_goals.dict()  # Convert the Pydantic model to a dictionary

    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            report_content = response.json().get("response", "No report content available.")
        else:
            telebot_bot.send_message(user_id, "Failed to generate the report. Please try again later.")
            return
    except Exception as e:
        telebot_bot.send_message(user_id, f"An error occurred while generating the report: {str(e)}")
        return

    # Delete the "Please wait" message
    telebot_bot.delete_message(chat_id=user_id, message_id=wait_message.message_id)

    # Generate the PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16, style='B')
    pdf.cell(200, 10, txt="Personalized Financial Report", ln=True, align='C')
    pdf.ln(10)  # Add some space
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"Report Details:\n{report_content}")

    # Save the PDF with a name based on the savings goal
    sanitized_savings_goal = "".join(c for c in saving_goals.savings_goal if c.isalnum() or c in (' ', '_')).strip()
    pdf_output_path = f"{sanitized_savings_goal.replace(' ', '_')}_report.pdf"
    pdf.output(pdf_output_path)

    # Send the PDF to the user
    with open(pdf_output_path, 'rb') as file:
        telebot_bot.send_document(user_id, file)

    # Clean up the temporary PDF file
    os.remove(pdf_output_path)