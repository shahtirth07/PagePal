// src/pages/ChatPage.tsx
import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";

const ChatPage: React.FC = () => {
  const { bookId } = useParams();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/chat/${bookId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (!res.ok) {
        throw new Error("Failed to get a response from the book.");
      }

      const data = await res.json();
      const botMsg = { role: "book", text: data.response };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div className="flex flex-col min-h-screen p-6 bg-gray-50 text-gray-900">
      <div className="mb-4">
        <Link to="/" className="text-blue-600 hover:underline">
          &larr; Back to Genres
        </Link>
      </div>

      <h1 className="text-2xl font-bold mb-6">Talk to this Book</h1>

      <div className="flex-grow overflow-y-auto mb-4 space-y-4 bg-white p-4 rounded-lg shadow-md">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`max-w-xl ${
              msg.role === "user" ? "ml-auto text-right" : "mr-auto text-left"
            }`}
          >
            <div
              className={`inline-block px-4 py-2 rounded-xl ${
                msg.role === "user"
                  ? "bg-purple-600 text-white"
                  : "bg-gray-200 text-gray-900"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {loading && (
          <p className="text-gray-500 italic text-sm">The book is typing...</p>
        )}
        {error && <p className="text-red-500">Error: {error}</p>}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Ask the book something..."
          className="flex-1 p-3 border rounded-lg shadow-sm"
        />
        <button
          onClick={sendMessage}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          disabled={loading}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatPage;
