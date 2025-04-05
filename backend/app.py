# backend/app.py
import os
import sys
from flask import Flask, jsonify, request, abort
from flask_cors import CORS # Make sure flask-cors is installed
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import re

# --- LangChain Imports ---
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

load_dotenv()

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "books"
COLLECTION_NAME = "books"
INDEX_NAME = "vector_index" # Name of your Vector Search Index in Atlas
EMBEDDING_MODEL = "text-embedding-ada-002"
LLM_MODEL = "gpt-3.5-turbo"

# --- Check Configuration ---
if not MONGO_URI:
    print("Error: MONGO_URI not found in .env file.")
    sys.exit(1)
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in .env file. LLM/Embedding calls might fail.")

# --- Initialize Components ---
rag_chain = None
mongo_client = None
mongo_collection = None
embeddings = None
llm = None

try:
    # Initialize MongoDB Client
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    mongo_collection = db[COLLECTION_NAME]
    print(f"Attempting to connect to MongoDB: {DB_NAME}.{COLLECTION_NAME}")
    mongo_client.admin.command('ping') # Check connection
    print("MongoDB connection successful.")

    # Initialize Embeddings
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # Initialize LLM
    llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0)

    # --- RAG Prompt Template ---
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    Answer:"""
    prompt = PromptTemplate.from_template(template)

    # --- Manual Retrieval Function ---
    def retrieve_context(query: str, k: int = 4, filter_criteria: dict = None):
        """Embeds query and performs vector search in MongoDB, with optional filtering."""
        # CORRECTED CHECK: Use 'is None'
        if mongo_collection is None or embeddings is None:
             raise ValueError("MongoDB collection or embeddings not initialized.")
        try:
            query_embedding = embeddings.embed_query(query)

            search_stage = {
                '$vectorSearch': {
                    'index': INDEX_NAME,
                    'path': 'chunks.embedding',
                    'queryVector': query_embedding,
                    'numCandidates': k * 20,
                    'limit': k
                }
            }
            if filter_criteria:
                 search_stage['$vectorSearch']['filter'] = filter_criteria
                 print(f"Applying vector search filter: {filter_criteria}")

            pipeline = [
                search_stage,
                {
                    '$project': {
                        '_id': 0,
                        'title': 1,
                        'chunks': 1,
                        'score': { '$meta': 'vectorSearchScore' }
                    }
                }
            ]

            results = list(mongo_collection.aggregate(pipeline))

            # --- Context Extraction (Simplistic) ---
            context_parts = []
            for doc in results:
                doc_title = doc.get('title', 'Unknown')
                chunk_texts = [chunk.get('text', '') for chunk in doc.get('chunks', [])]
                context_parts.append(f"Context from '{doc_title}':\n" + "\n".join(chunk_texts[:10])) # Limit context length?

            context = "\n\n---\n\n".join(context_parts)

            if not context:
                 print("Warning: No context retrieved from vector search.")
                 return "Could not find relevant context in the specified book(s)."
            return context

        except Exception as e:
            print(f"Error during MongoDB retrieval: {e}")
            if "index not found" in str(e).lower():
                 print(f"Error: Ensure Vector Search index '{INDEX_NAME}' exists and is ready.")
            return f"Error retrieving context from database: {e}"

    # --- RAG Chain using LCEL with manual retrieval ---
    rag_chain = (
        {
            "context": RunnablePassthrough() | (lambda input_dict: retrieve_context(input_dict['query'], filter_criteria=input_dict.get('filter'))),
            "question": RunnablePassthrough() | (lambda input_dict: input_dict['query'])
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    print("RAG components initialized (using manual MongoDB retrieval).")

except Exception as e:
    print(f"FATAL: Error initializing RAG components: {e}")
    rag_chain = None


# --- Flask App ---
app = Flask(__name__)
CORS(app) # Enable CORS

# --- API Endpoints ---

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello from the PagePal Python backend!"})

@app.route('/api/chat', methods=['POST'])
def chat():
    if not rag_chain:
         return jsonify({"error": "RAG chain not initialized. Check backend logs."}), 500

    data = request.get_json()
    query = data.get('query')
    book_filter = data.get('book_filter')

    if not query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    try:
        print(f"Received query: {query}" + (f" | Filter: {book_filter}" if book_filter else ""))
        input_dict = {"query": query, "filter": book_filter}
        answer = rag_chain.invoke(input_dict)
        print(f"Generated answer: {answer}")
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"Error processing chat request: {e}")
        return jsonify({"error": "An error occurred processing your request."}), 500


@app.route('/api/books', methods=['GET'])
def get_books():
    if mongo_collection is None:
         return jsonify({"error": "Database connection not initialized."}), 500

    genre = request.args.get('genre')
    query_filter = {}
    if genre:
        # --- MODIFICATION START ---
        # Use case-insensitive regex for matching genre
        try:
            # Create a regex pattern for exact match, ignoring case
            regex_pattern = f'^{re.escape(genre)}$'
            regex = re.compile(regex_pattern, re.IGNORECASE)
            query_filter['genre'] = regex
            print(f"Fetching books for genre (case-insensitive): {genre}")
        except re.error as re_err:
             print(f"Error creating regex for genre '{genre}': {re_err}")
             # Fallback or return error? Let's fallback to exact match for safety
             query_filter['genre'] = genre
             print(f"Regex failed, falling back to exact match for genre: {genre}")
        # --- MODIFICATION END ---
    else:
        print("Fetching all books")

    try:
        # Find books matching the filter, projecting only necessary fields
        # Convert ObjectId to string for JSON serialization
        books_cursor = mongo_collection.find(
            query_filter,
            {'_id': 1, 'title': 1, 'author': 1, 'genre': 1}
        )
        books_list = []
        for book in books_cursor:
            book['_id'] = str(book['_id']) # Convert ObjectId to string
            books_list.append(book)

        print(f"Found {len(books_list)} books.")
        return jsonify(books_list)

    except Exception as e:
        print(f"Error fetching books from MongoDB: {e}")
        return jsonify({"error": "An error occurred fetching books."}), 500

@app.route('/api/genres', methods=['GET'])
def get_genres():
    # CORRECTED CHECK: Use 'is None'
    if mongo_collection is None:
         return jsonify({"error": "Database connection not initialized."}), 500
    try:
        print("Fetching distinct genres...")
        genres = mongo_collection.distinct("genre", {"genre": {"$ne": None, "$ne": ""}})
        print(f"Found genres: {genres}")
        return jsonify(sorted(genres))
    except Exception as e:
        print(f"Error fetching genres from MongoDB: {e}")
        return jsonify({"error": "An error occurred fetching genres."}), 500

@app.route('/api/books/<book_id>', methods=['GET'])
def get_book_details(book_id):
    # CORRECTED CHECK: Use 'is None'
    if mongo_collection is None:
        return jsonify({"error": "Database connection not initialized."}), 500

    try:
        obj_id = ObjectId(book_id)
    except InvalidId:
        print(f"Invalid book ID format received: {book_id}")
        return jsonify({"error": "Invalid book ID format."}), 400

    try:
        print(f"Fetching details for book ID: {book_id}")
        book = mongo_collection.find_one(
            {'_id': obj_id},
            {'_id': 1, 'title': 1, 'author': 1, 'genre': 1}
        )

        if book:
            book['_id'] = str(book['_id'])
            print(f"Found book details: {book}")
            return jsonify(book)
        else:
            print(f"Book not found for ID: {book_id}")
            return jsonify({"error": "Book not found."}), 404

    except Exception as e:
        print(f"Error fetching book details from MongoDB: {e}")
        return jsonify({"error": "An error occurred fetching book details."}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
