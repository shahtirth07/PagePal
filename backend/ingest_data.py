# backend/ingest_data.py
import os
import shutil # For removing old DB directory
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings # Use the OpenAI integration
from langchain_community.vectorstores import Chroma # Use Chroma vector store
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Path to your book text file
file_path = "data/book1.txt" # <--- MAKE SURE THIS IS YOUR FILE PATH
# Directory to save the Chroma vector store
persist_directory = "chroma_db"

def create_vector_store(file_path, persist_directory):
    """Loads text, chunks it, creates embeddings, and saves to ChromaDB."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file.")
        return False

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return False

    try:
        # 1. Load the document
        print(f"Loading document from: {file_path}")
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        if not documents:
             print("No document content loaded.")
             return False
        print(f"Loaded {len(documents[0].page_content)} characters.")

        # 2. Chunk the document
        print("Chunking document...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks.")

        if not chunks:
            print("No chunks created.")
            return False

        # 3. Create Embeddings and Store in ChromaDB
        print("Creating embeddings and vector store...")
        # Initialize OpenAI embeddings
        # Requires OPENAI_API_KEY in your .env file
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

        # Optional: Remove old database directory if it exists
        if os.path.exists(persist_directory):
            print(f"Removing old database directory: {persist_directory}")
            shutil.rmtree(persist_directory)

        # Create Chroma vector store from documents
        # This will compute embeddings and store them
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory # Directory to save the database
        )

        print(f"Vector store created with {vectordb._collection.count()} documents.")
        print(f"Persisting database to: {persist_directory}")
        # Persisting is often handled automatically by from_documents with persist_directory,
        # but calling persist() ensures it's saved.
        vectordb.persist()
        print("Database persisted.")

        return True

    except Exception as e:
        print(f"An error occurred during vector store creation: {e}")
        return False

# --- Main execution ---
if __name__ == "__main__":
    print(f"Starting ingestion process...")
    success = create_vector_store(file_path, persist_directory)

    if success:
        print("Ingestion process completed successfully.")
    else:
        print("Ingestion process failed.")