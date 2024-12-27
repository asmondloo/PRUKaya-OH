import os

import fitz  

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document

from dotenv import load_dotenv
load_dotenv(verbose=False)

openai_api_key = os.getenv("OPENAI_API_KEY")

parsed = []



MAX_SIZE = 1800
MAX_OVERLAP = 500
RECURSIVE_CHUNKER = RecursiveCharacterTextSplitter(chunk_size=MAX_SIZE, chunk_overlap=MAX_OVERLAP)



def extract_documents(doc):
    paragraphs = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        for para in page.get_text("blocks"):
            paragraphs.append(para[4])
    
    paragraphs = [p.replace("\n", " ") for p in paragraphs]
    whole_text = " ".join(paragraphs)
    
    chunks = RECURSIVE_CHUNKER.split_text(whole_text)
    
    return chunks

for filename in os.listdir('./documents'):
    document_path = os.path.join('./documents', filename)
    if filename.endswith('.pdf'):
        with open(document_path, 'rb') as file:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            chunks = extract_documents(doc)
            parsed.extend(chunks)

docs = [Document(page_content=chunk) for chunk in parsed]

embeddings = OpenAIEmbeddings(api_key=openai_api_key)

chromadb_dir = './chroma_db'
chromadb = Chroma.from_documents(docs, embeddings, persist_directory=chromadb_dir)

print("Chroma vector store created successfully!")
