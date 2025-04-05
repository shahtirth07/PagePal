// src/App.jsx
import React from "react";
import { Routes, Route } from "react-router-dom";
import GenrePage from "./pages/GenrePage.tsx"; // Importing TSX file
import BookListPage from "./pages/BookListPage.tsx"; // Importing TSX file
import ChatPage from "./pages/ChatPage.tsx"; // <-- Uncommented ChatPage import

import "./App.css"; // 👈 Import your styles here

function App() {
  return (
    // Main container div
    <div className="app-container">
      {/* Router component to define application paths */}
      <Routes>
        {/* Default route: Shows the GenrePage */}
        <Route path="/" element={<GenrePage />} />
        {/* Route for BookListPage: Uses genreName parameter from URL */}
        <Route path="/books/:genreName" element={<BookListPage />} />
        {/* Route for ChatPage: Now uncommented */}
        <Route path="/chat/:bookId" element={<ChatPage />} />{" "}
        {/* <-- Uncommented this route */}
      </Routes>
    </div>
  );
}

// Export the App component as the default export
export default App;
