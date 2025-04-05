# backend/app.py
import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from flask_cors import CORS

# --- LangChain Imports ---
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

load_dotenv()

# --- Configuration ---
# Ensure OPENAI_API_KEY is set in .env
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in .env file. API calls will fail.")

CHROMA_PERSIST_DIR = "chroma_db"
EMBEDDING_MODEL = "text-embedding-ada-002"
LLM_MODEL = "gpt-4o-mini" # Or "gpt-4" if you have access/budget

# --- Initialize Components (Load once when app starts) ---
try:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embeddings)
    retriever = vectorstore.as_retriever() # Default k=4 results
    llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0) # Low temp for factual answers

    # --- RAG Prompt Template ---
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    Answer:"""
    prompt = PromptTemplate.from_template(template)

    # --- RAG Chain using LCEL ---
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    print("RAG components initialized successfully.")

except Exception as e:
    print(f"Error initializing RAG components: {e}")
    rag_chain = None # Set chain to None if initialization fails


# --- Flask App ---
app = Flask(__name__)
CORS(app)

# Simple test route
@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello from the PagePal Python backend!"})

# --- Chat Endpoint ---
@app.route('/api/chat', methods=['POST'])
def chat():
    if not rag_chain:
         return jsonify({"error": "RAG chain not initialized. Check backend logs."}), 500

    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    try:
        print(f"Received query: {query}")
        # Invoke the RAG chain
        answer = rag_chain.invoke(query)
        print(f"Generated answer: {answer}")
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"Error processing chat request: {e}")
        # You might want more specific error handling here
        return jsonify({"error": "An error occurred processing your request."}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Set debug=False if you don't want auto-reload or detailed errors in production
    # For development, debug=True is useful
    app.run(debug=True, port=port)