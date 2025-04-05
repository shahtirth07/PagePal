import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom"; // Import hooks
import BookCard from "../components/BookCard"; // Import the BookCard component
import "../styles/BookListPage.css"; // Adjust path if needed

interface Book {
  _id: string;
  title: string;
  author: string;
  genre?: string;
}

const BookListPage: React.FC = () => {
  const { genreName } = useParams<{ genreName: string }>();
  const navigate = useNavigate();

  const [books, setBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBooks = async () => {
      setIsLoading(true);
      setError(null);
      const decodedGenreName = decodeURIComponent(genreName || "");
      try {
        const apiUrl = `http://localhost:5000/api/books?genre=${encodeURIComponent(
          decodedGenreName
        )}`;
        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: Book[] = await response.json();
        setBooks(data);
      } catch (err: any) {
        setError(err.message || "Failed to load books.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchBooks();
  }, [genreName]);

  const handleBookSelect = (bookId: string) => {
    navigate(`/chat/${bookId}`);
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="mb-6">
        <Link to="/" className="text-blue-600 hover:underline">
          &larr; Back to Genres
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
        Books in {decodeURIComponent(genreName || "Selected Genre")}
      </h1>

      {isLoading && (
        <p className="text-center text-gray-500">Loading books...</p>
      )}
      {error && <p className="text-center text-red-500">Error: {error}</p>}

      {!isLoading && !error && books.length === 0 && (
        <p className="text-center text-gray-500">
          No books found for this genre.
        </p>
      )}

      {!isLoading && !error && books.length > 0 && (
        <div className="flex-grow grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 overflow-y-auto p-1">
          {books.map((book) => (
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
