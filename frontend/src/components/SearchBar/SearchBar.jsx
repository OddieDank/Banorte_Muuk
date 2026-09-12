import { useState } from "react";
import "./SearchBar.css";

function SearchBar({ onSearch }) {
    const [query, setQuery] = useState("");

    const handleSearch = () => {
        if (!query.trim()) return;

        if (onSearch) {
            onSearch(query);
        }
    };

    const handleKeyDown = (event) => {
        if (event.key === "Enter") {
            handleSearch();
        }
    };

    return (
        <div className="search-bar">

            <button
                className="search-menu-button"
                type="button"
                aria-label="Abrir menú"
            >
                <span className="menu-line"></span>
                <span className="menu-line"></span>
                <span className="menu-line"></span>
            </button>

            <input
                type="text"
                className="search-input"
                placeholder="Haz una pregunta"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleKeyDown}
            />

            <button
                className="search-voice-button"
                type="button"
                aria-label="Usar micrófono"
            >
                <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                >
                    <rect
                        x="9"
                        y="3"
                        width="6"
                        height="11"
                        rx="3"
                    />
                    <path d="M5 11a7 7 0 0 0 14 0" />
                    <path d="M12 18v3" />
                    <path d="M8 21h8" />
                </svg>
            </button>

            <button
                className="search-submit-button"
                type="button"
                onClick={handleSearch}
                aria-label="Buscar"
            >
                <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                >
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20 20-4-4" />
                </svg>
            </button>

        </div>
    );
}

export default SearchBar;