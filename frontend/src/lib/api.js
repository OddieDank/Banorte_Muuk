// Punto único del API_URL. Default: producción (Render). Para desarrollo
// local, frontend/.env (gitignored) define VITE_API_URL=http://localhost:8000.
export const API = import.meta.env.VITE_API_URL || "https://banorte-muuk.onrender.com";
