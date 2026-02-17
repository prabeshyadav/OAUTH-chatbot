from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_core.text_splitter import RecursiveCharacterTextSplitter
# Modern LangChain style
from langchain_text_splitters import RecursiveCharacterTextSplitter


import os

# Initialize the embedding model (converts text to vectors)
# NEW/STABLE (As of 2026)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def ingest_pdf_to_vector_db(file_path: str, user_id: str):
    # 1. Load and Split
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(pages)
    
    # 2. Create a local Vector Store for this user
    # This creates a folder named 'db_{user_id}' to store the data
    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings,
        persist_directory=f"./chroma_db_{user_id}"
    )
    return vectorstore

def query_vector_db(user_id: str, question: str):
    # Load the existing DB
    vectorstore = Chroma(
        persist_directory=f"./chroma_db_{user_id}", 
        embedding_function=embeddings
    )
    
    # Search for the top 3 most relevant chunks
    docs = vectorstore.similarity_search(question, k=3)
    
    # Combine them into one string
    context_text = "\n\n".join([doc.page_content for doc in docs])
    return context_text