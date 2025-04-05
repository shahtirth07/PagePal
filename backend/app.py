# backend/app.py

# --- Imports ---
import os
import sys
import json # For caching results
import hashlib # For creating cache keys
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient # Use synchronous pymongo
from bson import ObjectId
from bson.errors import InvalidId
import re
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough # Keep Passthrough
# Remove RunnableLambda if only used for async calls previously
# from langchain.schema.runnable import RunnableLambda
from langchain.schema.output_parser import StrOutputParser
from scipy.spatial.distance import cosine as cosine_distance # Keep for re-ranking
import numpy as np # Keep for re-ranking
import redis # Import redis

load_dotenv()

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "books"
COLLECTION_NAME = "books"
INDEX_NAME = "vector_index"
EMBEDDING_MODEL = "text-embedding-ada-002"
LLM_MODEL = "gpt-3.5-turbo"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost") # Redis config
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_EXPIRATION_SECONDS = 3600 # Cache results for 1 hour

# --- Check Configuration ---
if not MONGO_URI: sys.exit("Error: MONGO_URI not found in .env file.")
if not os.getenv("OPENAI_API_KEY"): print("Warning: OPENAI_API_KEY not found...")

# --- Initialize Components ---
rag_chain = None
mongo_client = None
mongo_collection = None
embeddings = None
llm = None
redis_client = None

