from telebot import types
from bot import telebot_bot
from fpdf import FPDF  # Use fpdf2 instead of fpdf
import os
import requests
import markdown  # For Markdown-to-HTML conversion
import html2text  # For HTML-to-plain-text conversion
from rag_pipeline import SavingGoals

user_data = {}

def clean_text_for_pdf(text):
    replacements = {
        "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    return text

def markdown_to_plain_text(markdown_text):
    """
    Converts Markdown content to plain text.
    - First, convert Markdown to HTML using `markdown`.
    - Then, strip HTML tags using `html2text`.
    """
    # Convert Markdown to HTML
    html_content = markdown.markdown(markdown_text)
    # Convert HTML to plain text
    plain_text = html2text.html2text(html_content)
    # Remove excessive newlines and clean up formatting
    plain_text = "\n".join(line.strip() for line in plain_text.splitlines() if line.strip())
    return plain_text

@telebot_bot.message_handler(commands=['generate_report'])
def ask_age(message):
    user_id = message.chat.id
    user_data[user_id] = {}
    telebot_bot.send_message(user_id, "Please enter your age.")
    telebot_bot.register_next_step_handler(message, ask_gender)

def ask_gender(message):
    user_id = message.chat.id
    try:
        user_data[user_id]['age'] = int(message.text)
    except ValueError:
        telebot_bot.send_message(user_id, "Invalid input. Please enter a valid number for your age.")
        return
    telebot_bot.send_message(user_id, "Please enter your gender (Male/Female/Other).")
    telebot_bot.register_next_step_handler(message, ask_monthly_income)

def ask_monthly_income(message):
    user_id = message.chat.id
    user_data[user_id]['gender'] = message.text
    telebot_bot.send_message(user_id, "Please enter your monthly income.")
    telebot_bot.register_next_step_handler(message, ask_expenses)

def ask_expenses(message):
    user_id = message.chat.id
    try:
        user_data[user_id]['monthly_income'] = float(message.text)
    except ValueError:
        telebot_bot.send_message(user_id, "Invalid input. Please enter a valid number for your monthly income.")
        return
    telebot_bot.send_message(user_id, "Please enter your monthly expenses.")
    telebot_bot.register_next_step_handler(message, ask_savings_goal)

def ask_savings_goal(message):
    user_id = message.chat.id
    try:
        user_data[user_id]['expenses'] = float(message.text)
    except ValueError:
        telebot_bot.send_message(user_id, "Invalid input. Please enter a valid number for your monthly expenses.")
        return
    telebot_bot.send_message(user_id, "Please enter your savings goal.")
    telebot_bot.register_next_step_handler(message, generate_report)

def generate_report(message):
    user_id = message.chat.id
    user_data[user_id]['savings_goal'] = message.text
    if not all(user_data[user_id].values()):
        telebot_bot.send_message(user_id, "Insufficient information to generate a report.")
        return
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
    wait_message = telebot_bot.send_message(user_id, "Please wait while the report is generating...")
    API_URL = "http://localhost:5000/generate_report"
    payload = saving_goals.dict()
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
    telebot_bot.delete_message(chat_id=user_id, message_id=wait_message.message_id)
    
    # Convert Markdown to plain text
    cleaned_report_content = clean_text_for_pdf(report_content)
    plain_text_content = markdown_to_plain_text(cleaned_report_content)

    # Generate the PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=12)  # Use Helvetica as the default font
    pdf.cell(0, 10, txt="Personalized Financial Report", ln=True, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=plain_text_content)
    
    # Save the PDF with a name based on the savings goal
    sanitized_savings_goal = "".join(c for c in saving_goals.savings_goal if c.isalnum() or c in (' ', '_')).strip()
    pdf_output_path = f"{sanitized_savings_goal.replace(' ', '_')}_report.pdf"
    pdf.output(pdf_output_path)
    
    # Send the PDF to the user
    with open(pdf_output_path, 'rb') as file:
        telebot_bot.send_document(user_id, file)
    
    # Clean up the temporary PDF file
    os.remove(pdf_output_path)