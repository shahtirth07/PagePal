import React from "react";

// Define the expected props for the BookCard
interface Book {
  _id: string;
  title: string;
  author: string;
  genre?: string; // Optional genre display
  coverUrl?: string; // Optional cover image URL
}

// Define the props for the BookCard component
interface BookCardProps {
  book: Book; // Book prop passed from the parent
}

const BookCard: React.FC<BookCardProps> = ({ book }) => {
  return (
    <div className="book-card">
      {/* Book Cover Image */}
      <img
        src={book.coverUrl || "placeholder.jpg"} // Use placeholder if no cover URL is provided
        alt="Book Cover"
        className="book-cover"
      />

      {/* Book Information Box */}
      <div className="book-info-box">
        <h3 className="text-lg font-semibold text-gray-800 mb-1 truncate" title={book.title}>
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
      </div>
    </div>
  );
};

export default BookCard;
