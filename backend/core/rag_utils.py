import os
import shutil
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Initialize the embedding model
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def ingest_pdf_to_vector_db(file_path: str, user_id: str):
    persist_dir = f"./chroma_db_{user_id}"
    
    # 1. DELETE OLD DATA: Ensures the bot only knows about the LATEST PDF
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
    
    # 2. Load and Split
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(pages)
    
    # 3. Create a fresh Vector Store
    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    # CLEANUP: Remove the temp file after processing
    if os.path.exists(file_path):
        os.remove(file_path)
        
    return vectorstore

def query_vector_db(user_id: str, question: str):
    persist_dir = f"./chroma_db_{user_id}"

    # Check if the database directory actually exists before trying to load it
    if not os.path.exists(persist_dir):
        return ""

    # Load the existing DB
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )

    # Search for the top 3 most relevant chunks
    docs = vectorstore.similarity_search(question, k=3)

    # Combine them into one string
    context_text = "\n\n".join([doc.page_content for doc in docs])
    return context_text