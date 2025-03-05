import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from pydantic import BaseModel

load_dotenv(verbose=False)

app = Flask(__name__)

openai_api_key = os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
llm = ChatOpenAI(model="gpt-4", api_key=openai_api_key)

chromadb_dir = "./chroma_db"
prukaya = Chroma(embedding_function=embeddings, persist_directory=chromadb_dir)
retriever = prukaya.as_retriever()

multi_retriever = MultiQueryRetriever.from_llm(
    retriever=retriever,
    llm=llm
)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """
    You are PRUKaya, an AI-powered financial buddy designed to guide young Singaporeans toward smarter financial decisions. You operate through Telegram and focus on helping users with saving, investing, and insuring in the Singaporean context. You offer insurance advice and information from all Singapore insurance providers, not limited to Prudential products. Approach conversations with the following guidelines:

    PRIMARY ROLE:
    - Provide personalized guidance on savings, investments, and insurance, using relevant context
    - Offer financial literacy support to youth, including explanations of financial terms, savings strategies, investment advice, and insurance options
    - Address challenges young adults face, such as inadequate savings, lack of insurance, and financial complexity
    - Provide information and comparisons from all insurance providers in Singapore to help users make informed decisions

    RESPONSE RULES:
    - Keep responses under 300 words
    - Use context-based information only
    - Provide clear, practical financial advice with actionable steps
    - For non-financial questions, guide users toward relevant financial topics
    - If context is insufficient, ask clarifying questions to derive actionable insights
    - Answer queries with definitive, actionable responses; avoid vague or non-committal answers
    - Always respond in markdown format, ensuring proper formatting and punctuation
    - Avoid recommending agent consultations or directing users to external websites
    - Refrain from responding to non-financial, business finance, or sensitive topics. If asked, say, "I'm sorry, I can't answer that as it is against my guidelines."
    - Provide relevant government resource links or direct access to CPF, IRAS, and other platforms when necessary
    - Be neutral and unbiased, not promoting any specific financial product or service

    ACTION TRIGGERS:
    - For policy listings: Direct to "listallpolicies" command

    CONVERSATION STRATEGY:
    - Use leading questions to uncover financial needs and priorities
    - Transform general queries into discussions on financial planning, savings, investment, or insurance
    - When context is unclear, derive financial insights from available information

    BOUNDARIES:
    - Focus on personal finance and insurance only
    - Maintain relevance to the Singapore market
    - Exclude non-financial/personal advice
    - Flag inappropriate or sensitive topics for escalation

    Focus on practical, actionable advice with a conversational, youth-friendly tone, aiming to make financial planning engaging and understandable.

    Context: {context}
    """
    ),
    
    MessagesPlaceholder("chat_history"),
    
    ("human", "{input}"),
])


document_chain = create_stuff_documents_chain(llm, qa_prompt)

async def process_query(query: str, chat_history: ChatMessageHistory):
    docs = await multi_retriever.aget_relevant_documents(query)

    if not docs:
        response = await llm.agenerate([query])
    else:
        response = await document_chain.ainvoke({
            "input": query,
            "context": docs,
            "chat_history": chat_history.messages
        })
    
    return response


@app.route('/query', methods=['POST'])
async def handle_query():
    data = request.get_json()
    user_query = data.get("query", "")
    
    chat_history = ChatMessageHistory()
    if "chat_history" in data:
        chat_history.add_messages(data["chat_history"])

    response = await process_query(user_query, chat_history)
    
    return jsonify({"response": response})


report_generation_prompt = """
You are a financial savings expert designed to guide young Singaporeans toward smarter financial decisions. Given the user's financial profile in the below variables, analyze their situation and generate a well-structured report. 
The report should be formatted in Markdown for readability and clarity.

Report Requirements:
1. User's Financial Overview
   - Summarize their age, gender, monthly income, and expenses.
   - Highlight key observations regarding their financial standing.

2. Savings & Investment Analysis
   - Evaluate the feasibility of their savings goal based on income and expenses.
   - Identify opportunities for optimizing savings.

3. Personalized Financial Advice
   - Recommend a tailored savings or investment plan.
   - Suggest suitable financial products or strategies.
   - Provide actionable steps to enhance financial stability and growth.

Variables Provided:
- {age}
- {gender}
- {monthly_income}
- {expenses}
- {savings_goal}

Response Rules:
- Keep responses under 500 words.
- Provide clear, practical financial advice with actionable steps.
- Answer must be relevant to Singaporean context and financial products.
- Response must be as if communicating to the user directly, suggesting specific actions and products.
- Be neutral and unbiased. 
- Suggest very specific products or services while maintaining neutrality.
- Use markdown for formatting.
- Avoid recommending agent consultations or directing users to external websites.
"""

class SavingGoals(BaseModel):
    age: int
    gender: str
    monthly_income: float
    expenses: float
    savings_goal: str

from flask import request, jsonify
from pydantic import ValidationError

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        # Parse the JSON payload from the request
        data = request.get_json()

        # Validate the payload using the SavingGoals Pydantic model
        saving_goals = SavingGoals(**data)

        # Format the prompt using the validated inputs
        prompt = report_generation_prompt.format(
            age=saving_goals.age,
            gender=saving_goals.gender,
            monthly_income=saving_goals.monthly_income,
            expenses=saving_goals.expenses,
            savings_goal=saving_goals.savings_goal
        )

        # Generate the report using the LLM
        response = llm.generate([prompt])  # Assuming `llm.generate` is synchronous
        return jsonify({"response": response.generations[0][0].text.strip()})

    except ValidationError as e:
        # Handle validation errors
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except Exception as e:
        # Handle other errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True,  use_reloader=False)
