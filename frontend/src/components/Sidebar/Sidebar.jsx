import "./Sidebar.css";

function Sidebar({ onLogout }) {
    return (
        <aside className="sidebar">

            <div className="sidebar-brand">
                <div className="sidebar-brand-mark">
                    M
                </div>

                <span>MUUK</span>
            </div>

            <div className="sidebar-profile">

                <div className="sidebar-profile-icon">
                    <svg
                        width="26"
                        height="26"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                    >
                        <circle cx="12" cy="8" r="4" />
                        <path d="M4 21a8 8 0 0 1 16 0" />
                    </svg>
                </div>

                <span>Mi perfil</span>

            </div>

            <button
                className="sidebar-logout"
                type="button"
                onClick={onLogout}
            >
                Cerrar sesión
            </button>

            <div className="sidebar-footer">
                Banca Digital
            </div>

        </aside>
    );
}

export default Sidebar;