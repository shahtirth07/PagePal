// src/App.tsx (Partial - Add/Uncomment these lines)
import React from "react";
import { Routes, Route } from "react-router-dom";
import GenrePage from "./pages/GenrePage.tsx";
import BookListPage from "./pages/BookListPage.tsx"; // <-- Import BookListPage
// ... other imports

function App() {
  return (
    <div className="app-container">
      <Routes>
        <Route path="/" element={<GenrePage />} />
        {/* Define the route for BookListPage, using :genreName as a URL parameter */}
        <Route path="/books/:genreName" element={<BookListPage />} />{" "}
        {/* <-- Add/Uncomment this route */}
        {/* <Route path="/chat/:bookId" element={<ChatPage />} /> */}
        {/* ... other routes */}
      </Routes>
    </div>
  );
}

export default App;
