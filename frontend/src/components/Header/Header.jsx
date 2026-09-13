import "./Header.css";

function Header({ username = "Usuario", vozActiva = false, onToggleVoz }) {
    return (
        <header className="home-header">

            <button
                type="button"
                className={`voz-toggle ${vozActiva ? "activa" : ""}`}
                onClick={onToggleVoz}
                aria-label={vozActiva ? "Desactivar voz" : "Activar voz"}
                aria-pressed={vozActiva}
                title={vozActiva ? "Desactivar voz" : "Activar voz"}
            >
                {vozActiva ? (
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 5 6 9H2v6h4l5 4V5z" />
                        <path d="M15.5 8.5a5 5 0 0 1 0 7" />
                        <path d="M18.5 5.5a9 9 0 0 1 0 13" />
                    </svg>
                ) : (
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 5 6 9H2v6h4l5 4V5z" />
                        <line x1="22" y1="9" x2="16" y2="15" />
                        <line x1="16" y1="9" x2="22" y2="15" />
                    </svg>
                )}
            </button>

            <p className="home-greeting">
                ¡Hola, {username}!
            </p>

            <h1>
                ¿En qué te puedo ayudar hoy?
            </h1>

        </header>
    );
}

export default Header;
