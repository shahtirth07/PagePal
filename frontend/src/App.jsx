// src/App.jsx
import React from "react";
import { Routes, Route } from "react-router-dom";
import GenrePage from "./pages/GenrePage.tsx";
import BookListPage from "./pages/BookListPage.tsx";
// import ChatPage from "./pages/ChatPage.tsx"; // if needed

import "./App.css"; // 👈 Import your styles here

function App() {
  return (
    <div className="app-container">
      <Routes>
        <Route path="/" element={<GenrePage />} />
        <Route path="/books/:genreName" element={<BookListPage />} />
        {/* <Route path="/chat/:bookId" element={<ChatPage />} /> */}
      </Routes>
    </div>
  );
}

export default App;