try:
    # --- Redis Client ---
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True) # Decode responses to strings
        redis_client.ping() # Check connection
        print(f"Redis connection successful to {REDIS_HOST}:{REDIS_PORT}.")
    except redis.exceptions.ConnectionError as redis_err:
        print(f"Warning: Redis connection failed: {redis_err}. Caching will be disabled.")
        redis_client = None # Disable caching if connection fails

    # --- MongoDB Client (Synchronous) ---
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    mongo_collection = db[COLLECTION_NAME]
    mongo_client.admin.command('ping')
    print("MongoDB connection successful.")

    # --- LangChain Components ---
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0.1)
    rag_template = """You are PagePal, a helpful assistant discussing the book "{book_title}".
Strictly base your answer ONLY on the following context extracted from the book.
Analyze the context provided. If it directly answers the user's question, provide that answer.
If the context is relevant to the question but doesn't answer it fully, synthesize the information found and state what is available in the text you have access to.
If the context provided is empty or only contains messages like 'Could not find relevant context...', politely inform the user that you couldn't find specific details on that topic within the text for "{book_title}" and suggest they ask about something else covered in the book.
use just little of your general knowledge of the book. **Do not** mention the words 'context', 'documents', or 'database' in your final response.

Context:
{context}

Question: {question}
Answer:"""
    rag_prompt = PromptTemplate.from_template(rag_template)

    # --- Synchronous Retrieval Function with Redis Cache ---
    def retrieve_context(query: str, k: int = 4, filter_criteria: dict = None, rerank_k: int = 5):
        """
        Embeds query, performs vector search in MongoDB, re-ranks, caches result in Redis.
        """
        # Generate cache key (hash of query + filter)
        cache_key_input = f"{query}::{json.dumps(filter_criteria, sort_keys=True)}"
        cache_key = f"context_cache:{hashlib.md5(cache_key_input.encode()).hexdigest()}"

        # Try fetching from cache first
        if redis_client:
            try:
                cached_context = redis_client.get(cache_key)
                if cached_context:
                    print(f"Cache HIT for query: '{query}' with filter: {filter_criteria}")
                    return cached_context # Return cached result directly
            except redis.exceptions.RedisError as redis_err:
                 print(f"Warning: Redis GET error: {redis_err}. Proceeding without cache.")

        print(f"Cache MISS for query: '{query}' with filter: {filter_criteria}")

        # --- If cache miss, perform retrieval ---
        if mongo_collection is None or embeddings is None: raise ValueError("MongoDB or embeddings not initialized.")
        try:
            # (Retrieval logic is the same as app_py_mongodb_v9 - Vector Search + Python Re-ranking)
            query_embedding = embeddings.embed_query(query)
            num_candidates_mongo = k * 5
            search_stage = { '$vectorSearch': { 'index': INDEX_NAME, 'path': 'chunks.embedding', 'queryVector': query_embedding, 'numCandidates': num_candidates_mongo * 10, 'limit': num_candidates_mongo } }
            if filter_criteria: search_stage['$vectorSearch']['filter'] = filter_criteria; print(f"Applying vector search filter: {filter_criteria}")
            pipeline = [ search_stage, { '$project': { '_id': 0, 'title': 1, 'chunks': 1 } } ]
            # Use synchronous aggregate call
            results = list(mongo_collection.aggregate(pipeline))
            print(f"MongoDB $vectorSearch returned {len(results)} candidate document(s).")

            if not results:
                context = "Could not find any potentially relevant documents in the specified book(s)."
            else:
                candidate_chunks = [];
                for doc in results:
                    doc_title = doc.get('title', 'Unknown')
                    for chunk_data in doc.get('chunks', []):
                        if 'text' in chunk_data and 'embedding' in chunk_data: candidate_chunks.append({ 'text': chunk_data['text'], 'embedding': chunk_data['embedding'], 'title': doc_title })
                if not candidate_chunks:
                    context = "Could not find relevant text chunks in the specified book(s)."
                else:
                    print(f"Extracted {len(candidate_chunks)} candidate chunks for re-ranking.")
                    chunk_similarities = []; query_embedding_np = np.array(query_embedding)
                    for chunk in candidate_chunks:
                        chunk_embedding_np = np.array(chunk['embedding']); similarity = 1 - cosine_distance(query_embedding_np, chunk_embedding_np); chunk_similarities.append((similarity, chunk['text'], chunk['title']))
                    chunk_similarities.sort(key=lambda x: x[0], reverse=True); top_chunks = chunk_similarities[:rerank_k]; print(f"Top {len(top_chunks)} re-ranked chunks selected.")
                    context_parts = [];
                    for score, text, title in top_chunks: print(f"  - Score: {score:.4f}, Title: {title}"); context_parts.append(f"Context from '{title}':\n{text}")
                    context = "\n\n---\n\n".join(context_parts)

            print(f"Retrieved Context Length: {len(context)}")
            if not context:
                print("Warning: No context constructed after re-ranking.")
                context = "Could not find relevant context in the specified book(s) after re-ranking." # Ensure fallback
            else:
                print(f"Context Snippet Sent to LLM: {context[:500]}...")

            # Store result in cache if Redis is available
            if redis_client and context:
                 try:
                     redis_client.set(cache_key, context, ex=CACHE_EXPIRATION_SECONDS)
                     print(f"Stored result in Redis cache (key: {cache_key[:15]}...)")
                 except redis.exceptions.RedisError as redis_err:
                      print(f"Warning: Redis SET error: {redis_err}. Failed to cache result.")

            return context

        except Exception as e:
            print(f"Error during MongoDB retrieval or re-ranking: {e}")
            if "index not found" in str(e).lower() or "failed to find search index" in str(e).lower():
                 print(f"CRITICAL Error: Vector Search index '{INDEX_NAME}' not found or misconfigured in Atlas!")
            return f"Error retrieving context from database: {e}"


    # --- RAG Chain (Synchronous) ---
    # Input: {"query": ..., "filter": ..., "book_title": ...}
    rag_chain = (
        {
            # Pass input dict, retrieve_context extracts query/filter
            "context": RunnablePassthrough() | (lambda input_dict: retrieve_context(input_dict['query'], filter_criteria=input_dict.get('filter'))),
            "question": RunnablePassthrough() | (lambda input_dict: input_dict['query']),
            "book_title": RunnablePassthrough() | (lambda input_dict: input_dict.get('book_title', 'the book'))
        }
        | rag_prompt
        | llm
        | StrOutputParser()
    )
    print("RAG components initialized (Synchronous retrieval with Redis Cache).")


except Exception as e:
    print(f"FATAL: Error initializing components: {e}")
    rag_chain = None


# --- Flask App ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints (Keep hello, chat, get_books, get_genres, get_book_details the same logic) ---
# The 'chat' endpoint uses the synchronous rag_chain

