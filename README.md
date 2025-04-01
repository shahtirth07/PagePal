# PagePal (SF Hacks 2025)

An AI-powered chatbot designed to answer questions and discuss content based *specifically* on a provided knowledge base of books. Using Retrieval-Augmented Generation (RAG), the chatbot retrieves relevant passages from ingested texts to generate accurate, context-aware responses, allowing users to explore books conversationally. Built for SF Hacks 2025 (with pre-hackathon prep).

## ✨ Features (Planned)

* **AI Chat:** Conversational interaction for querying book content.
* **RAG Pipeline:** Retrieves relevant text chunks from a vector store before generating answers.
* **Source-Based Answers:** Aims to provide answers grounded in the ingested book text.
* **React Frontend:** User-friendly chat interface.

## 💻 Tech Stack

* **Frontend:** React (Vite), JavaScript
* **Backend:** Python, Flask
* **AI / RAG:** LangChain, OpenAI API (for Embeddings & LLM)
* **Vector Store:** ChromaDB (local)
* **Environment Management:** Python `venv`, `python-dotenv` (Backend), `npm` (Frontend)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

* [Node.js](https://nodejs.org/) (v18.x or later recommended for frontend)
* [npm](https://www.npmjs.com/) (v9.x or later recommended for frontend)
* [Python](https://www.python.org/) (v3.8 - 3.11 recommended)
* `pip` (Python package installer, usually comes with Python)
* [Git](https://git-scm.com/)
* **(Windows Users Only):** [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/). This is required to install `chromadb` correctly. Select the "Desktop development with C++" workload during installation and reboot after installing.

## 🚀 Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/shahtirth07/MentalHealthChatBot.git](https://www.google.com/search?q=https://github.com/shahtirth07/MentalHealthChatBot.git) 
    # Note: Consider renaming repo or updating URL if you created a new PagePal repo
    cd PagePal # Or your actual repo folder name
    ```

2.  **Setup Backend:**
    ```bash
    cd backend
    python -m venv venv # Create virtual environment
    # Activate virtual environment (choose command for your OS/shell)
    # Windows (cmd): .\venv\Scripts\activate.bat
    # Windows (PowerShell): .\venv\Scripts\Activate.ps1
    # Windows (Git Bash): source venv/Scripts/activate
    # macOS/Linux: source venv/bin/activate

    # Install required Python packages
    pip install -r requirements.txt
    ```

3.  **Setup Frontend:**
    ```bash
    cd ../frontend
    npm install
    ```

4.  **Set up Environment Variables (Backend):**
    * Navigate back to the backend directory: `cd ../backend`
    * Create a `.env` file by copying the example: `cp .env.example .env` (or manually create `.env` and copy content from `.env.example`).
    * Open the `.env` file and fill in your `OPENAI_API_KEY` (see below).

## 🔑 Environment Variables

Create a `.env` file in the `backend` directory (copy from `backend/.env.example`).

**Required variables for `backend/.env`:**

```dotenv
# backend/.env
# Get from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-YourSecretOpenAI_KeyHere

# Add other keys here if needed later (e.g., alternative LLM keys, DB configs)

Testing the Backend API (Optional)
You can test the chat API endpoint directly using tools like Postman or curl.

Using Postman (Recommended):

Set the request method to POST.
Set the URL to http://localhost:5000/api/chat.
Go to the "Headers" tab, add Content-Type with value application/json.
Go to the "Body" tab, select "raw", choose "JSON" from the dropdown.
Enter the request body: {"query": "Ask a question about your book here"}
Click "Send". Check the response body for the answer.