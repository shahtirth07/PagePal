import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface Message {
  sender: 'user' | 'ai';
  text: string;
}

interface BookDetails {
  _id: string;
  title: string;
  author: string;
  genre?: string;
}

const ChatPage: React.FC = () => {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();

  const [bookDetails, setBookDetails] = useState<BookDetails | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingBook, setIsLoadingBook] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    const fetchBookDetails = async () => {
      if (!bookId) {
        setError("No book ID provided.");
        setIsLoadingBook(false);
        return;
      }
      setIsLoadingBook(true);
      setError(null);
      setMessages([]);
      try {
        const apiUrl = `http://localhost:5000/api/books/${bookId}`;
        const response = await fetch(apiUrl);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Book with ID ${bookId} not found.`);
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: BookDetails = await response.json();
        setBookDetails(data);
        setMessages([{ sender: 'ai', text: `You are now chatting about "${data.title}". Ask me anything!` }]);
      } catch (err: any) {
        setError(err.message || "Failed to load book details.");
        setBookDetails(null);
      } finally {
        setIsLoadingBook(false);
      }
    };

    fetchBookDetails();
  }, [bookId]);

  const handleSend = async () => {
    const userMessageText = input.trim();
    if (!userMessageText || isLoading || !bookDetails) return;

    const newUserMessage: Message = { sender: 'user', text: userMessageText };
    setMessages(prev => [...prev, newUserMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMessageText,
          book_filter: { title: bookDetails.title }
        }),
      });

      if (!response.ok) {
        let errorMsg = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorMsg;
        } catch (e) {
          console.error("Could not parse error response:", e);
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      const aiMessage: Message = { sender: 'ai', text: data.answer };
      setMessages(prev => [...prev, aiMessage]);

    } catch (err: any) {
      const errorMessage: Message = { sender: 'ai', text: `Sorry, an error occurred: ${err.message}` };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(event.target.value);
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: '#f4f7f6' }}>
      <div style={{ marginBottom: '24px', flexShrink: 0 }}>
        <button onClick={() => navigate(-1)} style={{ color: '#3498db', textDecoration: 'underline', fontSize: '18px' }}>
          &larr; Back to Books
        </button>
      </div>

      <h1 style={{ textAlign: 'center', fontSize: '24px', fontWeight: 'bold', color: '#333', marginBottom: '24px', flexShrink: 0 }}>
        {isLoadingBook ? "Loading Book..." : bookDetails ? `Chat with: ${bookDetails.title}` : "Book Not Found"}
        {bookDetails?.author && <span style={{ display: 'block', fontSize: '16px', fontWeight: 'normal', color: '#777' }}> by {bookDetails.author}</span>}
      </h1>

      {error && !isLoadingBook && <p style={{ color: '#e74c3c', textAlign: 'center', marginBottom: '12px' }}>Error loading book: {error}</p>}

      <div style={{ display: 'flex', flexDirection: 'row', backgroundColor: 'white', padding: '16px', borderRadius: '8px', marginBottom: '24px', boxShadow: '0 6px 12px rgba(0, 0, 0, 0.1)' }}>
        {/* Book Cover Placeholder */}
        <div style={{ width: '120px', height: '180px', backgroundColor: '#e0e0e0', borderRadius: '8px', marginRight: '20px', display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '18px', color: '#888' }}>
          <span>Upload Cover</span>
        </div>

        {/* Book Details */}
        <div style={{ flexGrow: 1 }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#2c3e50', marginBottom: '8px' }}>{bookDetails?.title}</h2>
          <p style={{ fontSize: '16px', color: '#555', margin: '4px 0' }}>by {bookDetails?.author}</p>
          {bookDetails?.genre && <p style={{ fontSize: '16px', color: '#3498db', fontStyle: 'italic' }}>Genre: {bookDetails.genre}</p>}
        </div>
      </div>

      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid #ddd', borderRadius: '12px', backgroundColor: 'white' }}>
        <div style={{ padding: '16px', overflowY: 'auto', flexGrow: 1, backgroundColor: '#f9f9f9' }}>
          {messages.map((msg, index) => (
            <div key={index} style={{
              maxWidth: '85%', padding: '10px', borderRadius: '8px', marginBottom: '12px',
              backgroundColor: msg.sender === 'user' ? '#d0e9ff' : '#f1f1f1', marginLeft: msg.sender === 'user' ? 'auto' : '0'
            }}>
              <p style={{ fontSize: '14px', lineHeight: '1.4', margin: '0' }}>{msg.text}</p>
            </div>
          ))}
          {isLoading && (
            <div style={{ maxWidth: '85%', padding: '10px', borderRadius: '8px', marginBottom: '12px', backgroundColor: '#f1f1f1', marginRight: 'auto' }}>
              <p style={{ fontSize: '14px', fontStyle: 'italic' }}>PagePal is thinking...</p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ display: 'flex', padding: '16px', borderTop: '1px solid #ddd', backgroundColor: 'white' }}>
          <textarea
            value={input}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={bookDetails ? `Ask about ${bookDetails.title}...` : "Loading book..."}
            rows={2}
            style={{ flexGrow: 1, padding: '10px', border: '1px solid #ddd', borderRadius: '8px', resize: 'none', fontSize: '14px', outline: 'none' }}
            disabled={isLoading || isLoadingBook || !bookDetails}
          />
          <button
            onClick={handleSend}
            style={{
              padding: '12px 20px', marginLeft: '12px', backgroundColor: '#3498db', color: 'white', border: 'none', borderRadius: '8px',
              cursor: 'pointer', transition: 'background-color 0.3s ease', disabled: isLoading || isLoadingBook || !bookDetails || !input.trim() ? '#ddd' : '#2980b9'
            }}
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