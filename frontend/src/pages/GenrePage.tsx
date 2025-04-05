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
  DollarSign,   // Added DollarSign for Business/Finance
  Feather,      // Added Feather for Poetry
  Heart,        // Added Heart for Health/Fitness
  ForkKnife,    // Added ForkKnife for Cookbooks
  Activity,     // Added Activity for Health/Fitness
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
    "business-finance": DollarSign,  // Added DollarSign for Business/Finance
    "psychology": Brain,             // Existing Brain icon for Psychology
    "cookbooks": ForkKnife,          // Added ForkKnife for Cookbooks
    "health-fitness": Activity,     // Added Activity for Health/Fitness
    "poetry": Feather,              // Added Feather for Poetry
    "biography": User,
    "miscellaneous": HelpCircle,
    "romance": BookHeart,           // Added BookHeart for Romance
    "fantasy": Rocket,              // Added Rocket for Fantasy
    "mystery": BookOpen,            // Added BookOpen for Mystery
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
  "Romance",       // Added Romance
  "Fantasy",       // Added Fantasy
  "Mystery",       // Added Mystery
  "Cookbooks",     // Added Cookbooks
  "Health-Fitness",// Added Health-Fitness
  "Poetry",        // Added Poetry
  "Miscellaneous",
];

const GenrePage: React.FC = () => {
  return (
    <div className="genre-page-container">
      <h1 className="genre-page-title">Browse Books by Genre</h1>

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
              className={`genre-tile ${colorClass}`}
            >
              <IconComponent
                size={48}
                strokeWidth={1.5}
                className="genre-tile-icon"
              />
              <span className="genre-tile-text">{genreName}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default GenrePage;
