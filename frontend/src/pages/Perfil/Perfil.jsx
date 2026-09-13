import { useEffect, useState } from "react";
import muukCoin from "../../public/muuk_coin.png";
import "./Perfil.css";

const API = "http://localhost:8000";

function Perfil({ onBack }) {
    const [datos, setDatos] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState("");
    const [muukCoins, setMuukCoins] = useState(null);
    const [muukHistory, setMuukHistory] = useState([]);

    useEffect(() => {
        const userId = localStorage.getItem("user_id");

        if (!userId) {
            setError("No se encontró el usuario.");
            setCargando(false);
            return;
        }

        Promise.all([
            fetch(`${API}/perfil?user_id=${userId}`),
            fetch(`${API}/muuk-coins/history?user_id=${userId}`)
        ])
            .then(async ([perfilResponse, coinsResponse]) => {
                if (!perfilResponse.ok) {
                    throw new Error("No se pudo cargar el perfil.");
                }

                if (!coinsResponse.ok) {
                    throw new Error("No se pudo cargar el historial de Muuk Coins.");
                }

                const perfilData = await perfilResponse.json();
                const coinsData = await coinsResponse.json();

                return {
                    perfilData,
                    coinsData
                };
            })
            .then(({ perfilData, coinsData }) => {
                setDatos(perfilData);
                setMuukCoins(coinsData.balance);
                setMuukHistory(coinsData.history);
            })
            .catch((err) => setError(err.message))
            .finally(() => setCargando(false));
    }, []);

    if (cargando) {
        return (
            <div className="perfil-page">
                <p>Cargando perfil...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="perfil-page">
                <button className="perfil-back" onClick={onBack}>← Volver</button>
                <p className="perfil-error">{error}</p>
            </div>
        );
    }

    const { usuario, perfil_financiero, productos } = datos;

    return (
        <div className="perfil-page">

            <button className="perfil-back" onClick={onBack}>← Volver</button>

            <h1 className="perfil-titulo">Mi perfil</h1>

            <section className="perfil-card">
                <div className="perfil-card-accent"></div>
                <div className="perfil-card-content">
                    <h2>Datos básicos</h2>
                    <div className="perfil-fila">
                        <span className="perfil-label">Nombre</span>
                        <span className="perfil-valor">{usuario.nombre}</span>
                    </div>
                    <div className="perfil-fila">
                        <span className="perfil-label">Edad</span>
                        <span className="perfil-valor">{usuario.edad}</span>
                    </div>
                    <div className="perfil-fila">
                        <span className="perfil-label">Ocupación</span>
                        <span className="perfil-valor">{usuario.ocupacion}</span>
                    </div>
                </div>
            </section>

            {perfil_financiero && (
                <section className="perfil-card">
                    <div className="perfil-card-accent"></div>
                    <div className="perfil-card-content">
                        <h2>Perfil financiero</h2>
                        <div className="perfil-fila">
                            <span className="perfil-label">Ingreso</span>
                            <span className="perfil-valor">{perfil_financiero.ingreso_rango}</span>
                        </div>
                        <div className="perfil-fila">
                            <span className="perfil-label">Nivel de ahorro</span>
                            <span className="perfil-valor">{perfil_financiero.ahorro_nivel}</span>
                        </div>
                        <div className="perfil-fila">
                            <span className="perfil-label">Nivel de deuda</span>
                            <span className="perfil-valor">{perfil_financiero.deuda_nivel}</span>
                        </div>
                        <div className="perfil-fila">
                            <span className="perfil-label">Meta financiera</span>
                            <span className="perfil-valor">{perfil_financiero.meta_financiera}</span>
                        </div>
                    </div>
                </section>
            )}

            <section className="perfil-card perfil-coins-card">
                <div className="perfil-card-accent"></div>

                <div className="perfil-card-content">

                    <div className="perfil-coins-header">
                        <div>
                            <h2>Muuk Coins</h2>
                            <p className="perfil-coins-subtitulo">
                                Recompensas por tus buenos hábitos financieros
                            </p>
                        </div>

                        <div className="perfil-coins-balance">
                            <img
                                src={muukCoin}
                                alt="Muuk Coin"
                                className="perfil-coins-icon"
                            />
                            <span>{muukCoins ?? 0}</span>
                        </div>
                    </div>

                    <div className="perfil-coins-divider"></div>

                    <h3 className="perfil-coins-historial-titulo">
                        Historial de movimientos
                    </h3>

                    {muukHistory.length === 0 ? (
                        <p className="perfil-vacio">
                            Todavía no tienes movimientos de Muuk Coins.
                        </p>
                    ) : (
                        <ul className="perfil-coins-lista">
                            {muukHistory.map((movimiento) => (
                                <li
                                    key={movimiento.muuk_coin_transaction_id}
                                    className="perfil-coins-movimiento"
                                >
                                    <div className="perfil-coins-movimiento-info">
                                        <span className="perfil-coins-descripcion">
                                            {movimiento.descripcion}
                                        </span>

                                        <span className="perfil-coins-tipo">
                                            {movimiento.tipo}
                                        </span>
                                    </div>

                                    <div className="perfil-coins-cantidad">
                                        {movimiento.cantidad > 0 ? "+" : ""}
                                        {movimiento.cantidad}

                                        <img
                                            src={muukCoin}
                                            alt="Muuk Coin"
                                            className="perfil-coins-icon-small"
                                        />
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}

                </div>
            </section>

            <section className="perfil-card">
                <div className="perfil-card-accent"></div>
                <div className="perfil-card-content">
                    <h2>Productos contratados</h2>
                    {productos.length === 0 ? (
                        <p className="perfil-vacio">No tienes productos contratados.</p>
                    ) : (
                        <ul className="perfil-lista">
                            {productos.map((p) => (
                                <li key={p.user_product_id}>
                                    <span className="perfil-producto-nombre">{p.nombre}</span>
                                    <span className="perfil-producto-estado">{p.estado}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </section>

        </div>
    );
}

export default Perfil;