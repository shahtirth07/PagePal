// src/pages/GenrePage.tsx
import React from "react";
import { Link } from "react-router-dom";
import {
  Brain,
  BookOpen,
  Rocket,
  User,
  HelpCircle,
  BookHeart,
  Atom,
} from "lucide-react";
// Import the CSS file
import "../styles/GenrePage.css"; // Adjust path if needed

// Define the structure for genre display properties - only need icon now
interface GenreDisplayProps {
  icon: React.ElementType;
}

// Helper function to get display properties (just icon) based on genre name
const getGenreDisplayProps = (
  genreName: string | null | undefined
): GenreDisplayProps => {
  const lowerGenre = genreName?.toLowerCase() || "unknown";
  const iconMappings: { [key: string]: React.ElementType } = {
    "self-help": Brain,
    devotional: BookHeart,
    "sci-fi": Atom,
    biography: User,
    t1: User,
    t2: User,
    unknown: HelpCircle,
  };
  const defaultIcon = HelpCircle;
  return { icon: iconMappings[lowerGenre] || defaultIcon };
};

// Helper function to generate the specific CSS modifier class for color
const getGenreColorClass = (genreName: string | null | undefined): string => {
  const lowerGenre = genreName?.toLowerCase() || "unknown";
  const classNameSuffix = lowerGenre
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `genre-tile--${classNameSuffix || "unknown"}`;
};

// Define the fixed list of genres to always display
const FIXED_GENRES = [
  "Self-Help",
  "Devotional",
  "Sci-Fi",
  "Biography",
  "t1",
  "t2",
  "Unknown",
];

const GenrePage: React.FC = () => {
  return (
    // Apply container class
    <div className="genre-page-container">
      {/* Apply title class */}
      <h1 className="genre-page-title">Browse Books by Genre</h1>

      {/* Apply grid class */}
      <div className="genre-grid">
        {FIXED_GENRES.map((genreName) => {
          const displayProps = getGenreDisplayProps(genreName);
          const IconComponent = displayProps.icon;
          const path = `/books/${encodeURIComponent(genreName)}`;
          const colorClass = getGenreColorClass(genreName);

          return (
            <Link
              key={genreName}
              to={path}
              // Apply base tile class and specific color class
              className={`genre-tile ${colorClass}`}
            >
              {/* Apply icon class - Reduced size */}
              <IconComponent
                size={48}
                strokeWidth={1.5}
                className="genre-tile-icon"
              />{" "}
              {/* Reduced size from 56 */}
              {/* Apply text class */}
              <span className="genre-tile-text">{genreName}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default GenrePage;