@app.route('/api/hello', methods=['GET'])
def hello():
    # ... (same) ...
    return jsonify({"message": "Hello from the PagePal Python backend!"})

@app.route('/api/chat', methods=['POST'])
def chat():
    if not rag_chain: return jsonify({"error": "RAG chain not initialized."}), 500
    data = request.get_json(); query = data.get('query'); book_filter = data.get('book_filter')
    if not query: return jsonify({"error": "Missing 'query' in request body"}), 400
    # Prepare input dict for the synchronous chain
    input_dict = {"query": query, "filter": book_filter, "book_title": book_filter.get("title", "this book") if book_filter else "this book"}
    try:
        print(f"Received query: {query}" + (f" | Filter: {book_filter}" if book_filter else ""))
        # Invoke the synchronous RAG chain
        answer = rag_chain.invoke(input_dict)
        print(f"Generated answer: {answer}")
        return jsonify({"answer": answer})
    except Exception as e: print(f"Error processing chat request: {e}"); return jsonify({"error": "An error occurred processing your request."}), 500

# --- Other endpoints remain the same ---
@app.route('/api/books', methods=['GET'])
def get_books():
    # ... (same as app_py_mongodb_v8_fixed_indent) ...
    if mongo_collection is None: return jsonify({"error": "Database connection not initialized."}), 500
    genre = request.args.get('genre')
    query_filter = {}
    if genre:
        try: regex = re.compile(f'^{re.escape(genre)}$', re.IGNORECASE); query_filter['genre'] = regex; print(f"Fetching books for genre (case-insensitive): {genre}")
        except re.error as re_err: print(f"Error creating regex for genre '{genre}': {re_err}"); query_filter['genre'] = genre; print(f"Regex failed, falling back to exact match for genre: {genre}")
    else: print("Fetching all books")
    try:
        books_cursor = mongo_collection.find(query_filter, {'_id': 1, 'title': 1, 'author': 1, 'genre': 1})
        books_list = []; [books_list.append({**book, '_id': str(book['_id'])}) for book in books_cursor]; print(f"Found {len(books_list)} books."); return jsonify(books_list)
    except Exception as e: print(f"Error fetching books from MongoDB: {e}"); return jsonify({"error": "An error occurred fetching books."}), 500

@app.route('/api/genres', methods=['GET'])
def get_genres():
    # ... (same as app_py_mongodb_v8_fixed_indent) ...
     if mongo_collection is None: return jsonify({"error": "Database connection not initialized."}), 500
     try: print("Fetching distinct genres..."); genres = mongo_collection.distinct("genre", {"genre": {"$ne": None, "$ne": ""}}); print(f"Found genres: {genres}"); return jsonify(sorted(genres))
     except Exception as e: print(f"Error fetching genres from MongoDB: {e}"); return jsonify({"error": "An error occurred fetching genres."}), 500

@app.route('/api/books/<book_id>', methods=['GET'])
def get_book_details(book_id):
    # ... (same as app_py_mongodb_v8_fixed_indent) ...
    if mongo_collection is None: return jsonify({"error": "Database connection not initialized."}), 500
    try: obj_id = ObjectId(book_id)
    except InvalidId: return jsonify({"error": "Invalid book ID format."}), 400
    try:
        print(f"Fetching details for book ID: {book_id}"); book = mongo_collection.find_one({'_id': obj_id}, {'_id': 1, 'title': 1, 'author': 1, 'genre': 1})
        if book: book['_id'] = str(book['_id']); print(f"Found book details: {book}"); return jsonify(book)
        else: return jsonify({"error": "Book not found."}), 404
    except Exception as e: print(f"Error fetching book details from MongoDB: {e}"); return jsonify({"error": "An error occurred fetching book details."}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # Removed the asyncio.run(initialize_mongo()) call
    # Initialization now happens synchronously at the top level try/except block
    port = int(os.environ.get('PORT', 5000))
    # Make sure rag_chain was initialized before running
    if rag_chain is None:
         print("FATAL: RAG Chain failed to initialize. Cannot start Flask app.")
         sys.exit(1)
    app.run(debug=True, port=port)

