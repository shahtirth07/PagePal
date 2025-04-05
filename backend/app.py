# backend/app.py

# --- Add these imports at the top ---
from scipy.spatial.distance import cosine as cosine_distance
import numpy as np
# --- Keep all other existing imports ---
import os
import sys
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import re
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# ... (Keep Configuration, Check Configuration, and Initialization blocks the same as v8) ...
# --- Make sure mongo_collection and embeddings are initialized in the try block ---
load_dotenv()

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "books"
COLLECTION_NAME = "books"
INDEX_NAME = "vector_index"
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
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    mongo_collection = db[COLLECTION_NAME]
    print(f"Attempting to connect to MongoDB: {DB_NAME}.{COLLECTION_NAME}")
    mongo_client.admin.command('ping')
    print("MongoDB connection successful.")
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0)
    template = """Answer the question based only on the following context:
{context}

Question: {question}
Answer:"""
    prompt = PromptTemplate.from_template(template)

    # --- REVISED Manual Retrieval Function with Re-Ranking ---
    def retrieve_context(query: str, k: int = 4, filter_criteria: dict = None, rerank_k: int = 3):
        """
        Embeds query, performs vector search in MongoDB, retrieves candidate chunks,
        re-ranks them based on cosine similarity in Python, and returns the top rerank_k chunks.
        """
        if mongo_collection is None or embeddings is None:
            print("Error: MongoDB collection or embeddings not initialized in retrieve_context.")
            raise ValueError("MongoDB collection or embeddings not initialized.")
        try:
            print(f"Retrieving context for query: '{query}' with filter: {filter_criteria}")
            query_embedding = embeddings.embed_query(query)

            # Step 1: Initial Candidate Retrieval using $vectorSearch
            # Retrieve more candidates initially (e.g., k * 5) to give re-ranking more options
            num_candidates_mongo = k * 5
            search_stage = {
                '$vectorSearch': {
                    'index': INDEX_NAME,
                    'path': 'chunks.embedding',
                    'queryVector': query_embedding,
                    'numCandidates': num_candidates_mongo * 10, # Increase oversampling for $vectorSearch
                    'limit': num_candidates_mongo # Limit documents returned by $vectorSearch
                }
            }
            if filter_criteria:
                search_stage['$vectorSearch']['filter'] = filter_criteria
                print(f"Applying vector search filter: {filter_criteria}")

            pipeline = [
                search_stage,
                { '$project': { '_id': 0, 'title': 1, 'chunks': 1 } } # Project needed fields
            ]

            results = list(mongo_collection.aggregate(pipeline))
            print(f"MongoDB $vectorSearch returned {len(results)} candidate document(s).")

            if not results:
                print("Warning: No documents returned from initial vector search.")
                return "Could not find any potentially relevant documents in the specified book(s)."

            # Step 2: Extract all candidate chunks and their embeddings from results
            candidate_chunks = []
            for doc in results:
                doc_title = doc.get('title', 'Unknown')
                for chunk_data in doc.get('chunks', []):
                    if 'text' in chunk_data and 'embedding' in chunk_data:
                        candidate_chunks.append({
                            'text': chunk_data['text'],
                            'embedding': chunk_data['embedding'],
                            'title': doc_title # Keep track of source title
                        })

            if not candidate_chunks:
                 print("Warning: No valid chunks found in the retrieved documents.")
                 return "Could not find relevant text chunks in the specified book(s)."

            print(f"Extracted {len(candidate_chunks)} candidate chunks for re-ranking.")

            # Step 3: Calculate Cosine Similarity in Python & Re-rank
            # Cosine Similarity = 1 - Cosine Distance
            chunk_similarities = []
            for chunk in candidate_chunks:
                # Ensure embedding is a numpy array for scipy
                chunk_embedding_np = np.array(chunk['embedding'])
                query_embedding_np = np.array(query_embedding)
                # Calculate similarity (higher is better)
                similarity = 1 - cosine_distance(query_embedding_np, chunk_embedding_np)
                chunk_similarities.append((similarity, chunk['text'], chunk['title']))

            # Sort by similarity score in descending order
            chunk_similarities.sort(key=lambda x: x[0], reverse=True)

            # Step 4: Select Top 'rerank_k' chunks for context
            top_chunks = chunk_similarities[:rerank_k]
            print(f"Top {len(top_chunks)} re-ranked chunks selected.")

            # Step 5: Format context
            context_parts = []
            for score, text, title in top_chunks:
                print(f"  - Score: {score:.4f}, Title: {title}") # Log score of selected chunks
                context_parts.append(f"Context from '{title}':\n{text}")

            context = "\n\n---\n\n".join(context_parts)

            # --- Log Extracted Context ---
            print(f"Retrieved Context Length: {len(context)}")
            if not context:
                print("Warning: No context constructed after re-ranking.")
                # This shouldn't happen if top_chunks is populated, but good fallback
                return "Could not find relevant context in the specified book(s) after re-ranking."
            else:
                print(f"Context Snippet Sent to LLM: {context[:500]}...")
            # --- End Log Extracted Context ---

            return context

        except Exception as e:
            print(f"Error during MongoDB retrieval or re-ranking: {e}")
            if "index not found" in str(e).lower():
                 print(f"Error: Ensure Vector Search index '{INDEX_NAME}' exists and is ready.")
            # Add more specific error checking if needed
            return f"Error retrieving context from database: {e}"


    # --- RAG Chain (remains the same, uses the improved retrieve_context) ---
    rag_chain = (
        {
            "context": RunnablePassthrough() | (lambda input_dict: retrieve_context(input_dict['query'], filter_criteria=input_dict.get('filter'))),
            "question": RunnablePassthrough() | (lambda input_dict: input_dict['query'])
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    print("RAG components initialized (using manual MongoDB retrieval with re-ranking).")

except Exception as e:
    print(f"FATAL: Error initializing RAG components: {e}")
    rag_chain = None

# --- Flask App ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints (Keep hello, chat, get_books, get_genres, get_book_details the same as v5) ---
# ... (Paste the full endpoint code from app_py_mongodb_v8_fixed_indent here) ...
@app.route('/api/hello', methods=['GET'])
def hello():
    # ... (same as before) ...
    return jsonify({"message": "Hello from the PagePal Python backend!"})

@app.route('/api/chat', methods=['POST'])
def chat():
    # ... (same as before - calls rag_chain.invoke) ...
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
    # ... (same as before - with case-insensitive regex) ...
    if mongo_collection is None:
         return jsonify({"error": "Database connection not initialized."}), 500
    genre = request.args.get('genre')
    query_filter = {}
    if genre:
        try:
            regex_pattern = f'^{re.escape(genre)}$'
            regex = re.compile(regex_pattern, re.IGNORECASE)
            query_filter['genre'] = regex
            print(f"Fetching books for genre (case-insensitive): {genre}")
        except re.error as re_err:
             print(f"Error creating regex for genre '{genre}': {re_err}")
             query_filter['genre'] = genre
             print(f"Regex failed, falling back to exact match for genre: {genre}")
    else:
        print("Fetching all books")
    try:
        books_cursor = mongo_collection.find(
            query_filter, {'_id': 1, 'title': 1, 'author': 1, 'genre': 1}
        )
        books_list = []
        for book in books_cursor:
            book['_id'] = str(book['_id'])
            books_list.append(book)
        print(f"Found {len(books_list)} books.")
        return jsonify(books_list)
    except Exception as e:
        print(f"Error fetching books from MongoDB: {e}")
        return jsonify({"error": "An error occurred fetching books."}), 500

@app.route('/api/genres', methods=['GET'])
def get_genres():
    # ... (same as before) ...
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
    # ... (same as before) ...
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
            {'_id': obj_id}, {'_id': 1, 'title': 1, 'author': 1, 'genre': 1}
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

# --- Main Execution ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)