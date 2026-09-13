// Punto único del API_URL. En Vercel se setea VITE_API_URL; en local cae a localhost.
export const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
