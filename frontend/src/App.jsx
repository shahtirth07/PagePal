// src/App.jsx
import React, { useState, useEffect, useRef } from "react";
import "./App.css"; // We'll add some styles here

function App() {
  // State to hold the chat messages
  // Each message is an object: { sender: 'user' | 'ai', text: string }
  const [messages, setMessages] = useState([]);
  // State for the user's current input
  const [input, setInput] = useState("");
  // State to track if the AI is responding
  const [isLoading, setIsLoading] = useState(false);

  // Ref for the messages container to auto-scroll
  const messagesEndRef = useRef(null);

  // Function to scroll to the bottom of the messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Scroll to bottom whenever messages update
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Function to handle sending a message
  const handleSend = async () => {
    const userMessageText = input.trim();
    // Don't send empty messages or if already loading
    if (!userMessageText || isLoading) return;

    // Add user message to the chat display
    const newUserMessage = { sender: "user", text: userMessageText };
    setMessages((prev) => [...prev, newUserMessage]);

    setInput(""); // Clear the input field
    setIsLoading(true); // Set loading state

    try {
      // --- API Call to Backend ---
      console.log("Sending query to backend:", userMessageText); // Log outgoing query
      const response = await fetch("http://localhost:5000/api/chat", {
        // Ensure backend port (5000) is correct
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: userMessageText }), // Send query in correct format
      });

      // Check if the response is okay (status code 200-299)
      if (!response.ok) {
        // Try to parse error message from backend, otherwise use status text
        let errorMsg = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorMsg;
        } catch (parseError) {
          // Ignore if response body isn't valid JSON
          console.error("Could not parse error response:", parseError);
        }
        throw new Error(errorMsg);
      }

      // Parse the JSON response from the backend
      const data = await response.json();
      console.log("Received answer from backend:", data.answer); // Log incoming answer

      // Add AI message to the chat display
      const aiMessage = { sender: "ai", text: data.answer };
      setMessages((prev) => [...prev, aiMessage]);
      // --- End API Call ---
    } catch (error) {
      // Log the error and display an error message in the chat
      console.error("Failed to send message or get response:", error);
      const errorMessage = {
        sender: "ai",
        text: `Sorry, an error occurred: ${error.message}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      // Reset loading state regardless of success or failure
      setIsLoading(false);
    }
  };

  // Update input state when user types
  const handleInputChange = (event) => {
    setInput(event.target.value);
  };

  // Send message when Enter key is pressed (unless Shift is held)
  const handleKeyPress = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault(); // Prevent adding a newline
      handleSend();
    }
  };

  // Render the component
  return (
    <div className="app-container">
      <h1>PagePal</h1>
      <div className="chat-container">
        <div className="messages">
          {/* Map through messages and display them */}
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              {/* Simple paragraph display */}
              <p>
                <strong>{msg.sender === "user" ? "You" : "PagePal"}:</strong>{" "}
                {msg.text}
              </p>
            </div>
          ))}
          {/* Show loading indicator */}
          {isLoading && (
            <div className="message ai">
              <p>
                <i>PagePal is thinking...</i>
              </p>
            </div>
          )}
          {/* Empty div to scroll to */}
          <div ref={messagesEndRef} />
        </div>
        <div className="input-area">
          <textarea
            value={input}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Ask PagePal about the book..."
            rows="3"
            disabled={isLoading} // Disable input while loading
          />
          <button onClick={handleSend} disabled={isLoading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
