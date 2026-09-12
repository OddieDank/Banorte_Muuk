import "./Header.css";

function Header({ username = "Usuario" }) {
    return (
        <header className="home-header">

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