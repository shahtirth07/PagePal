// src/pages/ChatPage.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// Define message structure
interface Message {
  sender: 'user' | 'ai';
  text: string;
}

// Define book details structure
interface BookDetails {
  _id: string;
  title: string;
  author: string;
  genre?: string;
}

const ChatPage: React.FC = () => {
  const { bookId } = useParams<{ bookId: string }>(); // Get bookId from URL
  const navigate = useNavigate(); // Hook for navigation

  const [bookDetails, setBookDetails] = useState<BookDetails | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false); // Loading state for AI response
  const [isLoadingBook, setIsLoadingBook] = useState(true); // Loading state for book details
  const [error, setError] = useState<string | null>(null); // Error state for book loading/chat

  const messagesEndRef = useRef<HTMLDivElement>(null); // Ref for scrolling

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  // Fetch book details when component mounts or bookId changes
  useEffect(() => {
    const fetchBookDetails = async () => {
      if (!bookId) {
        setError("No book ID provided.");
        setIsLoadingBook(false);
        return;
      }
      setIsLoadingBook(true);
      setError(null);
      setMessages([]); // Clear previous messages when loading new book
      try {
        const apiUrl = `http://localhost:5000/api/books/${bookId}`;
        console.log(`Fetching book details from: ${apiUrl}`);
        const response = await fetch(apiUrl);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Book with ID ${bookId} not found.`);
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: BookDetails = await response.json();
        setBookDetails(data);
        // Add an initial greeting from PagePal
        setMessages([{ sender: 'ai', text: `You are now chatting about "${data.title}". Ask me anything!` }]);
      } catch (err: any) {
        console.error("Failed to fetch book details:", err);
        setError(err.message || "Failed to load book details.");
        setBookDetails(null); // Clear details on error
      } finally {
        setIsLoadingBook(false);
      }
    };

    fetchBookDetails();
  }, [bookId]); // Re-run effect if bookId changes


  // Handle sending chat messages
  const handleSend = async () => {
    const userMessageText = input.trim();
    // Don't send if loading, no book details, or empty input
    if (!userMessageText || isLoading || !bookDetails) return;

    const newUserMessage: Message = { sender: 'user', text: userMessageText };
    setMessages(prev => [...prev, newUserMessage]);
    setInput('');
    setIsLoading(true);
    // setError(null); // Optionally clear previous chat errors

    try {
      console.log(`Sending query about "${bookDetails.title}":`, userMessageText);
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Send query AND the book title as a filter
        body: JSON.stringify({
          query: userMessageText,
          book_filter: { title: bookDetails.title } // Use title for filtering
        }),
      });

      if (!response.ok) {
        let errorMsg = `HTTP error! status: ${response.status}`;
         try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; }
         catch (e) { console.error("Could not parse error response:", e); }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      console.log("Received answer:", data.answer);
      const aiMessage: Message = { sender: 'ai', text: data.answer };
      setMessages(prev => [...prev, aiMessage]);

    } catch (err: any) {
      console.error("Failed to send/receive chat message:", err);
      const errorMessage: Message = { sender: 'ai', text: `Sorry, an error occurred: ${err.message}` };
      setMessages(prev => [...prev, errorMessage]);
      // setError(err.message); // Set error state if needed
    } finally {
      setIsLoading(false);
    }
  };

  // Input change handler
  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(event.target.value);
  };

  // Send on Enter key press
  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  // Render component
  return (
    <div className="p-6 h-full flex flex-col">
       {/* Back Button */}
       <div className="mb-4 flex-shrink-0"> {/* Ensure button doesn't shrink */}
         <button onClick={() => navigate(-1)} className="text-blue-600 hover:underline">
           &larr; Back to Books
         </button>
       </div>

       {/* Header showing book title or loading/error state */}
       <h1 className="text-2xl font-bold text-center mb-4 text-gray-800 flex-shrink-0">
         {isLoadingBook ? "Loading Book..." : bookDetails ? `Chat with: ${bookDetails.title}` : "Book Not Found"}
         {bookDetails?.author && <span className="block text-lg font-normal text-gray-600">by {bookDetails.author}</span>}
       </h1>

       {/* Display error if book loading failed */}
       {error && !isLoadingBook && <p className="text-center text-red-500 mb-4 flex-shrink-0">Error loading book: {error}</p>}

       {/* Chat Interface - Allow chat container to grow and scroll */}
       <div className="chat-container flex-grow flex flex-col overflow-hidden border border-gray-300 rounded-md mt-2">
         <div className="messages flex-grow overflow-y-auto p-4 bg-gray-50">
           {messages.map((msg, index) => (
             <div key={index} className={`message ${msg.sender} mb-3 max-w-[85%] p-3 rounded-lg ${msg.sender === 'user' ? 'bg-blue-100 ml-auto' : 'bg-gray-200 mr-auto'}`}>
               <p className="text-sm whitespace-pre-wrap">{msg.text}</p> {/* Added whitespace-pre-wrap */}
             </div>
           ))}
           {isLoading && (
             <div className="message ai mb-3 max-w-[85%] p-3 rounded-lg bg-gray-200 mr-auto">
               <p className="text-sm italic">PagePal is thinking...</p>
             </div>
           )}
           <div ref={messagesEndRef} />
         </div>
         <div className="input-area flex p-2 border-t border-gray-300 bg-white flex-shrink-0">
           <textarea
             value={input}
             onChange={handleInputChange}
             onKeyPress={handleKeyPress}
             placeholder={bookDetails ? `Ask about ${bookDetails.title}...` : "Loading book..."}
             rows={2}
             className="flex-grow p-2 border border-gray-300 rounded-md resize-none mr-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
             disabled={isLoading || isLoadingBook || !bookDetails}
           />
           <button
             onClick={handleSend}
             className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
             disabled={isLoading || isLoadingBook || !bookDetails || !input.trim()}
           >
             Send
           </button>
         </div>
       </div>
    </div>
  );
};

export default ChatPage;
