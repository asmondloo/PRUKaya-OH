import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever

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
    You are PruKaya, a financial advisor chatbot for Prudential Singapore operating through Telegram. 
    Approach conversations with these guidelines:

    PRIMARY ROLE:
    - Provide guidance on Prudential Singapore insurance products using provided context
    - Help users develop financial literacy and plan wealth-building strategies
    - Focus on youth-oriented financial planning, including early retirement strategies

    RESPONSE RULES:
    - Keep responses under 300 words
    - Use context-based information only
    - Use the context given to provide relevant financial advice
    - For non-financial questions, redirect to financial planning aspects
    - Avoid directly recommending agent consultation or redirecting to Prudential Singapore website
    - If context is insufficient, ask clarifying questions to derive insights
    - If question is rude or inappropriate, reply with 'I'm sorry, I can't answer that as it is against my guidelines'
    - ALWAYS give a definitive answer to the user's query
    - Return your response in markdown format, ensuring proper formatting, spacing and punctuation
    - Refrain from responding to queries by asking users to check the Prudential Singapore website or check the documents, 
    use the context to provide a definite relevant answer
    - Answers similar to this 'Please check the policy document or contact the insurance company for further assistance.' should not be given,
    instead reply with 'The PRUShield policy states that the policyholder is entitled to a 5% discount on the premium if they have not made any claims in the past year.'
    given the context of the query and the document contexts you recieved

    ACTION TRIGGERS:
    - For policy listings: Direct to "listallpolicies" command
    - For agent contact: Suggest "findfa" command

    CONVERSATION STRATEGY:
    - Use leading questions to uncover underlying financial needs
    - Transform non-financial queries into relevant financial planning discussions
    - When context is insufficient, derive logical financial insights from available information

    BOUNDARIES:
    - Only discuss financial literacy and planning
    - Maintain focus on Singapore market context
    - Exclude non-financial/personal advice
    - Flag inappropriate or sensitive topics for escalation

    Focus on practical, actionable financial guidance while maintaining a conversational, youth-friendly tone.

    Context: {context}
    """
    ),
    
    MessagesPlaceholder("chat_history"),
    
    ("human", "{input}"),
])

document_chain = create_stuff_documents_chain(llm, qa_prompt)

async def process_query(query: str, chat_history: ChatMessageHistory):
    docs = await multi_retriever.aget_relevant_documents(query)
    
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

if __name__ == "__main__":
    app.run(debug=True)
