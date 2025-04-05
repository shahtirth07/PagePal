// src/index.tsx OR src/main.tsx

import React from "react";
import ReactDOM from "react-dom/client";
// Make sure BrowserRouter is imported
import { BrowserRouter } from "react-router-dom";
import App from "./App"; // Import your main App component
import "./styles/index.css"; // Import global styles

// Get the root element from the HTML
const rootElement = document.getElementById("root");

// Ensure the root element exists before rendering
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      {/* 👇 This BrowserRouter wrapper is essential for Routes to work 👇 */}
      <BrowserRouter>
        <App />
      </BrowserRouter>
      {/* 👆 End of BrowserRouter wrapper 👆 */}
    </React.StrictMode>
  );
} else {
  console.error("Failed to find the root element with ID 'root'");
}
