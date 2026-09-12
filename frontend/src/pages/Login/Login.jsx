import { useState } from "react";
import "./Login.css";
import logo from "../../public/banorte-logo.svg";

function Login({ onLogin }) {

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [cargando, setCargando] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();

        if (!username.trim() || !password.trim()) {
            setError("Ingresa tu usuario y contraseña.");
            return;
        }

        setError("");
        setCargando(true);

        try {
            const respuesta = await fetch("http://localhost:8000/usuarios");
            if (!respuesta.ok) {
                setError("No se pudo conectar con el servidor.");
                return;
            }

            const usuarios = await respuesta.json();
            const buscado = username.trim().toLowerCase();

            // Coincide con el nombre completo o solo el primer nombre
            const encontrado = usuarios.find((u) => {
                const nombreCompleto = u.nombre.toLowerCase();
                const primerNombre = nombreCompleto.split(" ")[0];
                return nombreCompleto === buscado || primerNombre === buscado;
            });

            if (!encontrado) {
                setError("Usuario no encontrado. Prueba con Ana, Roberto o Marisol.");
                return;
            }

            localStorage.setItem("user_id", encontrado.user_id);
            localStorage.setItem("username", encontrado.nombre);

            if (onLogin) {
                onLogin(encontrado);
            }
        } catch (err) {
            setError("Error al conectar con el servidor.");
        } finally {
            setCargando(false);
        }
    };

    return (
        <div className="login-page">

            <div className="login-card">

                <div className="login-logo">
                    <img
                        src={logo}
                        alt="Banorte"
                        className="login-logo-img"
                    />
                </div>

                <div className="login-divider"></div>

                <h1>Bienvenido</h1>

                <p className="login-subtitle">
                    Ingresa para utilizar el asistente digital.
                </p>

                <form onSubmit={handleSubmit}>

                    <div className="login-field">
                        <label htmlFor="username">
                            Nombre
                        </label>

                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(event) =>
                                setUsername(event.target.value)
                            }
                            placeholder="Ingresa tu nombre"
                        />
                    </div>

                    <div className="login-field">
                        <label htmlFor="password">
                            Contraseña
                        </label>

                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(event.target.value)
                            }
                            placeholder="Ingresa tu contraseña"
                        />
                    </div>

                    {error && (
                        <p className="login-error">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        className="login-button"
                        disabled={cargando}
                    >
                        {cargando ? "Verificando..." : "Ingresar"}
                    </button>

                </form>

                <p className="login-footer">
                    Acceso seguro al asistente digital
                </p>

            </div>

        </div>
    );
}

export default Login;