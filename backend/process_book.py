import os
import sys
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# --- Config ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "books"
CHUNK_PREVIEW_SIZE = 3000
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# --- Load Book ---
def load_book(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".pdf":
        loader = PyPDFLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    
    docs = loader.load()
    if not docs:
        raise ValueError("No content loaded.")
    
    full_text = "\n".join(doc.page_content for doc in docs)
    return docs, full_text

# --- Extract Metadata from AI ---
def extract_metadata(text):
    llm = ChatOpenAI(model="gpt-4", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that extracts book metadata."),
        ("user", "Given the following content from a book, extract:\n"
                 "- Title of the book\n"
                 "- Author name(s)\n"
                 "- Genre classification\n\n"
                 "Respond in JSON format with keys: title, author, genre.\n\n"
                 "Book Content:\n{text}")
    ])
    chain = prompt | llm

    result = chain.invoke({"text": text[:CHUNK_PREVIEW_SIZE]})
    try:
        return json.loads(result.content)
    except json.JSONDecodeError:
        print("⚠️ Could not parse JSON from model.")
        print("Raw output:", result.content)
        raise

# --- Chunk and Embed ---
def chunk_and_embed(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)
    if not chunks:
        raise ValueError("No chunks generated.")

    texts = [chunk.page_content for chunk in chunks]

    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectors = embeddings.embed_documents(texts)

    return texts, vectors

# --- Store Everything in MongoDB ---
def store_in_mongo(metadata, texts, vectors, file_path):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db.books

    doc = {
        "file_path": file_path,
        "title": metadata.get("title"),
        "author": metadata.get("author"),
        "genre": metadata.get("genre"),
        "chunks": [
            {"text": text, "embedding": vector}
            for text, vector in zip(texts, vectors)
        ]
    }

    result = collection.insert_one(doc)
    print(f"✅ Book stored in MongoDB with _id: {result.inserted_id}")
    return result.inserted_id

# --- Main Pipeline ---
def process_book(file_path):
    print(f"📘 Processing book: {file_path}")

    docs, full_text = load_book(file_path)
    metadata = extract_metadata(full_text)
    print("🧠 Metadata extracted:", metadata)

    texts, vectors = chunk_and_embed(docs)
    print(f"🔢 Embedded {len(vectors)} chunks.")

    mongo_id = store_in_mongo(metadata, texts, vectors, file_path)
    return mongo_id

# --- Run from CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_book.py <path_to_book>")
        sys.exit(1)

    process_book(sys.argv[1])