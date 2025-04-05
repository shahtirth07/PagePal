// src/pages/BookListPage.tsx
import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom"; // Import hooks
import BookCard from "../components/BookCard"; // Import the BookCard component

// Define the structure for a book fetched from the API
interface Book {
  _id: string;
  title: string;
  author: string;
  genre?: string;
}

const BookListPage: React.FC = () => {
  // Get genreName from URL parameter (e.g., /books/Sci-Fi -> genreName = "Sci-Fi")
  const { genreName } = useParams<{ genreName: string }>();
  const navigate = useNavigate(); // Hook for programmatic navigation

  const [books, setBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch books for the specific genre when the component mounts or genreName changes
  useEffect(() => {
    const fetchBooks = async () => {
      setIsLoading(true);
      setError(null);
      // Decode genre name from URL in case it has spaces or special chars (%20 etc)
      const decodedGenreName = decodeURIComponent(genreName || "");
      try {
        const apiUrl = `http://localhost:5000/api/books?genre=${encodeURIComponent(
          decodedGenreName
        )}`;
        console.log(`Fetching books from: ${apiUrl}`);

        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: Book[] = await response.json();
        setBooks(data);
      } catch (err: any) {
        console.error("Failed to fetch books:", err);
        setError(err.message || "Failed to load books.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchBooks();
  }, [genreName]); // Re-run effect if genreName changes

  // Function to handle navigating to the chat page when a book card is clicked
  const handleBookSelect = (bookId: string) => {
    navigate(`/chat/${bookId}`); // Navigate to /chat/BOOK_ID
  };

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Back button */}
      <div className="mb-6">
        <Link to="/" className="text-blue-600 hover:underline">
          &larr; Back to Genres
        </Link>
      </div>

      {/* Page Title */}
      <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
        Books in {decodeURIComponent(genreName || "Selected Genre")}
      </h1>

      {/* Loading State */}
      {isLoading && (
        <p className="text-center text-gray-500">Loading books...</p>
      )}
      {/* Error State */}
      {error && <p className="text-center text-red-500">Error: {error}</p>}

      {/* No Books Found State */}
      {!isLoading && !error && books.length === 0 && (
        <p className="text-center text-gray-500">
          No books found for this genre.
        </p>
      )}

      {/* Book List Display (Grid for Tile Layout) */}
      {!isLoading && !error && books.length > 0 && (
        // Responsive grid: 1 col mobile, 2 cols small screens, 3 cols large screens
        <div className="flex-grow grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 overflow-y-auto p-1">
          {books.map((book) => (
            // Wrap BookCard in a div that handles the click for navigation
            <div
              key={book._id}
              onClick={() => handleBookSelect(book._id)}
              className="cursor-pointer"
            >
              <BookCard book={book} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BookListPage;
