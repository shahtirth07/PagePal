// src/components/BookCard.tsx
import React from "react";

// Define the expected props for the BookCard
interface Book {
  _id: string;
  title: string;
  author: string;
  genre?: string; // Optional genre display
}

interface BookCardProps {
  book: Book;
  // Add onClick or use Link wrapper in parent component
}

const BookCard: React.FC<BookCardProps> = ({ book }) => {
  return (
    <div className="p-4 border border-gray-200 rounded-lg shadow hover:shadow-md transition-shadow bg-white">
      <h3
        className="text-lg font-semibold text-gray-800 mb-1 truncate"
        title={book.title}
      >
        {book.title || "Untitled Book"}
      </h3>
      <p className="text-sm text-gray-600 mb-2 truncate" title={book.author}>
        by {book.author || "Unknown Author"}
      </p>
      {book.genre && (
        <span className="inline-block bg-gray-200 rounded-full px-3 py-1 text-xs font-semibold text-gray-700">
          {book.genre}
        </span>
      )}
      {/* Add a button or wrap with Link in BookListPage for navigation */}
    </div>
  );
};

export default BookCard;
